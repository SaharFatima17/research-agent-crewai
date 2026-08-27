# Research Agent — CrewAI, all-in-one Streamlit app

Backend and frontend combined into a single Streamlit app: no separate
FastAPI server, no HTTP/SSE calls. The CrewAI Flow runs directly inside
the Streamlit process and streams progress straight into the UI.

This exists because the split backend (FastAPI on a separate host) kept
hitting platform limits (Vercel's 500MB serverless bundle cap, Render's
new card-verification requirement on the free tier). Combining everything
into one Streamlit Community Cloud deployment sidesteps both.

## Files

| File            | Role                                              |
|-----------------|----------------------------------------------------|
| `app.py`        | Streamlit UI - calls `flow.run_research_stream()` directly |
| `theme.py`      | UI styling / rendering helpers                     |
| `state.py`      | Shared Flow state (Pydantic model)                 |
| `tools.py`      | Web search tool                                    |
| `llm.py`        | Lazily-built Gemini LLM instance                   |
| `agents.py`     | CrewAI Agents (lazily built)                       |
| `tasks.py`      | CrewAI Task builders                               |
| `flow.py`       | The CrewAI Flow itself (`decompose -> search -> draft -> review -> finalize`) |
| `logging_config.py` | Safe console+file logging                      |

## Run locally

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in GEMINI_API_KEY
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this folder to its own GitHub repo.
2. share.streamlit.io -> Create app -> point at `app.py`.
3. Advanced settings -> Secrets:
   ```
   GEMINI_API_KEY = "your-key-here"
   ```
4. Deploy. That's it - one app, one URL, no backend to babysit.
