"""

About
    The smallest possible agent.

    Adapted from:

            https://tinyagents.dev/

Run

    First, launch the mock server (and leave running):

        $> py312 mock_llm.py

    Then, in a different terminal,

        $> py312 nano_agent.py

Notes
    The HTTP traffic is printed in the terminal running the server,
    the LLM response is printed in the terminal running the agent.

"""
import json
import requests
import tools
from tool_defs import TOOL_DEFS
from guardrails import INPUT_RULES, OUTPUT_RULES, check_gate
from utils import trace
# from config import LLM_CONFIG_MOCK as LLM_CONFIG
from config import LLM_CONFIG_GEMINI as LLM_CONFIG
from utils import debug


# SYSTEM PROMPT
SYSTEM = "You have tools. add(a,b) to add two numbers. upper(text) to capitalize text. remember() to save facts. schedule() to add next steps. Use them when needed. Be concise."

# MEMORY
memory_dict = {}


# CONVERSATION AND STATE
conversation = [
    {"role": "system", "content": SYSTEM},
]

# messages and memory updated dynamically
state = {
    "turns": [],
    "messages": conversation,
    "memory": memory_dict
}

# TASKS QUEUE
task_queue = []

# TOOL REGISTRY
TOOL_REGISTRY = {
    "add": tools.add,
    "upper": tools.upper,
    "remember": tools.make_remember(memory_dict),
    "schedule": tools.make_schedule(task_queue),
}

# ------ LLM CLIENT ------
def ask_llm(message):
    """Post the current conversation to the LLM and retrieve its answer."""

    trace("llm_call", f"Asking: {message}")

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
            "tools": TOOL_DEFS,
        }
    ) # request.post

    # Bytes to text
    # request() provides shortcut for: json.loads(await response.string())
    # This converst HTTP bytes -> text -> JSON -> Python object
    response_json = response.json()
    debug("response_json\n", response_json)
    return response_json["choices"][0]["message"]


# ------ ORCHESTRATOR ------
def agent(task, max_iter = 5):
    """ Orchestrator """

    # ----- INPUT GATE -----
    ok, reason = check_gate(task, INPUT_RULES, 'INPUT')
    if not ok: return f"BLOCKED: {reason}"

    # ----- AGENT LOOP -----
    trace("agent_start", f"Input: {task}")

    mem_str = json.dumps(memory_dict) if memory_dict else "empty"
    system_message = \
        {"role": "system", "content": SYSTEM + f" Memory: {mem_str}"}
    conversation[0] = system_message # replace

    conversation.append({"role": "user", "content": task})

    # record state
    turn_id = len(state["turns"])
    state["turns"].append({"id": turn_id+1, "iterations": 0})

    for iter in range(max_iter):
        state["turns"][turn_id]["iterations"] = iter+1
        trace("llm_call", f"Turn: {turn_id}  Iterations: {iter+1}")
        llm_response = ask_llm(task)
        if not llm_response.get("tool_calls"): # not tasks left -> final answer
            final_answer = llm_response.get('content', '')
            # ----- OUTPUT GATE -----
            ok, reason = check_gate(final_answer, OUTPUT_RULES, 'OUTPUT')
            if not ok: return f"REDACTED: {reason}"
            conversation.append({"role": "assistant", "content": final_answer})
            trace("agent_end",
                f"Done in {state["turns"][turn_id]["iterations"]} iterations")
            return final_answer
        # add LLM message to conversation
        conversation.append(llm_response)
        # loop over tool calls
        for tc in llm_response["tool_calls"]:
            fcn = tc["function"]
            name = fcn["name"]
            args = json.loads(fcn["arguments"]) # str -> dict
            result = TOOL_REGISTRY[name](**args)
            trace("tool_result", f"{name}({args}) -> {result}")
            conversation.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": str(result)
            })

    return f"Max iteration reached: {max_iter}"


# ------ BFS SCHEDULER (Breadth-First Search) ------
def run_queue(initial_tasks, max_tasks=5):
    task_queue.clear()
    task_queue.extend(initial_tasks)
    results = []
    processed = 0
    while task_queue and processed < max_tasks:
        task = task_queue.pop(0)
        processed += 1
        trace("agent_start", f"[{processed}/{max_tasks}] {task}")
        result = agent(task)
        results.append({"task": task, "result": result})
        print("task", task, "result", result)
    if task_queue:
        trace("policy_block", f"BUDGET: {len(task_queue)} tasks remaining")
    return results


# ------ MAIN ------
if __name__ == "__main__":

    import pprint

    # DO NOT DELETE: The first ever successful call
    # user_prompts = [
    #     "Add 5 and 6",
    # ]

    user_prompts = [
        "Change 'sphynx' to upper case",
    ]

    for r in run_queue(user_prompts):
        print(f">> [{r['task']}] {r['result']}")
