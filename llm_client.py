""" LLM Client """
import requests
from config import LLM_CONFIG
from utils import debug


def validate_llm_response(response):
        # Generic response validation
        # 1 - transport/API validation
        if not response.ok:
            debug(f"LLM API error ({response.status_code}): {response.text}")
            raise RuntimeError(f"LLM API returned HTTP {response.status_code}")
        # 2 - format validation
        try:
            response_json = response.json()
        except ValueError as exc:
            debug(f"Invalid JSON from LLM: {response.text}")
            raise RuntimeError("LLM returned invalid JSON") from exc

        # 3 - schema validation
        if not isinstance(response_json, dict) or "choices" not in response_json:
            debug(f"Unexpected LLM response structure: {response_json}")
            raise RuntimeError("LLM returned unexpected response structure")

        # Chat Completions schema validation
        # Response schema: OpenAI-compatible Chat Completions
        # 4 - choices' structure validation
        choices = response_json["choices"]
        if not isinstance(choices, list) or not choices:
            debug(f"Invalid 'choices' in LLM response: {response_json}")
            raise RuntimeError("LLM returned invalid choices")

        # 5 - messages' structure validation
        message = choices[0].get("message")
        if not isinstance(message, dict):
            debug(f"Invalid 'message' in LLM response: {response_json}")
            raise RuntimeError("LLM returned invalid message")



def ask_llm(conversation, tool_defs):
    """Post the current conversation to the LLM and retrieve its answer."""

    payload = {
        "model": LLM_CONFIG["model"],
        "messages": conversation,
        "tools": tool_defs,
    }
    if "reasoning_effort" in LLM_CONFIG:
        payload["reasoning_effort"] = LLM_CONFIG["reasoning_effort"]

    response = requests.post(
        # Where to post
        f"{LLM_CONFIG['base_url']}/chat/completions",
        # Metadata (credentials, type)
        headers={
            "Authorization": f"Bearer {LLM_CONFIG['api_key']}",
            "Content-Type": "application/json"
        },
        # What to post (data)
        json=payload
    ) # request.post

    # ----- RESPONSE VALIDATION -----
    # Optional but RECOMMENDED
    validate_llm_response(response)

    # Bytes to text
    # request() provides shortcut for: json.loads(await response.string())
    # This converst HTTP bytes -> text -> JSON -> Python object (dict)
    response_json = response.json()
    debug("response_json\n", response_json)

    message = response_json["choices"][0]["message"]
    usage = response_json.get("usage")
    return {
        "message": message,
        "usage": usage,
    }
