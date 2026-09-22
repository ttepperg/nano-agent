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
import tools
from tool_defs import TOOL_DEFS
from guardrails import INPUT_RULES, OUTPUT_RULES, check_gate
from utils import trace, save_conversation
from llm_client import ask_llm
from cli import parse_args


# SYSTEM PROMPT
SYSTEM = "You have tools. add(a,b) to add two numbers. upper(text) to capitalize text. remember() to save facts. Use them when needed. Be concise."

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
    "memory": memory_dict,
    "usage": {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
}

# TOOL REGISTRY
TOOL_REGISTRY = {
    "add": tools.add,
    "upper": tools.upper,
    "remember": tools.make_remember(memory_dict),
}

# ------ ORCHESTRATOR ------
def agent(task, max_iters = 5):
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
    save_conversation(conversation)

    # record state
    turn_id = len(state["turns"])
    state["turns"].append({"id": turn_id+1, "iterations": 0})

    for iter in range(max_iters):
        state["turns"][turn_id]["iterations"] = iter+1
        trace("llm_call", f"Turn: {turn_id}  Iterations: {iter+1}")
        result = ask_llm(conversation, TOOL_DEFS)
        llm_response = result["message"]
        usage = result["usage"]
        if usage:
            state["usage"]["prompt_tokens"] += usage["prompt_tokens"]
            state["usage"]["completion_tokens"] += usage["completion_tokens"]
            state["usage"]["total_tokens"] += usage["total_tokens"]
        trace(
            "llm_usage",
            f"Prompt: {usage['prompt_tokens']}  "
            f"Completion: {usage['completion_tokens']}  "
            f"Total: {usage['total_tokens']}"
        )
        if not llm_response.get("tool_calls"): # not tasks left -> final answer
            final_answer = llm_response.get('content', '')
            # ----- OUTPUT GATE -----
            ok, reason = check_gate(final_answer, OUTPUT_RULES, 'OUTPUT')
            if not ok: return f"REDACTED: {reason}"
            conversation.append({"role": "assistant", "content": final_answer})
            save_conversation(conversation)
            trace("agent_end",
                f"Done in {state["turns"][turn_id]["iterations"]} iterations")
            return final_answer
        # add LLM message to conversation
        conversation.append(llm_response)
        save_conversation(conversation)
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
            save_conversation(conversation)

    trace("agent_end", f"Maximum iterations reached: {max_iters}")
    return f"Agent stopped after reaching the maximum of {max_iters} iterations."


def main():
    """ Runs thd main loop as an interactive session via the command line"""

    args = parse_args()

    print("="*100)
    while True:

        task = input("[user] >> ")

        if task.lower() in {"exit", "quit"}:
            break

        print("[nano-agent] ... processing", end="\r", flush=True)

        result = agent(task, max_iters=args.max_iters)

        # just cosmetics (optional)
        display_result = ", ".join(line.strip() for line in result.splitlines())

        print(f"\033[K[nano-agent] << {display_result}")
        print(
            f" Usage:\n"
            f"   Prompt tokens:     {state['usage']['prompt_tokens']}\n"
            f"   Completion tokens: {state['usage']['completion_tokens']}\n"
            f"   Total tokens:      {state['usage']['total_tokens']}\n"
        )


# ------ MAIN ------
if __name__ == "__main__": main()

    # DO NOT DELETE: The first ever successful call to Gemini (17 SEP 2026)
    # user_prompts = [
    #     "Add 5 and 6",
    # ]
