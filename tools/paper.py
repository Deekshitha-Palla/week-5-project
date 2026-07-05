"""
Paper search and read tools — Hugging Face Papers API (arXiv index).

Implement:
  - paper_search(query, limit) -> {papers: [{arxiv_id, title, abstract, url}, ...]}
  - read_paper(arxiv_id) -> {title, abstract, content, url, ...}

API docs: week_3/3_paper_tools.md
"""
import os
import requests
import json
from tools.web import smart_fetch


HF_API = "https://huggingface.co/api/papers"
BASE_URL="https://huggingface.co"


def paper_search(query: str, limit: int = 5) -> dict:
    response = requests.get(
        f"{HF_API}/search",
        params={"q": query},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()  # this is a LIST, not a dict
    
    results = []
    for item in data[:limit]:
        paper = item["paper"]
        results.append({
            "id": paper.get("id", ""),
            "title": paper.get("title", ""),
            "abstract": paper.get("summary", "")[:200],
            "authors": [a.get("name", "") for a in paper.get("authors", [])],
        })
    return {"content": results}


def read_paper(arxiv_id: str) -> dict:
    # 1. fetch structured metadata
    meta_response = requests.get(f"{BASE_URL}/api/papers/{arxiv_id}", timeout=10)
    if meta_response.status_code == 404:
        # not indexed on HF — fall back to web_search + web_fetch on arxiv.org
        fallback_url = f"https://arxiv.org/abs/{arxiv_id}"
        # TODO: call your web_fetch / smart_fetch tool on fallback_url
        content = smart_fetch(fallback_url)
        return {
            "title": "",
            "abstract": "",
            "content": content,
            "url": fallback_url,
        }
    meta_response.raise_for_status()
    meta = meta_response.json()  

    # 2. fetch markdown content (separate endpoint, no /api/)
    md_response = requests.get(f"{BASE_URL}/papers/{arxiv_id}.md", timeout=10)
    content = md_response.text if md_response.status_code == 200 else meta.get("summary", "")

    return {
        "title": meta.get("title", ""),
        "abstract": meta.get("summary", ""),   # which key holds the abstract, per the docs?
        "content": content,
        "url": f"https://arxiv.org/abs/{arxiv_id}",
    }

TOOLS=[
    {
        "type":"function",
        "function":{
            "name":"paper_search",
            "description":
                "Search the academic papers for current information. Use this when the user asks "
                "Returns a list of search results with ids,titles, abstracts and authors.",
            "parameters":{
                "type":"object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The hybrid search query. Be specific and targeted.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of papers to return. Defaults to 5.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type":"function",
        "function":{
            "name":"read_paper",
            "description": (
                "Fetches arXiv paper content + metadata by ID, falls back to web if not indexed (error:404)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "arxiv_id": {
                        "type": "string",
                        "description": "The arXiv paper ID to fetch, e.g. '2305.03653'. Get this from the id field returned by paper_search."
                    },
                },
                "required": ["arxiv_id"],
            },
        },
    },
]

TOOL_REGISTRY={
    "paper_search":paper_search,
    "read_paper":read_paper,
}
# if __name__ == "__main__":
#     result = paper_search("attention mechanism", limit=3)
#     print(result)
#     print()
#     first_id = result["content"][0]["id"]
#     print(read_paper(first_id))