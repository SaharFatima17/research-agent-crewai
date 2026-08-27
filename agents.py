"""
CrewAI Agent definitions.

Each agent has a narrow, single-purpose role -- this is the CrewAI
equivalent of each LLM-driven node in the LangGraph version (decompose,
draft, review, finalize). `allow_delegation=False` keeps every agent
doing only its own job instead of handing work to other agents, which
matters here since the flow (not the agents) controls the overall order
and the review-loop logic.

Agents are built fresh on every call rather than cached at module level.
They used to be cached in a module-level dict, but on Streamlit (a
long-lived, multi-session process) that meant every session shared the
same Agent object -- if two runs (two tabs, a double-click, or a rerun
mid-stream) touched the same cached Agent at once, CrewAI's internal
executor raised "Executor is already running. Cannot invoke the same
executor instance concurrently." Building a fresh Agent per call avoids
that entirely; the LLM instance itself is still cached in llm.py since
it's stateless per-call.
"""

from crewai import Agent

from llm import get_llm


def get_planner_agent() -> Agent:
    return Agent(
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


def get_writer_agent() -> Agent:
    return Agent(
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


def get_reviewer_agent() -> Agent:
    return Agent(
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


def get_summarizer_agent() -> Agent:
    return Agent(
        role="Executive summarizer",
        goal="Write a short, direct executive summary of a finished report.",
        backstory="You write summaries busy stakeholders can read in ten seconds.",
        llm=get_llm(),
        allow_delegation=False,
        verbose=False,
    )