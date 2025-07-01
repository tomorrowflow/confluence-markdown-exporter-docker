"""Confluence API documentation.

https://developer.atlassian.com/cloud/confluence/rest/v1/intro
"""

import functools
import mimetypes
import os
import re
import urllib.parse
from collections.abc import Set
from os import PathLike
from pathlib import Path
from string import Template
from typing import Literal
from typing import TypeAlias
from typing import cast

import jmespath
import yaml
from atlassian.errors import ApiError
from bs4 import BeautifulSoup
from bs4 import Tag
from markdownify import ATX
from markdownify import MarkdownConverter
from pydantic import BaseModel
from requests import HTTPError
from tqdm import tqdm

from confluence_markdown_exporter.api_clients import get_api_instances
from confluence_markdown_exporter.utils.app_data_store import get_settings
from confluence_markdown_exporter.utils.export import sanitize_filename
from confluence_markdown_exporter.utils.export import sanitize_key
from confluence_markdown_exporter.utils.export import save_file
from confluence_markdown_exporter.utils.table_converter import TableConverter

JsonResponse: TypeAlias = dict
StrPath: TypeAlias = str | PathLike[str]

DEBUG: bool = bool(os.getenv("DEBUG"))

settings = get_settings()
confluence, jira = get_api_instances()


class JiraIssue(BaseModel):
    key: str
    summary: str
    description: str | None
    status: str

    @classmethod
    def from_json(cls, data: JsonResponse) -> "JiraIssue":
        fields = data.get("fields", {})
        return cls(
            key=data.get("key", ""),
            summary=fields.get("summary", ""),
            description=fields.get("description", ""),
            status=fields.get("status", {}).get("name", ""),
        )

    @classmethod
    @functools.lru_cache(maxsize=100)
    def from_key(cls, issue_key: str) -> "JiraIssue":
        issue_data = cast("JsonResponse", jira.get_issue(issue_key))
        return cls.from_json(issue_data)


class User(BaseModel):
    account_id: str
    username: str
    display_name: str
    public_name: str
    email: str

    @classmethod
    def from_json(cls, data: JsonResponse) -> "User":
        return cls(
            account_id=data.get("accountId", ""),
            username=data.get("username", ""),
            display_name=data.get("displayName", ""),
            public_name=data.get("publicName", ""),
            email=data.get("email", ""),
        )

    @classmethod
    @functools.lru_cache(maxsize=100)
    def from_username(cls, username: str) -> "User":
        return cls.from_json(
            cast("JsonResponse", confluence.get_user_details_by_username(username))
        )

    @classmethod
    @functools.lru_cache(maxsize=100)
    def from_userkey(cls, userkey: str) -> "User":
        return cls.from_json(cast("JsonResponse", confluence.get_user_details_by_userkey(userkey)))

    @classmethod
    @functools.lru_cache(maxsize=100)
    def from_accountid(cls, accountid: str) -> "User":
        return cls.from_json(
            cast("JsonResponse", confluence.get_user_details_by_accountid(accountid))
        )


class Version(BaseModel):
    number: int
    by: User
    when: str
    friendly_when: str

    @classmethod
    def from_json(cls, data: JsonResponse) -> "Version":
        return cls(
            number=data.get("number", 0),
            by=User.from_json(data.get("by", {})),
            when=data.get("when", ""),
            friendly_when=data.get("friendlyWhen", ""),
        )


class Organization(BaseModel):
    spaces: list["Space"]

    @property
    def pages(self) -> list[int]:
        return [page for space in self.spaces for page in space.pages]

    def export(self) -> None:
        export_pages(self.pages)

    @classmethod
    def from_json(cls, data: JsonResponse) -> "Organization":
        return cls(
            spaces=[Space.from_json(space) for space in data.get("results", [])],
        )

    @classmethod
    @functools.lru_cache(maxsize=100)
    def from_api(cls) -> "Organization":
        return cls.from_json(
            cast(
                "JsonResponse",
                confluence.get_all_spaces(
                    space_type="global", space_status="current", expand="homepage"
                ),
            )
        )


class SearchResults(BaseModel):
    query: str
    page_ids: list[int]
    total_size: int
    total_pages: int  # Pages only (filtered)

    def export(self) -> None:
        export_pages(self.page_ids)

    @classmethod
    def from_cql(cls, cql_query: str, limit: int = 100) -> "SearchResults":
        """Execute CQL query and return page IDs for export.

        Automatically filters results to pages only and handles pagination.
        """
        page_ids = []
        start = 0
        paging_limit = 25  # Conservative limit to avoid API restrictions
        total_size = 0
        total_pages = 0

        # Ensure we only get pages by adding type filter if not present
        if "type" not in cql_query.lower():
            if cql_query.strip():
                cql_query = f"({cql_query}) AND type = page"
            else:
                cql_query = "type = page"
        elif "type = page" not in cql_query.lower() and "type=page" not in cql_query.lower():
            # If type is specified but not page, add page filter
            if "type" in cql_query.lower():
                print(
                    "WARNING: CQL query specifies content type other than 'page'. Adding 'AND type = page' to filter pages only."
                )
                cql_query = f"({cql_query}) AND type = page"

        print(f"Executing full CQL query: {cql_query}")

        try:
            while start < limit:
                current_limit = min(paging_limit, limit - start)

                response = cast(
                    "JsonResponse",
                    confluence.cql(
                        cql_query,
                        start=start,
                        limit=current_limit,
                        expand="space",  # Minimal expansion to avoid 50-result limit
                    ),
                )

                # Extract page IDs from results
                results = response.get("results", [])
                current_page_ids = []

                for result in results:
                    # The actual page information is nested under the 'content' key
                    content = result.get("content", {})
                    content_type = content.get("type", "unknown")

                    # Check if it's a page by content type
                    is_page = content_type == "page"

                    if is_page:
                        page_id = content.get("id")
                        if page_id:
                            try:
                                current_page_ids.append(int(page_id))
                            except (ValueError, TypeError):
                                print(f"WARNING: Invalid page ID: {page_id}")
                    else:
                        # Skip non-page content
                        pass

                page_ids.extend(current_page_ids)

                # Update counters
                size = response.get("size", 0)
                total_size = response.get("totalSize", 0)
                total_pages += len(current_page_ids)

                print(
                    f"Retrieved {len(current_page_ids)} pages from {size} total results (batch {start // paging_limit + 1})"
                )

                # Break if no more results
                if size == 0 or len(current_page_ids) == 0:
                    break

                start += size

        except HTTPError as e:
            if e.response and e.response.status_code == 400:  # Bad Request - invalid CQL
                print(f"ERROR: Invalid CQL query syntax: {cql_query}")
                print(
                    "Please check CQL syntax. See: https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/"
                )
                print("Common issues:")
                print("- Use 'AND' not '&' between conditions")
                print("- Use double quotes around values with spaces")
                print("- Check field names and operators")
                return cls(query=cql_query, page_ids=[], total_size=0, total_pages=0)
            print(
                f"ERROR: HTTP {e.response.status_code if e.response else 'Unknown'} when executing CQL query"
            )
            return cls(query=cql_query, page_ids=[], total_size=0, total_pages=0)
        except Exception as e:
            print(f"ERROR: Unexpected error when executing CQL query: {e!s}")
            return cls(query=cql_query, page_ids=[], total_size=0, total_pages=0)

        # Remove duplicates and sort
        unique_page_ids = sorted(list(set(page_ids)))

        # Print the first three items from the results
        if unique_page_ids:
            print("First three items from the results:")
            for i, page_id in enumerate(unique_page_ids[:3]):
                print(f"  {i + 1}. Page ID: {page_id}")

        print("CQL Search Results:")
        print(f"  Query: {cql_query}")
        print(f"  Total matched content: {total_size}")
        print(f"  Pages found: {len(unique_page_ids)}")
        print(f"  Pages to export: {len(unique_page_ids)}")

        return cls(
            query=cql_query,
            page_ids=unique_page_ids,
            total_size=total_size,
            total_pages=len(unique_page_ids),
        )


class Space(BaseModel):
    key: str
    name: str
    description: str
    homepage: int

    @property
    def pages(self) -> list[int]:
        homepage = Page.from_id(self.homepage)
        return [self.homepage, *homepage.descendants]

    def export(self) -> None:
        export_pages(self.pages)

    @classmethod
    def from_json(cls, data: JsonResponse) -> "Space":
        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            description=data.get("description", {}).get("plain", {}).get("value", ""),
            homepage=data.get("homepage", {}).get("id"),
        )

    @classmethod
    @functools.lru_cache(maxsize=100)
    def from_key(cls, space_key: str) -> "Space":
        return cls.from_json(
            cast("JsonResponse", confluence.get_space(space_key, expand="homepage"))
        )


class Label(BaseModel):
    id: str
    name: str
    prefix: str

    @classmethod
    def from_json(cls, data: JsonResponse) -> "Label":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            prefix=data.get("prefix", ""),
        )


class Document(BaseModel):
    title: str
    space: Space
    ancestors: list[int]

    @property
    def _template_vars(self) -> dict[str, str]:
        return {
            "space_key": sanitize_filename(self.space.key),
            "space_name": sanitize_filename(self.space.name),
            "homepage_id": str(self.space.homepage),
            "homepage_title": sanitize_filename(Page.from_id(self.space.homepage).title),
            "ancestor_ids": "/".join(str(a) for a in self.ancestors),
            "ancestor_titles": "/".join(
                sanitize_filename(Page.from_id(a).title) for a in self.ancestors
            ),
        }


class Attachment(Document):
    id: str
    file_size: int
    media_type: str
    media_type_description: str
    file_id: str
    collection_name: str
    download_link: str
    comment: str
    version: Version

    @property
    def extension(self) -> str:
        if self.comment == "draw.io diagram" and self.media_type == "application/vnd.jgraph.mxfile":
            return ".drawio"
        if self.comment == "draw.io preview" and self.media_type == "image/png":
            return ".drawio.png"

        return mimetypes.guess_extension(self.media_type) or ""

    @property
    def filename(self) -> str:
        return f"{self.file_id}{self.extension}"

    @property
    def _template_vars(self) -> dict[str, str]:
        return {
            **super()._template_vars,
            "attachment_id": str(self.id),
            "attachment_title": sanitize_filename(self.title),
            "attachment_file_id": sanitize_filename(self.file_id),
            "attachment_extension": self.extension,
        }

    @property
    def export_path(self) -> Path:
        filepath_template = Template(settings.export.attachment_path.replace("{", "${"))
        return Path(filepath_template.safe_substitute(self._template_vars))

    @classmethod
    def from_json(cls, data: JsonResponse) -> "Attachment":
        extensions = data.get("extensions", {})
        container = data.get("container", {})
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            space=Space.from_key(data.get("_expandable", {}).get("space", "").split("/")[-1]),
            file_size=extensions.get("fileSize", 0),
            media_type=extensions.get("mediaType", ""),
            media_type_description=extensions.get("mediaTypeDescription", ""),
            file_id=extensions.get("fileId", ""),
            collection_name=extensions.get("collectionName", ""),
            download_link=data.get("_links", {}).get("download", ""),
            comment=extensions.get("comment", ""),
            ancestors=[
                *[ancestor.get("id") for ancestor in container.get("ancestors", [])],
                container.get("id"),
            ][1:],
            version=Version.from_json(data.get("version", {})),
        )

    @classmethod
    def from_page_id(cls, page_id: int) -> list["Attachment"]:
        attachments = []
        start = 0
        paging_limit = 50
        size = paging_limit  # Initialize to limit to enter the loop

        while size >= paging_limit:
            response = cast(
                "JsonResponse",
                confluence.get_attachments_from_content(
                    page_id,
                    start=start,
                    limit=paging_limit,
                    expand="container.ancestors,version",
                ),
            )

            attachments.extend([cls.from_json(att) for att in response.get("results", [])])

            size = response.get("size", 0)
            start += size

        return attachments

    def export(self) -> None:
        filepath = settings.export.output_path / self.export_path
        if filepath.exists():
            return

        try:
            response = confluence._session.get(str(confluence.url + self.download_link))
            response.raise_for_status()  # Raise error if request fails
        except HTTPError:
            print(f"There is no attachment with title '{self.title}'. Skipping export.")
            return

        save_file(
            filepath,
            response.content,
        )


class Page(Document):
    id: int
    body: str
    body_export: str
    editor2: str
    labels: list["Label"]
    attachments: list["Attachment"]

    @property
    def descendants(self) -> list[int]:
        cql_query = f"ancestor={self.id} AND type=page"
        page_ids = []
        start = 0
        paging_limit = 100
        total_size = paging_limit  # Initialize to limit to enter the loop

        ids_exp = jmespath.compile("results[].content.id.to_number(@)")

        try:
            while start < total_size:
                response = cast(
                    "JsonResponse",
                    confluence.cql(cql_query, limit=paging_limit, start=start),
                )

                page_ids.extend(ids_exp.search(response))

                size = response.get("size", 0)
                total_size = response.get("totalSize", 0)

                if size == 0:
                    break

                start += size

        except HTTPError as e:
            if e.response.status_code == 404:  # noqa: PLR2004
                print(
                    f"WARNING: Content with ID {self.id} not found (404) when fetching descendants."
                )
                return []
            return []
        except Exception as e:  # noqa: BLE001
            print(
                f"ERROR: Unexpected error when fetching descendants for content ID {self.id}: {e!s}"
            )
            return []

        return page_ids

    @property
    def _template_vars(self) -> dict[str, str]:
        return {
            **super()._template_vars,
            "page_id": str(self.id),
            "page_title": sanitize_filename(self.title),
        }

    @property
    def export_path(self) -> Path:
        filepath_template = Template(settings.export.page_path.replace("{", "${"))
        return Path(filepath_template.safe_substitute(self._template_vars))

    @property
    def html(self) -> str:
        if settings.export.include_document_title:
            return f"<h1>{self.title}</h1>{self.body}"
        return self.body

    @property
    def markdown(self) -> str:
        return self.Converter(self).markdown

    def export(self) -> None:
        if DEBUG:
            self.export_body()
        self.export_markdown()
        self.export_attachments()

    def export_with_descendants(self) -> None:
        export_pages([self.id, *self.descendants])

    def export_body(self) -> None:
        soup = BeautifulSoup(self.html, "html.parser")
        save_file(
            settings.export.output_path
            / self.export_path.parent
            / f"{self.export_path.stem}_body_view.html",
            str(soup.prettify()),
        )
        soup = BeautifulSoup(self.body_export, "html.parser")
        save_file(
            settings.export.output_path
            / self.export_path.parent
            / f"{self.export_path.stem}_body_export_view.html",
            str(soup.prettify()),
        )
        save_file(
            settings.export.output_path
            / self.export_path.parent
            / f"{self.export_path.stem}_body_editor2.xml",
            str(self.editor2),
        )

    def export_markdown(self) -> None:
        save_file(
            settings.export.output_path / self.export_path,
            self.markdown,
        )

    def export_attachments(self) -> None:
        for attachment in self.attachments:
            if (
                attachment.filename.endswith(".drawio")
                and f"diagramName={attachment.title}" in self.body
            ):
                attachment.export()
                continue
            if (
                attachment.filename.endswith(".drawio.png")
                and attachment.title.replace(" ", "%20") in self.body_export
            ):
                attachment.export()
                continue
            if attachment.file_id in self.body:
                attachment.export()
                continue

    def get_attachment_by_id(self, attachment_id: str) -> Attachment:
        return next(attachment for attachment in self.attachments if attachment_id in attachment.id)

    def get_attachment_by_file_id(self, file_id: str) -> Attachment:
        return next(attachment for attachment in self.attachments if attachment.file_id == file_id)

    def get_attachments_by_title(self, title: str) -> list[Attachment]:
        return [attachment for attachment in self.attachments if attachment.title == title]

    @classmethod
    def from_json(cls, data: JsonResponse) -> "Page":
        return cls(
            id=data.get("id", 0),
            title=data.get("title", ""),
            space=Space.from_key(data.get("_expandable", {}).get("space", "").split("/")[-1]),
            body=data.get("body", {}).get("view", {}).get("value", ""),
            body_export=data.get("body", {}).get("export_view", {}).get("value", ""),
            editor2=data.get("body", {}).get("editor2", {}).get("value", ""),
            labels=[
                Label.from_json(label)
                for label in data.get("metadata", {}).get("labels", {}).get("results", [])
            ],
            attachments=Attachment.from_page_id(data.get("id", 0)),
            ancestors=[ancestor.get("id") for ancestor in data.get("ancestors", [])][1:],
        )

    @classmethod
    @functools.lru_cache(maxsize=1000)
    def from_id(cls, page_id: int) -> "Page":
        try:
            return cls.from_json(
                cast(
                    "JsonResponse",
                    confluence.get_page_by_id(
                        page_id,
                        expand="body.view,body.export_view,body.editor2,metadata.labels,"
                        "metadata.properties,ancestors",
                    ),
                )
            )
        except ApiError as e:
            print(f"WARNING: Could not access page with ID {page_id}: {e!s}")
            # Return a minimal page object with error information
            return cls(
                id=page_id,
                title="[Error: Page not accessible]",
                space=Space(key="", name="", description="", homepage=0),
                body="",
                body_export="",
                editor2="",
                labels=[],
                attachments=[],
                ancestors=[],
            )

    @classmethod
    def from_url(cls, page_url: str) -> "Page":
        """Retrieve a Page object given a Confluence page URL."""
        path = urllib.parse.urlparse(page_url).path.rstrip("/")
        if match := re.search(r"/wiki/.+?/pages/(\d+)", path):
            page_id = match.group(1)
            return Page.from_id(int(page_id))

        if match := re.search(r"^/([^/]+?)/([^/]+)$", path):
            space_key = urllib.parse.unquote_plus(match.group(1))
            page_title = urllib.parse.unquote_plus(match.group(2))
            page_data = cast(
                "JsonResponse",
                confluence.get_page_by_title(space=space_key, title=page_title, expand="version"),
            )
            return Page.from_id(page_data["id"])

        msg = f"Could not parse page URL {page_url}."
        raise ValueError(msg)

    class Converter(TableConverter, MarkdownConverter):
        """Create a custom MarkdownConverter for Confluence HTML to Markdown conversion."""

        class Options(MarkdownConverter.DefaultOptions):
            bullets = "-"
            heading_style = ATX
            macros_to_ignore: Set[str] = frozenset(["qc-read-and-understood-signature-box"])
            front_matter_indent = 2

        def __init__(self, page: "Page", **options) -> None:  # noqa: ANN003
            super().__init__(**options)
            self.page = page
            self.page_properties = {}

        @property
        def markdown(self) -> str:
            md_body = self.convert(self.page.html)
            markdown = f"{self.front_matter}\n"
            if settings.export.page_breadcrumbs:
                markdown += f"{self.breadcrumbs}\n"
            markdown += f"{md_body}\n"
            return markdown

        @property
        def front_matter(self) -> str:
            indent = self.options["front_matter_indent"]
            self.set_page_properties(tags=self.labels)

            if not self.page_properties:
                return ""

            yml = yaml.dump(self.page_properties, indent=indent).strip()
            # Indent the root level list items
            yml = re.sub(r"^( *)(- )", r"\1" + " " * indent + r"\2", yml, flags=re.MULTILINE)
            return f"---\n{yml}\n---\n"

        @property
        def breadcrumbs(self) -> str:
            return (
                " > ".join([self.convert_page_link(ancestor) for ancestor in self.page.ancestors])
                + "\n"
            )

        @property
        def labels(self) -> list[str]:
            return [f"#{label.name}" for label in self.page.labels]

        def set_page_properties(self, **props: list[str] | str | None) -> None:
            for key, value in props.items():
                if value:
                    self.page_properties[sanitize_key(key)] = value

        def convert_page_properties(
            self, el: BeautifulSoup, text: str, parent_tags: list[str]
        ) -> None:
            rows = [
                cast("list[Tag]", tr.find_all(["th", "td"]))
                for tr in cast("list[Tag]", el.find_all("tr"))
                if tr
            ]
            if not rows:
                return

            props = {
                row[0].get_text(strip=True): self.convert(str(row[1])).strip()
                for row in rows
                if len(row) == 2  # noqa: PLR2004
            }

            self.set_page_properties(**props)

        def convert_alert(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            """Convert Confluence info macros to Markdown GitHub style alerts.

            GitHub specific alert types: https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts
            """
            alert_type_map = {
                "info": "IMPORTANT",
                "panel": "NOTE",
                "tip": "TIP",
                "note": "WARNING",
                "warning": "CAUTION",
            }

            alert_type = alert_type_map.get(str(el["data-macro-name"]), "NOTE")

            blockquote = super().convert_blockquote(el, text, parent_tags)
            return f"\n> [!{alert_type}]{blockquote}"

        def convert_div(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            # Handle Confluence macros
            if el.has_attr("data-macro-name"):
                macro_name = str(el["data-macro-name"])
                if macro_name in self.options["macros_to_ignore"]:
                    return ""

                macro_handlers = {
                    "panel": self.convert_alert,
                    "info": self.convert_alert,
                    "note": self.convert_alert,
                    "tip": self.convert_alert,
                    "warning": self.convert_alert,
                    "details": self.convert_page_properties,
                    "drawio": self.convert_drawio,
                    "scroll-ignore": self.convert_hidden_content,
                    "toc": self.convert_toc,
                    "jira": self.convert_jira_table,
                    "attachments": self.convert_attachments,
                }
                if macro_name in macro_handlers:
                    return macro_handlers[macro_name](el, text, parent_tags)

            class_handlers = {
                "expand-container": self.convert_expand_container,
                "columnLayout": self.convert_column_layout,
            }
            for class_name, handler in class_handlers.items():
                if class_name in str(el.get("class", "")):
                    return handler(el, text, parent_tags)

            return super().convert_div(el, text, parent_tags)

        def convert_expand_container(
            self, el: BeautifulSoup, text: str, parent_tags: list[str]
        ) -> str:
            """Convert expand-container div to HTML details element."""
            # Extract summary text from expand-control-text
            summary_element = el.find("span", class_="expand-control-text")
            summary_text = (
                summary_element.get_text().strip() if summary_element else "Click here to expand..."
            )

            # Extract content from expand-content
            content_element = el.find("div", class_="expand-content")
            # Recursively convert the content
            content = (
                self.process_tag(content_element, parent_tags).strip() if content_element else ""
            )

            # Return as details element
            return f"\n<details>\n<summary>{summary_text}</summary>\n\n{content}\n\n</details>\n\n"

        def convert_span(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            if el.has_attr("data-macro-name"):
                if el["data-macro-name"] == "jira":
                    return self.convert_jira_issue(el, text, parent_tags)

            return text

        def convert_attachments(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            file_header = el.find("th", {"class": "filename-column"})
            file_header_text = file_header.text.strip() if file_header else "File"

            modified_header = el.find("th", {"class": "modified-column"})
            modified_header_text = modified_header.text.strip() if modified_header else "Modified"

            def _get_path(p: Path) -> str:
                attachment_path = self._get_path_for_href(p, settings.export.attachment_href)
                return attachment_path.replace(" ", "%20")

            rows = [
                {
                    "file": f"[{att.title}]({_get_path(att.export_path)})",
                    "modified": f"{att.version.friendly_when} by {self.convert_user(att.version.by)}",  # noqa: E501
                }
                for att in self.page.attachments
            ]

            html = f"""<table>
            <tr><th>{file_header_text}</th><th>{modified_header_text}</th></tr>
            {"".join(f"<tr><td>{row['file']}</td><td>{row['modified']}</td></tr>" for row in rows)}
            </table>"""

            return (
                f"\n\n{self.convert_table(BeautifulSoup(html, 'html.parser'), text, parent_tags)}\n"
            )

        def convert_column_layout(
            self, el: BeautifulSoup, text: str, parent_tags: list[str]
        ) -> str:
            cells = el.find_all("div", {"class": "cell"})

            if len(cells) < 2:  # noqa: PLR2004
                return super().convert_div(el, text, parent_tags)

            html = f"<table><tr>{''.join([f'<td>{cell!s}</td>' for cell in cells])}</tr></table>"

            return self.convert_table(BeautifulSoup(html, "html.parser"), text, parent_tags)

        def convert_jira_table(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            jira_tables = BeautifulSoup(self.page.body_export, "html.parser").find_all(
                "div", {"class": "jira-table"}
            )

            if len(jira_tables) == 0:
                print("No Jira table found. Ignoring.")
                return text

            if len(jira_tables) > 1:
                print("Multiple Jira tables are not supported. Ignoring.")
                return text

            return self.process_tag(jira_tables[0], parent_tags)

        def convert_toc(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            tocs = BeautifulSoup(self.page.body_export, "html.parser").find_all(
                "div", {"class": "toc-macro"}
            )

            if len(tocs) == 0:
                print("Could not find TOC macro. Ignoring.")
                return text

            if len(tocs) > 1:
                print("Multiple TOC macros are not supported. Ignoring.")
                return text

            return self.process_tag(tocs[0], parent_tags)

        def convert_hidden_content(
            self, el: BeautifulSoup, text: str, parent_tags: list[str]
        ) -> str:
            content = super().convert_p(el, text, parent_tags)
            return f"\n<!--{content}-->\n"

        def convert_jira_issue(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            issue_key = el.get("data-jira-key")
            link = cast("BeautifulSoup", el.find("a", {"class": "jira-issue-key"}))
            if not issue_key:
                return self.process_tag(link, parent_tags)
            if not link:
                return text

            try:
                issue = JiraIssue.from_key(str(issue_key))
                return f"[[{issue.key}] {issue.summary}]({link.get('href')})"
            except HTTPError:
                return f"[[{issue_key}]]({link.get('href')})"

        def convert_pre(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            if not text:
                return ""

            code_language = ""
            if el.has_attr("data-syntaxhighlighter-params"):
                match = re.search(r"brush:\s*([^;]+)", str(el["data-syntaxhighlighter-params"]))
                if match:
                    code_language = match.group(1)

            return f"\n\n```{code_language}\n{text}\n```\n\n"

        def convert_sub(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            return f"<sub>{text}</sub>"

        def convert_sup(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            """Convert superscript to Markdown footnotes."""
            if el.previous_sibling is None:
                return f"[^{text}]:"  # Footnote definition
            return f"[^{text}]"  # f"<sup>{text}</sup>"

        def convert_a(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:  # noqa: PLR0911
            if "user-mention" in str(el.get("class")):
                return self.convert_user_mention(el, text, parent_tags)
            if "createpage.action" in str(el.get("href")) or "createlink" in str(el.get("class")):
                if fallback := BeautifulSoup(self.page.editor2, "html.parser").find(
                    "a", string=text
                ):
                    return self.convert_a(fallback, text, parent_tags)  # type: ignore -
                return f"[[{text}]]"
            if "page" in str(el.get("data-linked-resource-type")):
                page_id = str(el.get("data-linked-resource-id", ""))
                if page_id and page_id != "null":
                    return self.convert_page_link(int(page_id))
            if "attachment" in str(el.get("data-linked-resource-type")):
                return self.convert_attachment_link(el, text, parent_tags)
            if match := re.search(r"/wiki/.+?/pages/(\d+)", str(el.get("href", ""))):
                page_id = match.group(1)
                return self.convert_page_link(int(page_id))
            if str(el.get("href", "")).startswith("#"):
                # Handle heading links
                return f"[{text}](#{sanitize_key(text, '-')})"

            return super().convert_a(el, text, parent_tags)

        def convert_page_link(self, page_id: int) -> str:
            if not page_id:
                msg = "Page link does not have valid page_id."
                raise ValueError(msg)

            page = Page.from_id(page_id)
            page_path = self._get_path_for_href(page.export_path, settings.export.page_href)

            return f"[{page.title}]({page_path.replace(' ', '%20')})"

        def convert_attachment_link(
            self, el: BeautifulSoup, text: str, parent_tags: list[str]
        ) -> str:
            if attachment_file_id := el.get("data-media-id"):
                attachment = self.page.get_attachment_by_file_id(str(attachment_file_id))
            elif attachment_id := el.get("data-linked-resource-id"):
                attachment = self.page.get_attachment_by_id(str(attachment_id))
            path = self._get_path_for_href(attachment.export_path, settings.export.attachment_href)
            return f"[{attachment.title}]({path.replace(' ', '%20')})"

        def convert_time(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            if el.has_attr("datetime"):
                return f"{el['datetime']}"

            return f"{text}"

        def convert_user_mention(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            if el.has_attr("data-account-id"):
                return self.convert_user(User.from_accountid(str(el.get("data-account-id"))))

            return self.convert_user_name(text)

        def convert_user(self, user: User) -> str:
            return self.convert_user_name(user.display_name)

        def convert_user_name(self, name: str) -> str:
            return name.removesuffix("(Unlicensed)").removesuffix("(Deactivated)").strip()

        def convert_li(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            md = super().convert_li(el, text, parent_tags)
            bullet = self.options["bullets"][0]

            # Convert Confluence task lists to GitHub task lists
            if el.has_attr("data-inline-task-id"):
                is_checked = el.has_attr("class") and "checked" in el["class"]
                return md.replace(f"{bullet} ", f"{bullet} {'[x]' if is_checked else '[ ]'} ", 1)

            return md

        def convert_img(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            file_id = el.get("data-media-id")
            if not file_id:
                return ""

            attachment = self.page.get_attachment_by_file_id(str(file_id))
            path = self._get_path_for_href(attachment.export_path, settings.export.attachment_href)
            el["src"] = path.replace(" ", "%20")
            if "_inline" in parent_tags:
                parent_tags.remove("_inline")  # Always show images.
            return super().convert_img(el, text, parent_tags)

        def convert_drawio(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            if match := re.search(r"\|diagramName=(.+?)\|", str(el)):
                drawio_name = match.group(1)
                preview_name = f"{drawio_name}.png"
                drawio_attachments = self.page.get_attachments_by_title(drawio_name)
                preview_attachments = self.page.get_attachments_by_title(preview_name)

                if not drawio_attachments or not preview_attachments:
                    return f"\n<!-- Drawio diagram `{drawio_name}` not found -->\n\n"

                drawio_path = self._get_path_for_href(
                    drawio_attachments[0].export_path, settings.export.attachment_href
                )
                preview_path = self._get_path_for_href(
                    preview_attachments[0].export_path, settings.export.attachment_href
                )

                drawio_image_embedding = f"![{drawio_name}]({preview_path.replace(' ', '%20')})"
                drawio_link = f"[{drawio_image_embedding}]({drawio_path.replace(' ', '%20')})"
                return f"\n{drawio_link}\n\n"

            return ""

        def convert_table(self, el: BeautifulSoup, text: str, parent_tags: list[str]) -> str:
            if el.has_attr("class") and "metadata-summary-macro" in el["class"]:
                return self.convert_page_properties_report(el, text, parent_tags)

            return super().convert_table(el, text, parent_tags)

        def convert_page_properties_report(
            self, el: BeautifulSoup, text: str, parent_tags: list[str]
        ) -> str:
            data_cql = el.get("data-cql")
            if not data_cql:
                return ""
            soup = BeautifulSoup(self.page.body_export, "html.parser")
            table = soup.find("table", {"data-cql": data_cql})
            if not table:
                return ""
            return super().convert_table(table, "", parent_tags)  # type: ignore -

        def _get_path_for_href(self, path: Path, style: Literal["absolute", "relative"]) -> str:
            """Get the path to use in href attributes based on settings."""
            if style == "absolute":
                # Note that usually absolute would be
                # something like this: (settings.export.output_path / path).absolute()
                # In this case the URL will be "absolute" to the export path.
                # This is useful for local file links.
                result = "/" + str(path).lstrip("/")
            else:
                result = os.path.relpath(path, self.page.export_path.parent)
            return result


def export_page(page_id: int) -> None:
    """Export a Confluence page to Markdown.

    Args:
        page_id: The page id.
        output_path: The output path.
    """
    page = Page.from_id(page_id)
    page.export()


def export_pages(page_ids: list[int]) -> None:
    """Export a list of Confluence pages to Markdown.

    Args:
        page_ids: List of pages to export.
        output_path: The output path.
    """
    for page_id in (pbar := tqdm(page_ids, smoothing=0.05)):
        pbar.set_postfix_str(f"Exporting page {page_id}")
        export_page(page_id)
