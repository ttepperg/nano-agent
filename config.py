""" Agent configuration """

import os

# RUNTIME DIAGNOSTICS AND AGENT TRACING
DEBUG_ON = True
TRACE_ON = True


# SERVER DETAILS

# MOCK SERVER / LLM
LLM_CONFIG_MOCK = {
    "base_url": "http://localhost:8000",
    "api_key": "fake-key", # a real key should not be exposed!
    "model": "mock-model",
}

# Google / Gemini API
LLM_CONFIG_GEMINI = {
    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
    "api_key": os.environ["GEMINI_API_KEY"],
    "model": "gemini-3.6-flash",
}
