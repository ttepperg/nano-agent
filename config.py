""" Agent configuration """

import os

# RUNTIME DIAGNOSTICS AND AGENT TRACING
DEBUG_ON = True
TRACE_ON = True


# SERVER DETAILS
# Select via environmental variable (fallback: 'mock')
# export LLM_BACKEND='mock' | 'gemini'

LLM_BACKENDS = {
    "mock": {
        "base_url": "http://localhost:8000",
        "api_key": "fake-key",
        "model": "mock-model",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "api_key": os.environ.get("GEMINI_API_KEY"),
        "model": "gemini-3.6-flash",
    },
}

LLM_BACKEND = os.getenv("LLM_BACKEND", "mock")
LLM_CONFIG = LLM_BACKENDS[LLM_BACKEND]
