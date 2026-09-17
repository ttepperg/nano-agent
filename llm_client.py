""" LLM Client """
import requests
# from config import LLM_CONFIG_MOCK as LLM_CONFIG
from config import LLM_CONFIG_GEMINI as LLM_CONFIG
from utils import debug

def ask_llm(conversation, tool_defs):
    """Post the current conversation to the LLM and retrieve its answer."""

    response = requests.post(
        # Where to post
        f"{LLM_CONFIG['base_url']}/chat/completions",
        # Metadata (credentials, type)
        headers={
            "Authorization": f"Bearer {LLM_CONFIG['api_key']}",
            "Content-Type": "application/json"
        },
        # What to post (data)
        json={
            "model": LLM_CONFIG['model'],
            "messages": conversation,
            "tools": tool_defs,
        }
    ) # request.post

    # Bytes to text
    # request() provides shortcut for: json.loads(await response.string())
    # This converst HTTP bytes -> text -> JSON -> Python object
    response_json = response.json()
    debug("response_json\n", response_json)
    return response_json["choices"][0]["message"]
