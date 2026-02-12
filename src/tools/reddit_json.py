"""
Reddit JSON Thread Fetcher

Fetches full Reddit thread content using the public .json endpoint.
No API credentials required. Rate limited to stay under Reddit's
unauthenticated threshold of ~10 requests/minute.
"""

import logging
import time
import requests
from crewai.tools import tool

logger = logging.getLogger("decision_miner.tools")

HEADERS = {
    "User-Agent": "DecisionMiner/1.0 (research tool)"
}

_last_request_time = 0.0
_MIN_REQUEST_INTERVAL = 6.0  # seconds between requests


def _rate_limit():
    """Enforce minimum interval between Reddit requests."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        wait = _MIN_REQUEST_INTERVAL - elapsed
        logger.debug(f"Rate limiting: waiting {wait:.1f}s")
        time.sleep(wait)
    _last_request_time = time.time()


def _normalize_reddit_url(url: str) -> str:
    """Normalize a Reddit URL to its .json form."""
    url = url.split("?")[0].rstrip("/")

    if "reddit.com" not in url:
        raise ValueError(f"Not a Reddit URL: {url}")

    if url.startswith("http://"):
        url = "https://" + url[7:]
    elif not url.startswith("https://"):
        url = "https://" + url

    url = url.replace("old.reddit.com", "www.reddit.com")
    if "://reddit.com" in url:
        url = url.replace("://reddit.com", "://www.reddit.com")

    if not url.endswith(".json"):
        url += ".json"

    return url


def _extract_comments(children: list, max_depth: int = 4) -> list[dict]:
    """
    Recursively extract comments from Reddit's nested JSON structure.

    Reddit returns comments as kind="t1" objects with nested replies.
    "more" objects (load-more stubs) are skipped since they require auth.
    """
    comments = []

    for child in children:
        kind = child.get("kind", "")
        data = child.get("data", {})

        if kind == "t1":
            depth = data.get("depth", 0)
            if depth > max_depth:
                continue

            comments.append({
                "author": data.get("author", "[deleted]"),
                "body": data.get("body", ""),
                "score": data.get("score", 0),
                "depth": depth,
            })

            replies = data.get("replies", "")
            if isinstance(replies, dict):
                reply_children = replies.get("data", {}).get("children", [])
                comments.extend(_extract_comments(reply_children, max_depth))

        elif kind == "more":
            count = data.get("count", 0)
            if count > 0:
                logger.debug(f"Skipping 'more' node with {count} additional comments")

    return comments


def _format_comment(comment: dict) -> str:
    """Format a single comment with indentation based on depth."""
    indent = "  " * comment["depth"]
    score_str = f"[{comment['score']} pts]" if comment["score"] else ""
    return f"{indent}u/{comment['author']} {score_str}:\n{indent}  {comment['body']}"


def fetch_reddit_thread(url: str, max_depth: int = 4, max_comments: int = 50) -> dict:
    """
    Fetch and parse a Reddit thread via the .json endpoint.

    Returns dict with: title, selftext, author, score, num_comments,
                       comments, subreddit, url, error
    """
    try:
        json_url = _normalize_reddit_url(url)
    except ValueError as e:
        return {"error": str(e), "url": url}

    _rate_limit()

    try:
        resp = requests.get(json_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        return {"error": f"HTTP {resp.status_code}", "url": url}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}", "url": url}

    try:
        data = resp.json()
    except ValueError:
        return {"error": "Invalid JSON response", "url": url}

    # Reddit returns [post_listing, comments_listing]
    if not isinstance(data, list) or len(data) < 2:
        return {"error": "Unexpected Reddit JSON structure", "url": url}

    post_children = data[0].get("data", {}).get("children", [])
    if not post_children:
        return {"error": "No post data found", "url": url}

    post_data = post_children[0].get("data", {})

    comment_children = data[1].get("data", {}).get("children", [])
    comments = _extract_comments(comment_children, max_depth)

    # Sort by score descending, take top N
    comments.sort(key=lambda c: c.get("score", 0), reverse=True)
    comments = comments[:max_comments]

    return {
        "title": post_data.get("title", ""),
        "selftext": post_data.get("selftext", ""),
        "author": post_data.get("author", "[deleted]"),
        "score": post_data.get("score", 0),
        "num_comments": post_data.get("num_comments", 0),
        "subreddit": post_data.get("subreddit", ""),
        "comments": comments,
        "url": url,
        "error": None,
    }


@tool("Fetch Reddit Thread")
def fetch_reddit_thread_tool(url: str, max_comments: int = 30) -> str:
    """
    Fetch the full content of a Reddit thread including the original post and top comments.
    No Reddit API credentials needed. Use this when you have a Reddit URL from search results
    and want to read the actual discussion in detail.

    Args:
        url: Full Reddit thread URL (e.g., https://www.reddit.com/r/socialwork/comments/abc123/title/)
        max_comments: Maximum number of comments to include (default 30, sorted by score)

    Returns:
        Formatted thread content with original post and top comments
    """
    result = fetch_reddit_thread(url, max_depth=4, max_comments=max_comments)

    if result.get("error"):
        return f"Error fetching thread: {result['error']} (URL: {result['url']})"

    output_parts = [
        f"## r/{result['subreddit']}: {result['title']}",
        f"**Author:** u/{result['author']} | **Score:** {result['score']} | **Comments:** {result['num_comments']}",
        "",
        "### Original Post",
        result["selftext"] or "[No text content - may be a link post]",
        "",
        f"### Top Comments ({len(result['comments'])} shown)",
    ]

    for comment in result["comments"]:
        output_parts.append("")
        output_parts.append(_format_comment(comment))

    full_output = "\n".join(output_parts)
    logger.info(f"Fetched Reddit thread: {len(full_output)} chars, {len(result['comments'])} comments")
    return full_output
