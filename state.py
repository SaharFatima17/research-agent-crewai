"""
Shared Flow state for the CrewAI Research Assistant Agent.

CrewAI's Flow class requires its state to be a Pydantic model (or a plain
dict). Using a model here is the direct equivalent of the ResearchState
TypedDict from the LangGraph version -- every flow method reads from and
writes to this one object via `self.state`.
"""

from typing import List
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    step: str      # the research step/question this result belongs to
    query: str     # the actual query sent to the search tool
    title: str
    url: str
    snippet: str


class ResearchState(BaseModel):
    # --- input ---
    question: str = ""

    # --- planning ---
    steps: List[str] = Field(default_factory=list)
    pending_steps: List[str] = Field(default_factory=list)

    # --- search ---
    search_results: List[SearchResult] = Field(default_factory=list)
    failed_searches: List[str] = Field(default_factory=list)

    # --- drafting / review loop ---
    draft: str = ""
    review_notes: str = ""
    missing_info: bool = False
    missing_topics: List[str] = Field(default_factory=list)
    loop_count: int = 0

    # --- output ---
    final_report: str = ""
    summary: str = ""
    sources: List[str] = Field(default_factory=list)

    # --- observability ---
    log: List[str] = Field(default_factory=list)
