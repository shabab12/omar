"""Miniflux MCP server: lets Claude read and manage your Miniflux feeds."""
import os
import re
from html import unescape

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("MINIFLUX_URL", "").rstrip("/")
API_KEY = os.environ.get("MINIFLUX_API_KEY", "")

mcp = FastMCP("miniflux")


def _client() -> httpx.Client:
    if not BASE_URL or not API_KEY:
        raise RuntimeError("Set MINIFLUX_URL and MINIFLUX_API_KEY environment variables")
    return httpx.Client(
        base_url=f"{BASE_URL}/v1",
        headers={"X-Auth-Token": API_KEY},
        timeout=30,
    )


def _call(method: str, path: str, **kwargs):
    with _client() as c:
        r = c.request(method, path, **kwargs)
        r.raise_for_status()
        return r.json() if r.content else None


def _text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", "", html or "")
    html = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h\d>", "\n", html)
    text = unescape(re.sub(r"<[^>]+>", "", html))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _entry_summary(e: dict) -> dict:
    return {
        "id": e["id"],
        "title": e["title"],
        "feed": e["feed"]["title"],
        "category": e["feed"]["category"]["title"],
        "published_at": e["published_at"],
        "status": e["status"],
        "starred": e["starred"],
        "url": e["url"],
        "reading_time_min": e.get("reading_time"),
    }


@mcp.tool()
def list_entries(
    status: str = "unread",
    limit: int = 20,
    category_id: int | None = None,
    feed_id: int | None = None,
    search: str | None = None,
    starred: bool = False,
) -> list[dict]:
    """List entries (articles), newest first. status: unread | read | removed."""
    params: dict = {
        "status": status,
        "limit": min(limit, 100),
        "order": "published_at",
        "direction": "desc",
    }
    if search:
        params["search"] = search
    if starred:
        params["starred"] = "true"
    if feed_id:
        path = f"/feeds/{feed_id}/entries"
    elif category_id:
        path = f"/categories/{category_id}/entries"
    else:
        path = "/entries"
    data = _call("GET", path, params=params)
    return [_entry_summary(e) for e in data["entries"]]


@mcp.tool()
def get_entry(entry_id: int, max_chars: int = 8000) -> dict:
    """Get one article with its content converted to plain text."""
    e = _call("GET", f"/entries/{entry_id}")
    out = _entry_summary(e)
    out["author"] = e.get("author")
    out["content"] = _text(e["content"])[:max_chars]
    return out


@mcp.tool()
def mark_entries(entry_ids: list[int], status: str = "read") -> str:
    """Set status of entries: read | unread | removed."""
    _call("PUT", "/entries", json={"entry_ids": entry_ids, "status": status})
    return f"Marked {len(entry_ids)} entries as {status}"


@mcp.tool()
def toggle_star(entry_id: int) -> str:
    """Toggle the starred (bookmark) state of an entry."""
    _call("PUT", f"/entries/{entry_id}/bookmark")
    return "Toggled star"


@mcp.tool()
def list_feeds() -> list[dict]:
    """List subscribed feeds with their category and unread counts."""
    feeds = _call("GET", "/feeds")
    counters = _call("GET", "/feeds/counters").get("unreads", {})
    return [
        {
            "id": f["id"],
            "title": f["title"],
            "site_url": f["site_url"],
            "category": f["category"]["title"],
            "unread": counters.get(str(f["id"]), 0),
            "error": f["parsing_error_message"] or None,
        }
        for f in feeds
    ]


@mcp.tool()
def list_categories() -> list[dict]:
    """List categories with unread counts."""
    return [
        {"id": c["id"], "title": c["title"], "unread": c.get("total_unread")}
        for c in _call("GET", "/categories", params={"counts": "true"})
    ]


@mcp.tool()
def add_feed(feed_url: str, category_id: int | None = None) -> dict:
    """Subscribe to a new feed. Uses the first category if none is given."""
    if category_id is None:
        category_id = _call("GET", "/categories")[0]["id"]
    return _call("POST", "/feeds", json={"feed_url": feed_url, "category_id": category_id})


@mcp.tool()
def refresh_all_feeds() -> str:
    """Ask Miniflux to refresh every feed now."""
    _call("PUT", "/feeds/refresh")
    return "Refresh started"


if __name__ == "__main__":
    mcp.run()
