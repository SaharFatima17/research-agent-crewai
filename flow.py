"""
CrewAI Flow for the Research Assistant Agent.

This is the direct equivalent of graph.py + nodes.py from the LangGraph
version. Each @start/@listen method is a "node"; the @router method is
the conditional edge; the loop back into search happens because
`route_after_review` can return "loop_back", which re-triggers the same
`search` method (it's decorated with two triggers: the initial one from
`decompose`, and the loop one from the router).

    decompose -> search -> draft -> review --(gaps, loop_count<3)--> search
                                        \\
                                         --(satisfied / cap hit)--> finalize

Flow state (`self.state`) is a ResearchState Pydantic model -- every
method reads from and writes to it directly, same role as the shared
TypedDict state in the LangGraph version.
"""

import json
import re

from crewai import Crew
from crewai.flow.flow import Flow, start, listen, router

from state import ResearchState, SearchResult
from tools import web_search
from tasks import build_decompose_task, build_draft_task, build_review_task, build_summary_task
from logging_config import get_logger

logger = get_logger(__name__)

MAX_LOOPS = 3


class ResearchFlow(Flow[ResearchState]):

    def _log(self, message: str) -> None:
        logger.info(message)
        self.state.log.append(message)

    # ----------------------------------------------------------------
    # 1. Decompose the question into 3-5 research steps
    # ----------------------------------------------------------------
    @start()
    def decompose(self):
        question = self.state.question
        self._log(f"[decompose] breaking down question: {question!r}")

        task = build_decompose_task(question)
        crew = Crew(agents=[task.agent], tasks=[task])
        raw = str(crew.kickoff())

        steps = []
        for line in raw.splitlines():
            cleaned = re.sub(r"^\s*\d+[\.\)]\s*", "", line).strip()
            if cleaned:
                steps.append(cleaned)
        steps = steps[:5] if len(steps) > 5 else steps
        if len(steps) < 3:
            steps = steps + [question] * (3 - len(steps))

        self.state.steps = steps
        self.state.pending_steps = steps
        self._log(f"[decompose] produced {len(steps)} steps: {steps}")
        return steps

    # ----------------------------------------------------------------
    # 2. Search the web for each pending step
    #    Triggered by decompose (first pass) AND by the "loop_back"
    #    route from route_after_review (subsequent passes).
    # ----------------------------------------------------------------
    @listen(decompose)
    @listen("loop_back")
    def search(self):
        pending = self.state.pending_steps
        self._log(f"[search] searching {len(pending)} step(s)")

        for step in pending:
            raw_results = web_search(step, max_results=4)
            if not raw_results:
                self.state.failed_searches.append(step)
                self._log(f"[search] no results / call failed for step: {step!r}")
                continue
            for r in raw_results:
                self.state.search_results.append(
                    SearchResult(step=step, query=step, title=r["title"], url=r["url"], snippet=r["snippet"])
                )
            self._log(f"[search] {len(raw_results)} result(s) for step: {step!r}")

        self.state.pending_steps = []
        return self.state.search_results

    # ----------------------------------------------------------------
    # 3. Draft a report section from everything collected so far
    # ----------------------------------------------------------------
    @listen(search)
    def draft(self):
        question = self.state.question
        results = self.state.search_results
        self._log(f"[draft] drafting from {len(results)} search result(s)")

        evidence = "\n\n".join(
            f"- ({r.step}) {r.title}: {r.snippet} [{r.url}]" for r in results
        ) or "No search evidence was collected."

        task = build_draft_task(question, evidence)
        crew = Crew(agents=[task.agent], tasks=[task])
        self.state.draft = str(crew.kickoff())

        self._log("[draft] draft produced")
        return self.state.draft

    # ----------------------------------------------------------------
    # 4. Review the draft for gaps
    # ----------------------------------------------------------------
    @listen(draft)
    def review(self):
        question = self.state.question
        draft = self.state.draft
        self.state.loop_count += 1
        self._log(f"[review] round {self.state.loop_count}/{MAX_LOOPS}")

        task = build_review_task(question, draft)
        crew = Crew(agents=[task.agent], tasks=[task])
        raw = str(crew.kickoff())

        missing_info = False
        notes = ""
        missing_topics = []
        try:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            parsed = json.loads(match.group(0) if match else raw)
            missing_info = bool(parsed.get("missing_info", False))
            notes = str(parsed.get("notes", ""))
            missing_topics = list(parsed.get("missing_topics", []))[:3]
        except Exception:
            self._log("[review] could not parse reviewer JSON; assuming no gaps")

        # Loop cap: stop looping after MAX_LOOPS rounds even if gaps remain
        if self.state.loop_count >= MAX_LOOPS:
            if missing_info:
                self._log(f"[review] gaps remain but loop cap ({MAX_LOOPS}) reached; stopping")
            missing_info = False

        self.state.review_notes = notes
        self.state.missing_info = missing_info
        self.state.missing_topics = missing_topics
        if missing_info:
            self.state.pending_steps = missing_topics
            self.state.steps = self.state.steps + missing_topics

        self._log(f"[review] missing_info={missing_info} notes={notes!r}")
        return missing_info

    # ----------------------------------------------------------------
    # Conditional edge: loop back to search, or move on to finalize
    # ----------------------------------------------------------------
    @router(review)
    def route_after_review(self):
        return "loop_back" if self.state.missing_info else "finalize"

    # ----------------------------------------------------------------
    # 5. Finalize: summary + source list
    # ----------------------------------------------------------------
    @listen("finalize")
    def finalize_step(self):
        question = self.state.question
        draft = self.state.draft
        self._log("[finalize] producing final report")

        task = build_summary_task(question, draft)
        crew = Crew(agents=[task.agent], tasks=[task])
        self.state.summary = str(crew.kickoff())

        sources = sorted({r.url for r in self.state.search_results if r.url})
        self.state.sources = sources

        self.state.final_report = (
            f"## Summary\n{self.state.summary}\n\n"
            f"## Report\n{draft}\n\n"
            f"## Sources\n" + "\n".join(f"- {s}" for s in sources)
        )

        self._log(f"[finalize] done, {len(sources)} source(s)")
        return self.state.final_report


def run_research(question: str) -> dict:
    """Convenience runner for non-streaming use (e.g. a script or test)."""
    flow = ResearchFlow()
    flow.state.question = question
    flow.kickoff()
    return flow.state.model_dump()


def run_research_stream(question: str):
    """
    Generator used by the streaming API endpoint. It drives the same flow
    instance's methods directly, one at a time, yielding
    (step_name, state_dict) after each -- this is what gives the frontend
    live per-step progress, the same role graph_app.stream() played in the
    LangGraph version.
    """
    flow = ResearchFlow()
    flow.state.question = question

    flow.decompose()
    yield "decompose", flow.state.model_dump()

    round_num = 0
    while True:
        flow.search()
        yield "search", flow.state.model_dump()

        flow.draft()
        yield "draft", flow.state.model_dump()

        flow.review()
        yield "review", flow.state.model_dump()

        round_num += 1
        route = flow.route_after_review()
        if route == "finalize" or round_num >= MAX_LOOPS:
            break

    flow.finalize_step()
    yield "finalize", flow.state.model_dump()