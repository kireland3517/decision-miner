import os
from crewai.tools import tool
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()


def get_tavily_client() -> TavilyClient:
    """Get configured Tavily client."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables")
    return TavilyClient(api_key=api_key)


@tool("Search Reddit and Forums")
def tavily_search_tool(query: str, max_results: int = 10) -> str:
    """
    Search the web for discussions, forum posts, and Reddit threads related to the query.
    Use this to find real human discussions about workplace frustrations and decision-making challenges.

    Args:
        query: Search query - include specific terms like 'reddit', subreddit names, or forum names
        max_results: Maximum number of results to return (default 10)

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
        content = result.get("content", "")[:500]  # Truncate long content
        raw_content = result.get("raw_content", "")[:1000] if result.get("raw_content") else ""

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
