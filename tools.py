""" Tools available to the LLM"""

# --------------------------------------
# TASK TOOLS: Add as many as required
def add(a,b):
    return a + b

def upper(text):
    return text.upper()

# --------------------------------------
# AGENT SUPPORTING INFRASTRUCTURE

# --------- DO NOT CHANGE ---------
def make_remember(memory):
    """Create a closure that retains access to the memory object."""
    def remember(key, value):
        memory.update({key: value})
        return f"Saved to memory: {key}={value}"
    return remember
