"""Content collection abstraction for different export modes."""

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List

from confluence_markdown_exporter.confluence import Page
from confluence_markdown_exporter.confluence import SearchResults
from confluence_markdown_exporter.confluence import Space


class ContentCollector(ABC):
    """Abstract base class for collecting content from different sources."""

    @abstractmethod
    def collect_pages(self) -> list[Page]:
        """Collect pages based on the export mode."""

    @abstractmethod
    def get_spaces_involved(self) -> list[str]:
        """Get list of space keys involved in this export."""

    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of what's being exported."""


class SpaceContentCollector(ContentCollector):
    """Collects all pages from a specific Confluence space."""

    def __init__(self, space_key: str):
        self.space_key = space_key
        self._space = None
        self._pages = None

    def collect_pages(self) -> list[Page]:
        """Collect all pages from the space."""
        if self._pages is None:
            if self._space is None:
                self._space = Space.from_key(self.space_key)

            # Convert page IDs to Page objects
            self._pages = [Page.from_id(page_id) for page_id in self._space.pages]

        return self._pages

    def get_spaces_involved(self) -> list[str]:
        """Return the single space key."""
        return [self.space_key]

    def get_description(self) -> str:
        """Get description of the space export."""
        return f"Space: {self.space_key}"


class PageContentCollector(ContentCollector):
    """Collects a single page by ID."""

    def __init__(self, page_id: str):
        self.page_id = page_id
        self._page = None

    def collect_pages(self) -> list[Page]:
        """Collect the single page."""
        if self._page is None:
            # Convert string page_id to int for Page.from_id
            self._page = Page.from_id(int(self.page_id))

        return [self._page]

    def get_spaces_involved(self) -> list[str]:
        """Extract space from page metadata."""
        if self._page is None:
            self.collect_pages()  # Load page to get space info

        # At this point _page should not be None, but add safety check
        if self._page is not None:
            return [self._page.space.key]
        return []

    def get_description(self) -> str:
        """Get description of the page export."""
        return f"Page ID: {self.page_id}"


class SearchContentCollector(ContentCollector):
    """Collects pages based on CQL search query."""

    def __init__(self, cql_query: str, limit: int = 100):
        self.cql_query = cql_query
        self.limit = limit
        self._pages = None
        self._search_results = None

    def collect_pages(self) -> list[Page]:
        """Collect pages based on CQL search."""
        if self._pages is None:
            # Execute search to get page IDs
            if self._search_results is None:
                self._search_results = SearchResults.from_cql(self.cql_query, limit=self.limit)

            # Convert page IDs to Page objects
            self._pages = [Page.from_id(page_id) for page_id in self._search_results.page_ids]

        return self._pages

    def get_spaces_involved(self) -> list[str]:
        """Extract unique spaces from collected pages."""
        if self._pages is None:
            self.collect_pages()

        # Get unique space keys from all pages
        if self._pages is not None:
            space_keys = list(set(page.space.key for page in self._pages))
            return space_keys
        return []

    def get_description(self) -> str:
        """Get description of the search export."""
        return f"CQL Query: {self.cql_query}"
