# Research Agent frontend — CrewAI, all-in-one Streamlit app.
# Runs the CrewAI flow directly inside this process (no separate backend
# server, no HTTP calls) so the whole thing deploys as a single Streamlit
# Community Cloud app.
"""Research Agent frontend + CrewAI flow, combined into one Streamlit app."""
import os
import time
import datetime
import streamlit as st
from dotenv import load_dotenv
from theme import base_style, masthead, hero, render_rail, render_log, render_case_file, NODE_ORDER
from flow import run_research_stream

load_dotenv()

st.set_page_config(page_title="Research Agent — CrewAI", page_icon="🤝", layout="wide", initial_sidebar_state="expanded")
st.markdown(base_style(), unsafe_allow_html=True)
if "ref" not in st.session_state:
    st.session_state["ref"] = datetime.datetime.now().strftime("%y%m%d-%H%M%S")

st.markdown(masthead(st.session_state["ref"]), unsafe_allow_html=True)
st.markdown(hero(), unsafe_allow_html=True)


# Sidebar is presentation only.
with st.sidebar:
    st.markdown("### Research Agent")
    st.caption("Live workflow monitor")
    st.divider()
    st.markdown("**Engine**")
    if os.environ.get("GEMINI_API_KEY"):
        st.success("CrewAI engine ready")
    else:
        st.error("GEMINI_API_KEY not set")
        st.caption("Add it in Settings \u2192 Secrets, then reload.")
    st.divider()
    st.markdown("**Pipeline**")
    for label in ["Plan", "Search", "Draft", "Review", "Finalize"]:
        st.markdown(f"<span class='ra-chip'>{label}</span>", unsafe_allow_html=True)
    st.caption("CrewAI Agents + a Flow run directly in this app - no separate backend.")

# Main workspace
left, right = st.columns([1.65, 1], gap="large")
node_status = {n: "pending" for n in NODE_ORDER}
rail_placeholder = right.empty()
rail_placeholder.markdown(render_rail(node_status), unsafe_allow_html=True)

with left:
    st.markdown('<div class="ra-section">Research question</div>', unsafe_allow_html=True)
    question = st.text_area(
        "Research question",
        placeholder="Example: What are the main approaches to carbon capture, and how do their costs and scalability compare?",
        height=125,
        label_visibility="collapsed",
    )
    run_clicked = st.button("✦  Start research", type="primary")
    st.markdown('<div style="height:.5rem"></div>', unsafe_allow_html=True)
    st.markdown('<div class="ra-section">Live activity</div>', unsafe_allow_html=True)
    log_placeholder = st.empty()
    log_placeholder.markdown(render_log([]), unsafe_allow_html=True)
    result_placeholder = st.empty()

if run_clicked:
    if not question.strip():
        with left:
            st.warning("Enter a research question first.", icon="✎")
        st.stop()

    if not os.environ.get("GEMINI_API_KEY"):
        with left:
            st.error("GEMINI_API_KEY is not set. Add it in Settings \u2192 Secrets, then reload the app.")
        st.stop()

    extra_search_rounds = 0
    search_visits = 0
    all_log_lines = []
    final_state = None
    start = time.time()

    try:
        for step_name, node_state in run_research_stream(question.strip()):
            if step_name not in NODE_ORDER:
                continue
            idx = NODE_ORDER.index(step_name)
            for earlier in NODE_ORDER[:idx]:
                if node_status.get(earlier) != "flag": node_status[earlier] = "done"
            node_status[step_name] = "active"
            if step_name == "search":
                search_visits += 1
                extra_search_rounds = min(max(search_visits - 1, 0), 2)
            rail_placeholder.markdown(render_rail(node_status, extra_search_rounds), unsafe_allow_html=True)
            all_log_lines = node_state.get("log", all_log_lines)
            log_placeholder.markdown(render_log(all_log_lines), unsafe_allow_html=True)
            node_status[step_name] = "flag" if step_name == "search" and node_state.get("failed_searches") else "done"
            rail_placeholder.markdown(render_rail(node_status, extra_search_rounds), unsafe_allow_html=True)
            final_state = node_state

        for n in NODE_ORDER:
            if node_status.get(n) != "flag": node_status[n] = "done"
        rail_placeholder.markdown(render_rail(node_status, extra_search_rounds), unsafe_allow_html=True)
        elapsed = time.time() - start

    except Exception as e:
        with left:
            st.error(f"The research run failed: {e}")
        st.stop()

    with left:
        if final_state and final_state.get("final_report"):
            sources = final_state.get("sources", [])
            c1, c2, c3 = st.columns(3)
            c1.metric("Sources", len(sources))
            c2.metric("Steps", len(final_state.get("steps", [])))
            c3.metric("Time", f"{elapsed:.1f}s")
            result_placeholder.markdown(
                render_case_file(
                    ref=st.session_state["ref"],
                    summary=final_state.get("summary", ""),
                    report_markdown=final_state.get("draft", ""),
                    sources=sources,
                    failed=final_state.get("failed_searches") or [],
                ), unsafe_allow_html=True,
            )
        else:
            st.warning("The graph finished but produced no report. Check the activity log above.")
