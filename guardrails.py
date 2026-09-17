from utils import trace

INPUT_RULES = [
    lambda text: "delete" not in text.lower() or "Input blocked: no delete commands",
    lambda text: "drop" not in text.lower() or "Input blocked: no drop commands",
    lambda text: len(text) < 500 or "Input blocked: message too long",
]
OUTPUT_RULES = [
    lambda text: "password" not in text.lower() or "Output redacted: contains password",
    lambda text: "secret" not in text.lower() or "Output redacted: contains secret",
]

def check_gate(text, rules, gate_name):
    for rule in rules:
        result = rule(text)
        if result is not True:
            trace("policy_block", f"{gate_name}: {result}")
            return False, result
    trace("policy_check", f"{gate_name}: PASS")
    return True, None
