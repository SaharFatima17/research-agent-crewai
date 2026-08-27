"""
CrewAI Task builders.

Tasks in CrewAI carry the actual instructions for a given run -- unlike
Agents (which are reusable roles), a Task is built fresh each time with
the real question/evidence/draft plugged in, then handed to a one-task
Crew to execute. This mirrors how the LangGraph version built a fresh
prompt string per node call.
"""

from crewai import Task

from agents import get_planner_agent, get_writer_agent, get_reviewer_agent, get_summarizer_agent


def build_decompose_task(question: str) -> Task:
    return Task(
        description=(
            f"Break this question into 3 to 5 concrete, independently "
            f"searchable research steps.\n\nQuestion: {question}\n\n"
            "Reply with ONLY a numbered list, one step per line, no preamble."
        ),
        expected_output="A numbered list of 3 to 5 short research steps.",
        agent=get_planner_agent(),
    )


def build_draft_task(question: str, evidence: str) -> Task:
    return Task(
        description=(
            f"Question: {question}\n\nEvidence:\n{evidence}\n\n"
            "Using ONLY the evidence above, write a clear, well-organized "
            "report section answering the question. Refer to sources "
            "loosely inline where useful. If evidence is thin on a point, "
            "say so plainly rather than inventing facts."
        ),
        expected_output="A well-organized report section in markdown.",
        agent=get_writer_agent(),
    )


def build_review_task(question: str, draft: str) -> Task:
    return Task(
        description=(
            f"Question: {question}\n\nDraft:\n{draft}\n\n"
            "Decide whether the draft fully answers the question. Reply "
            'with ONLY valid JSON: {"missing_info": true|false, "notes": '
            '"short critique", "missing_topics": ["topic1", "topic2"]}. '
            "missing_topics should be empty if missing_info is false, and "
            "should list at most 3 concrete follow-up search topics "
            "otherwise."
        ),
        expected_output="A single JSON object, nothing else.",
        agent=get_reviewer_agent(),
    )


def build_summary_task(question: str, report: str) -> Task:
    return Task(
        description=(
            f"Question: {question}\n\nReport:\n{report}\n\n"
            "Write a 2 to 4 sentence executive summary answering the "
            "question directly."
        ),
        expected_output="A 2 to 4 sentence executive summary, nothing else.",
        agent=get_summarizer_agent(),
    )
