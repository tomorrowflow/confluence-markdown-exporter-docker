"""Input validation for different export modes."""

from confluence_markdown_exporter.confluence import Page
from confluence_markdown_exporter.confluence import SearchResults
from confluence_markdown_exporter.confluence import Space


def validate_page_id(page_id: str) -> None:
    """Validate that page ID exists and is accessible.

    Args:
        page_id: The page ID to validate

    Raises:
        ValueError: If page ID is invalid or inaccessible
    """
    try:
        # Convert to int to validate format
        page_id_int = int(page_id)

        # Try to fetch the page to validate accessibility
        page = Page.from_id(page_id_int)

        # Check if page has error information (from confluence.py line 623-633)
        if page.title == "[Error: Page not accessible]":
            raise ValueError(f"Page with ID '{page_id}' is not accessible or does not exist")

    except ValueError as e:
        if "invalid literal for int()" in str(e):
            raise ValueError(f"Invalid page ID format '{page_id}': must be a numeric ID")
        raise  # Re-raise the original ValueError
    except Exception as e:
        raise ValueError(f"Invalid or inaccessible page ID '{page_id}': {e}")


def validate_space_key(space_key: str) -> None:
    """Validate that space key exists and is accessible.

    Args:
        space_key: The space key to validate

    Raises:
        ValueError: If space key is invalid or inaccessible
    """
    try:
        space = Space.from_key(space_key)

        # Basic validation - check if space has required attributes
        if not space.key or not space.name:
            raise ValueError(f"Space with key '{space_key}' appears to be invalid")

    except Exception as e:
        raise ValueError(f"Invalid or inaccessible space key '{space_key}': {e}")


def validate_cql_query(cql_query: str, limit: int = 100) -> None:
    """Validate CQL query syntax and test execution.

    Args:
        cql_query: The CQL query to validate
        limit: Maximum number of results to test with (default: 100)

    Raises:
        ValueError: If CQL query is invalid or returns no results
    """
    # Check for empty or whitespace-only query
    if not cql_query or not cql_query.strip():
        raise ValueError("CQL query cannot be empty")

    try:
        # Test the query with a small limit to avoid performance issues
        test_limit = min(limit, 10)
        results = SearchResults.from_cql(cql_query, limit=test_limit)

        # Check if query returned any results
        if not results.page_ids:
            raise ValueError(f"CQL query returned no results: '{cql_query}'")

    except Exception as e:
        raise ValueError(f"Invalid CQL query '{cql_query}': {e}")
