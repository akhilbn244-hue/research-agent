"""
tools.py  -  THE AGENT'S TOOLS
==============================

Gemini can't browse the internet by itself. Instead we give it a MENU of tools,
each with a name and a description, like buttons on a remote control.
Gemini reads the menu and replies "please press web_search with this query".
OUR code presses the button, then hands the result back to Gemini.

That hand-off is called TOOL CALLING (or function calling). The descriptions
below matter a lot: they are the only thing Gemini knows about each tool,
so a clear description is what makes the agent use a tool well.

The three tools:
  web_search    - search the web (DuckDuckGo, free, no key needed)
  read_webpage  - open one web page and return its readable text
  save_note     - write down a finding, with the link it came from
"""

import ipaddress
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

MAX_PAGE_CHARS = 4000        # only the first part of each page goes back to Gemini (saves tokens)
HEADERS = {"User-Agent": "Mozilla/5.0 (research-agent portfolio project)"}


# ---------------------------------------------------------------- the menu Gemini reads
TOOL_MENU = [
    {
        "name": "web_search",
        "description": "Search the web. Returns up to 5 results, each with a title, link and short snippet. "
                       "Use specific queries, e.g. 'bespoke bridal tailoring Kochi' rather than 'clothes'.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "What to search for."}}, "required": ["query"]},
    },
    {
        "name": "read_webpage",
        "description": "Open one web page and return its readable text (first 4,000 characters). "
                       "Use it on promising links from web_search to check facts before saving them.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string", "description": "The full link, starting with http:// or https://"}}, "required": ["url"]},
    },
    {
        "name": "save_note",
        "description": "Save one finding for the final report. Every note must include the link it came from. "
                       "Save only facts you actually read in a search result or page.",
        "parameters": {"type": "object", "properties": {
            "competitor": {"type": "string", "description": "Which business the finding is about."},
            "finding": {"type": "string", "description": "The fact, in one or two sentences."},
            "source_url": {"type": "string", "description": "The link where you found it."}},
            "required": ["competitor", "finding", "source_url"]},
    },
]


# ---------------------------------------------------------------- the tools themselves
def web_search(query):
    """Search DuckDuckGo and return a short list of results."""
    from ddgs import DDGS                              # imported here so the app still opens if it's missing
    try:
        results = DDGS().text(query, max_results=5)
    except Exception as problem:                       # no internet, search blocked for a moment, etc.
        return {"error": f"Search failed: {problem}. Try a different query."}
    return {"results": [{"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
                        for r in results]}


def is_public_web_address(url):
    """Only allow normal websites - never addresses inside your own computer or home network."""
    parts = urlparse(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return False
    try:
        address = ipaddress.ip_address(socket.gethostbyname(parts.hostname))
    except (socket.gaierror, ValueError):
        return False
    return not (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved)


def read_webpage(url):
    """Download a page and return its visible text, without menus, scripts and styling."""
    if not is_public_web_address(url):
        return {"error": "That isn't a public web address, so it wasn't opened."}
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as problem:
        return {"error": f"Couldn't open the page: {problem}. Try another link."}
    if "text/html" not in response.headers.get("Content-Type", "text/html"):
        return {"error": "That link isn't a web page (it may be a PDF or image)."}

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    title = soup.title.get_text(strip=True) if soup.title else url
    return {"title": title, "url": url, "text": text[:MAX_PAGE_CHARS], "truncated": len(text) > MAX_PAGE_CHARS}


def run_tool(name, args, notes):
    """
    Press the button Gemini asked for. `notes` is the shared list save_note adds to.
    Always returns a dictionary - errors included - so the agent can read what happened and adapt.
    """
    try:
        if name == "web_search":
            return web_search(str(args.get("query", "")))
        if name == "read_webpage":
            return read_webpage(str(args.get("url", "")))
        if name == "save_note":
            note = {k: str(args.get(k, "")).strip() for k in ("competitor", "finding", "source_url")}
            if not note["source_url"].startswith("http"):
                return {"error": "Notes need a source link starting with http. Note not saved."}
            notes.append(note)
            return {"saved": True, "notes_so_far": len(notes)}
        return {"error": f"There is no tool called {name}."}
    except Exception as problem:                       # a tool must never crash the whole agent
        return {"error": f"The {name} tool failed: {problem}"}
