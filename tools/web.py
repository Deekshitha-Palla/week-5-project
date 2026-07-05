"""
Web search and fetch tools — carry forward from Week 2.

Implement or copy from your week_2/project/:
  - web_search(query) — Serper
  - web_fetch(url) — requests + trafilatura/markdownify
"""

# TODO: copy from Week 2 project
import os
import json
import requests
import trafilatura
from urllib.parse import urlparse


TOOLS=[
    {
        "type":"function",
        "function":{
            "name":"web_search",
            "description":(
                "Search the web for current information. Use this when the user asks "
                "about recent events, specific facts, or anything you are uncertain about. "
                "Returns a list of search results with titles, URLs, and snippets."
            ),
            "parameters":{
                "type":"object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query. Be specific and targeted.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type":"function",
        "function":{
            "name":"smart_fetch",
            "description": (
                "Fetch and read the full content of a web page. "
                "Checks for llms.txt first for efficient site navigation, "
                "then falls back to full page fetch. Use this after web_search "
                "to read a specific result in detail."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL to fetch, including https://"
                    },
                },
                "required": ["url"]
            },
        },
    },
]

def web_search(query:str,num_res:int=5) -> str:
    response=requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY":os.environ["SERPER_KEY"],"Content-Type":"application/json"},
        json={
            "q":query,
            "num":num_res,
        },
        timeout=10,
    )
    response.raise_for_status()
    data=response.json()
    results=[]
    for i in data.get("organic",[]):
        results.append({
            "title":i.get("title",""),
            "link":i.get("link",""),
            "snippet":i.get("snippet",""),
        })
    return results

def web_fetch(url:str) -> str:
    response=requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"},
        allow_redirects=True,
        timeout=10,
    )
    response.raise_for_status()
    return response.text

def fetch_clean(url: str) -> str:
    html = web_fetch(url)
    text = trafilatura.extract(html, include_comments=False, include_tables=True)
    return text or ""

MAX_CHARS = 8000
def fetch_for_agent(url: str) -> str:
    content = fetch_clean(url)
    if len(content) > MAX_CHARS:
        content = content[:MAX_CHARS] + "\n\n[...truncated]"
    return content

def smart_fetch(url: str) -> str:
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

    try:
        resp = requests.get(f"{base}/llms.txt", timeout=5)
        if resp.status_code == 200:
            return f"[llms.txt found]\n\n{resp.text}\n\n---\nOriginal URL: {url}"
    except Exception:
        pass

    return fetch_for_agent(url)

TOOL_REGISTRY={
    "web_search":web_search,
    "smart_fetch":smart_fetch,
}