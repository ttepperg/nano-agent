"""

About
    A mock Large Language Model (LLM) application programming interface (API)

Called by

    mock_server.py

"""
import json
import random
from utils import extract_keyval

# response template
response = {
    "choices": [
        { "message": {"content": None} }
    ]
}

# Mock responses
random_answer = [
    "Paris",
    "Yes", "No", "Maybe",
    "password", "secret",
]

# Mock memories
random_memory = \
    ["Bread", "Sun", "Walking", "Never", "Here", "Radical"]

# Mock tasks
task_choices = ["Add 1 and 5", "Upper case text", "Do something else"]

def set_tools_openai_api(request, tool_index, args_dict, id):
    """ Response schema: OpenAI-compatible Chat Completions """
    select_tool = request["tools"][tool_index]
    select_tool["function"]["arguments"] = json.dumps(args_dict)
    select_tool["id"] = str(id)
    return select_tool

# ------ MOCK LLM ------
def llm_api(request):
    """
        LLM emulator.
        Uses an ad-hoc, deterministic logic to return responses.
    """
    select_tools = []
    for roles in request["messages"]:
        if roles["role"] == "user":
            user_msg = roles["content"]
    for umsg in user_msg.split('then'): # emulates multi-task request
        if "add" in umsg.lower():
            args = {"a": 5, "b": 1}
            select_tool = \
                set_tools_openai_api(request,0, args,'1234')
            select_tools.append(select_tool)
            llm_response = {"tool_calls": select_tools}
        elif "upper" in umsg.lower():
            args = {"text": "abcdef"}
            select_tool = \
                set_tools_openai_api(request,1,args,'5678')
            select_tools.append(select_tool)
            llm_response = {"tool_calls": select_tools}
        elif any(s in umsg.lower() for s in ['age', 'name', 'birthplace']):
            key, val = extract_keyval(umsg)
            args = {"key": key, "value": val}
            select_tool = \
                set_tools_openai_api(request, 2, args, '8910')
            select_tools.append(select_tool)
            llm_response = {"tool_calls": select_tools}
        elif 'do ' in umsg.lower():
            task = random.choice(task_choices)
            args =  {"task": task}
            select_tool = \
                set_tools_openai_api(request, 3, args, '1112')
            select_tools.append(select_tool)
            llm_response = {"tool_calls": select_tools}
        else:
            word = random.choice(random_answer)
            llm_response = {"content": word}

    response["choices"][0]["message"] = {"role": "assistant", **llm_response}
    response["usage"] =  {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 30, # includes 'thinking' tokens
        }


    return response
