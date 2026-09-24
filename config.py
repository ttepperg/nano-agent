""" Agent configuration """

import os

# RUNTIME DIAGNOSTICS AND AGENT TRACING
DEBUG_ON = True
TRACE_ON = True


# SERVER DETAILS
# Select via environmental variable (fallback: 'mock')
# export LLM_BACKEND='mock' | 'gemini'

MOCK_PORT = 8001

LLM_BACKENDS = {
    "mock": {
        "base_url": f"http://localhost:{MOCK_PORT}",
        "api_key": "fake-key",
        "model": "mock-model",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "api_key": os.environ.get("GEMINI_API_KEY"),
        "model": "gemini-3.6-flash",
    },
    "gpt": {
        "base_url": "https://api.openai.com/v1",
        "api_key": os.environ["OPENAI_API_KEY"],
        "model": "gpt-5.6-luna",
        "reasoning_effort": "none",
        "parallel_tool_calls": False,
    },
}

LLM_BACKEND = os.getenv("LLM_BACKEND", "mock")
LLM_CONFIG = LLM_BACKENDS[LLM_BACKEND]
