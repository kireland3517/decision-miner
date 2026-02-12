import os
import logging
from crewai.tools import tool
from tavily import TavilyClient
from dotenv import load_dotenv

logger = logging.getLogger("decision_miner.tools")

load_dotenv()


def get_tavily_client() -> TavilyClient:
    """Get configured Tavily client."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables")
    return TavilyClient(api_key=api_key)


@tool("Search Reddit and Forums")
def tavily_search_tool(query: str, max_results: int = 10, max_content_chars: int = 3000, max_raw_chars: int = 5000) -> str:
    """
    Search the web for discussions, forum posts, and Reddit threads related to the query.
    Use this to find real human discussions about workplace frustrations and decision-making challenges.

    Args:
        query: Search query - include specific terms like 'reddit', subreddit names, or forum names
        max_results: Maximum number of results to return (default 10)
        max_content_chars: Max characters for content summary (default 3000)
        max_raw_chars: Max characters for raw content (default 5000)

    Returns:
        Formatted string of search results with titles, URLs, and content snippets
    """
    client = get_tavily_client()

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        include_raw_content=True,
    )

    results = []
    for i, result in enumerate(response.get("results", []), 1):
        title = result.get("title", "No title")
        url = result.get("url", "")

        full_content = result.get("content", "")
        full_raw = result.get("raw_content", "") or ""
        logger.info(f"Result {i} '{title}': content={len(full_content)} chars, raw_content={len(full_raw)} chars, url={url}")

        content = full_content[:max_content_chars]
        raw_content = full_raw[:max_raw_chars]

        result_text = f"""
---
Result {i}: {title}
URL: {url}
Summary: {content}
"""
        if raw_content:
            result_text += f"Full Content Preview:\n{raw_content}\n"

        results.append(result_text)

    if not results:
        return "No results found for this query."

    return "\n".join(results)


@tool("Search Subreddit")
def search_subreddit(subreddit: str, topic: str, max_results: int = 10) -> str:
    """
    Search for discussions within a specific subreddit about a topic.

    Args:
        subreddit: Name of the subreddit (without r/) e.g., 'socialwork', 'sysadmin', 'nursing'
        topic: Topic to search for within that subreddit
        max_results: Maximum number of results to return

    Returns:
        Formatted search results from that subreddit
    """
    query = f"site:reddit.com/r/{subreddit} {topic}"
    return tavily_search_tool(query, max_results)


@tool("Extract Full Page Content")
def tavily_extract_tool(urls: str) -> str:
    """
    Extract the full cleaned content from one or more URLs.
    Use this after finding promising Reddit threads via search to get the complete
    thread content including all comments.

    Args:
        urls: Comma-separated list of URLs to extract content from (max 5)

    Returns:
        Full extracted content from each URL
    """
    client = get_tavily_client()

    url_list = [u.strip() for u in urls.split(",")][:5]

    logger.info(f"Extracting full content from {len(url_list)} URLs")

    response = client.extract(urls=url_list)

    results = []
    for item in response.get("results", []):
        url = item.get("url", "")
        raw_content = item.get("raw_content", "")
        content_len = len(raw_content)
        logger.info(f"Extracted {content_len} chars from {url}")

        display_content = raw_content[:10000]
        truncation_note = f"\n[...truncated, {content_len} total chars]" if content_len > 10000 else ""

        results.append(f"""
---
URL: {url}
Content ({content_len} chars):
{display_content}{truncation_note}
""")

    failed = response.get("failed_results", [])
    if failed:
        results.append(f"\nFailed to extract: {', '.join(f.get('url', '?') for f in failed)}")

    return "\n".join(results) if results else "No content could be extracted."
