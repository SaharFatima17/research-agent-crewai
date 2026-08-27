"""
CrewAI Agent definitions.

Each agent has a narrow, single-purpose role -- this is the CrewAI
equivalent of each LLM-driven node in the LangGraph version (decompose,
draft, review, finalize). `allow_delegation=False` keeps every agent
doing only its own job instead of handing work to other agents, which
matters here since the flow (not the agents) controls the overall order
and the review-loop logic.

Agents are built lazily (on first use, then cached) rather than at
import time, so a missing GEMINI_API_KEY doesn't crash the whole app on
startup -- it only surfaces when a research run actually starts.
"""

from crewai import Agent

from llm import get_llm

_cache = {}


def get_planner_agent() -> Agent:
    if "planner" not in _cache:
        _cache["planner"] = Agent(
            role="Research planner",
            goal=(
                "Break a user's question into 3 to 5 concrete, independently "
                "searchable research steps."
            ),
            backstory=(
                "You are a meticulous research planner who scopes work into "
                "clear, searchable pieces before anyone starts digging."
            ),
            llm=get_llm(),
            allow_delegation=False,
            verbose=False,
        )
    return _cache["planner"]


def get_writer_agent() -> Agent:
    if "writer" not in _cache:
        _cache["writer"] = Agent(
            role="Research analyst",
            goal=(
                "Write clear, well-organized report sections using only the "
                "evidence given, never inventing facts."
            ),
            backstory=(
                "You are a careful analyst who cites evidence honestly and "
                "flags it plainly when the evidence on a point is thin."
            ),
            llm=get_llm(),
            allow_delegation=False,
            verbose=False,
        )
    return _cache["writer"]


def get_reviewer_agent() -> Agent:
    if "reviewer" not in _cache:
        _cache["reviewer"] = Agent(
            role="Strict editor",
            goal="Find gaps in a draft report and decide whether more research is needed.",
            backstory=(
                "You are a demanding editor who only signs off on a report "
                "once it genuinely answers the question that was asked."
            ),
            llm=get_llm(),
            allow_delegation=False,
            verbose=False,
        )
    return _cache["reviewer"]


def get_summarizer_agent() -> Agent:
    if "summarizer" not in _cache:
        _cache["summarizer"] = Agent(
            role="Executive summarizer",
            goal="Write a short, direct executive summary of a finished report.",
            backstory="You write summaries busy stakeholders can read in ten seconds.",
            llm=get_llm(),
            allow_delegation=False,
            verbose=False,
        )
    return _cache["summarizer"]
