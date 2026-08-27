"""
Shared LLM configuration for all CrewAI agents in this project.

CrewAI's own `LLM` class (not a raw provider SDK client) is what Agents
expect, so every agent in agents.py imports `gemini_llm` from here rather
than each constructing its own.
"""

import os

from crewai import LLM

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

_llm_instance = None


def get_llm() -> LLM:
    """
    Lazily create the shared LLM instance on first use. Deferring this
    (instead of building it at import time) means a missing API key
    surfaces as a clear error when a research run actually starts,
    rather than crashing the whole app / import chain on startup.
    """
    global _llm_instance
    if _llm_instance is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Get a free key at "
                "https://aistudio.google.com/apikey and add it to your "
                "environment or .env file before running the agent."
            )
        _llm_instance = LLM(model=f"gemini/{DEFAULT_MODEL}", api_key=api_key)
    return _llm_instance
