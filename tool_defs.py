""" Schema of tools available to the LLM"""

# TASK TOOLS

ADD_DEF = {
    "type": "function",
    "function": {
        "name": "add",
        "description": "Add two numbers",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"}
            }
        }
    }
}

UPPER_DEF = {
    "type": "function",
    "function": {
        "name": "upper",
        "description": "Uppercase text",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            }
        }
    }
}

# AGENT SUPPORTING INFRASTRUCTURE (DO NOT CHANGE)
REMEMBER_DEF = {
    "type": "function",
    "function": {
        "name": "remember",
        "description": "Save to long-term memory",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "value": {"type": "string"}
            }
        }
    }
}

TOOL_DEFS = [
    ADD_DEF,
    UPPER_DEF,
    REMEMBER_DEF,
]
