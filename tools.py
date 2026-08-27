"""
Web search tool used inside the search step.

Uses DuckDuckGo Search (via the `ddgs` package) by default because it
needs no API key and no billing account, which keeps the project inside
a free/low-cost budget. If a TAVILY_API_KEY is present in the environment,
Tavily is used instead (higher quality results, small free tier).

Both paths are wrapped so a failed call never raises out of the flow --
it returns an empty list and the caller logs + records the failure.

This function is deterministic and framework-agnostic, so it's called
directly from the flow rather than being routed through a CrewAI agent --
that keeps the structured {title, url, snippet} results reliable for
storing in the flow state (an agent's free-text summary of search results
would be lossy to parse back into structured fields).
"""

import os
from typing import List, TypedDict


class RawResult(TypedDict):
    title: str
    url: str
    snippet: str


def _search_tavily(query: str, max_results: int) -> List[RawResult]:
    from tavily import TavilyClient

    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    resp = client.search(query=query, max_results=max_results)
    return [
        RawResult(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=r.get("content", ""),
        )
        for r in resp.get("results", [])
    ]


def _search_duckduckgo(query: str, max_results: int) -> List[RawResult]:
    from ddgs import DDGS

    out: List[RawResult] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            out.append(
                RawResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                )
            )
    return out


def web_search(query: str, max_results: int = 4) -> List[RawResult]:
    """
    Run a web search and return a list of {title, url, snippet}.
    Never raises -- returns [] on any failure so the flow can keep going.
    """
    try:
        if os.environ.get("TAVILY_API_KEY"):
            return _search_tavily(query, max_results)
        return _search_duckduckgo(query, max_results)
    except Exception:
        return []
