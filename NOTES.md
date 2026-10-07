# nano-agent — learning notes

This document records how the ideas from **A Tour of Agents** were reconstructed as a small, conventional Python project that runs locally.

The aim was not simply to reproduce a working agent. It was to understand the machinery that agent frameworks normally hide:

```text id="l6p6vl"
LLM API
   ↓
tool calling
   ↓
agent loop
   ↓
conversation
   ↓
state
   ↓
memory
   ↓
policy / guardrails
```

The resulting project, `nano-agent`, is intentionally small and uses ordinary Python rather than an agent framework.

The later production stage builds an HTTP service, browser UI, Docker container, automated tests, persistent storage, and deployment infrastructure around this core. This document focuses on the **raw agent**.

> **Code examples marked “simplified” illustrate the idea and are not necessarily verbatim copies of the repository code.**

---

## 1. Starting point: what is an agent?

The basic idea is simple:

> An AI agent is a program that communicates with an LLM and acts on the LLM's instructions.

At the smallest scale:

```text id="uf0ti2"
user request
    ↓
LLM
    ↓
response
```

With tools:

```text id="r0c7h8"
user request
    ↓
LLM
    ↓
tool call
    ↓
Python function
    ↓
tool result
    ↓
LLM
    ↓
final answer
```

The important insight is that an agent does not require a special “agent API”. Its core can be built from ordinary Python functions, dictionaries, lists, loops, state, and HTTP requests.

---

# 2. Why build a local version?

The original course runs interactively in the browser using Python through Pyodide. That is convenient for teaching, but it hides some of the environment around the agent.

For `nano-agent`, we deliberately replaced that environment with ordinary local Python:

```text id="5c0f6e"
Course

Browser
   ↓
Pyodide
   ↓
Python


nano-agent

Terminal
   ↓
normal Python
```

During development, the real LLM was initially replaced by a local HTTP mock:

```text id="5tu2x8"
nano-agent
    ↓ HTTP
mock LLM server
```

This preserved the important external-service boundary while removing the need for:

```text id="rp8e7b"
browser execution
Pyodide
external API
API key
```

The local project therefore became a conventional Python application whose moving parts could be inspected directly.

---

# 3. Lesson 1 — The agent function

The first lesson reduces the agent to an ordinary function that calls an LLM.

### Simplified example

```python id="gxk4y6"
def agent(task):
    response = ask_llm(...)
    return response
```

The LLM client sends an HTTP request:

```python id="u3kfp7"
payload = {
    "messages": [
        {"role": "user", "content": "add 2 and 3"}
    ]
}

response = requests.post(
    base_url,
    json=payload,
)
```

The basic architecture is therefore:

```text id="av5q49"
agent
   ↓
LLM client
   ↓
HTTP
   ↓
LLM API
```

### Local adaptation

Instead of calling a real provider immediately, the local version called the mock server:

```text id="b5y3z8"
nano-agent
   ↓
HTTP
   ↓
127.0.0.1:8001
   ↓
mock LLM server
```

This made the HTTP boundary visible.

### What this teaches

The model is a **dependency**. The agent is the application logic around that dependency.

---

# 4. Lesson 2 — Tools = dictionary

The next lesson introduces actions the model can request.

### Simplified example

```python id="9uj3o0"
tools = {
    "add": add,
    "upper": upper,
}
```

If the LLM requests:

```text id="yutb9d"
tool = "add"
arguments = {"a": 2, "b": 3}
```

Python can dispatch the request with:

```python id="f79qjh"
result = tools[tool](**arguments)
```

So:

```text id="qmymw4"
LLM
 ↓
"name": "add"
 ↓
tools["add"]
 ↓
add(...)
```

There are two separate pieces:

```text id="xh4f6o"
tool definition
    → tells the LLM what it may request

tool registry
    → tells Python what function to execute
```

### What this teaches

Tool calling can be understood as **structured data plus ordinary Python dispatch**.

---

# 5. Lesson 3 — The agent loop

A single tool call is not enough. The model may need to inspect a tool result and then request another action.

### Simplified example

```python id="gtyv06"
while True:
    response = ask_llm(...)

    if response contains a tool call:
        result = run_tool(...)
        append result
        continue

    return response
```

The control flow is:

```text id="m6l7cp"
              ┌─────────────────────┐
              │                     ↓
user → LLM → tool call → tool → result
          ↑                       │
          └───────────────────────┘

                  or

                  ↓
             final answer
```

The LLM decides **what it wants to do next**. Python decides **how to execute it and whether the loop continues**.

### Local adaptation

The mock LLM was extended to return deterministic tool calls, allowing this cycle to be reproduced locally without relying on model behaviour.

### What this teaches

The agent itself is an **iterative control loop around the LLM**.

---

# 6. Lesson 4 — Conversation = messages

The LLM does not automatically receive previous turns. The application supplies the conversation explicitly.

### Simplified example

```python id="h1c2th"
messages = [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
]
```

Instead of treating requests independently:

```text id="0xusqk"
turn 1
turn 2
turn 3
```

we maintain one growing history:

```text id="4d1u2o"
turn 1
    ↓
messages

turn 2
    ↓
same messages + new user message

turn 3
    ↓
same messages + new user message
```

Tool interaction also becomes part of that history:

```text id="n0wpna"
user
  ↓
assistant → tool call
  ↓
tool → tool result
  ↓
assistant → final response
```

### What this teaches

Conversation is **explicit application state**. The model only knows what we include in its context.

---

# 7. Lesson 5 — State = dictionary

Conversation is only one kind of state.

An agent may also need:

```text id="hfn1xm"
messages
turn count
memory
metadata
```

### Simplified example

```python id="r0s3gt"
state = {
    "messages": messages,
    "turns": 0,
    "memory": {},
}
```

This gives us one coherent object:

```text id="yl1y9x"
state
├── messages
├── turns
├── memory
└── ...
```

The important distinction is:

```text id="enmnv7"
conversation ≠ all state
```

Conversation is one component of the application's state.

### What this teaches

A running agent needs **application state**, not just a chat transcript.

---

# 8. Lesson 6 — Memory

Conversation and memory answer different questions:

```text id="53b3bq"
Conversation
→ What has happened in this interaction?

Memory
→ What information should remain useful later?
```

A simple memory store is just a dictionary:

```python id="uo4z4k"
memory = {}
```

A `remember()` tool can update it:

```python id="q4v19o"
memory[key] = value
```

That information can later be supplied to the LLM again:

```text id="q05rcx"
remember(...)
    ↓
memory
    ↓
system prompt / context
    ↓
LLM
```

### Closures

Because `remember()` needs access to the same memory object, a closure is useful.

### Simplified example

```python id="jyp1j2"
def make_remember(memory):

    def remember(key, value):
        memory[key] = value

    return remember
```

The returned function retains access to the `memory` object from its enclosing scope.

### What this teaches

Memory is **ordinary application state deliberately carried into later model calls**.

---

# 9. Message roles and tool-call protocol

As tools and conversation were combined, the exact message structure became important.

Messages have roles such as:

```text id="4o19p6"
system
user
assistant
tool
```

Tool calls also need identifiers so their results can be associated with the correct request:

```text id="84zw3q"
assistant
    tool_call_id = X

tool
    tool_call_id = X
    result = ...
```

So the message history is not merely a transcript. It is part of the protocol exchanged with the model API.

### What this teaches

Once tools exist, **data structure is part of behaviour**. A malformed message is not merely inconvenient; it can break the protocol.

---

# 10. Lesson 7 — Policy and guardrails

The next lesson places explicit application logic around the LLM.

### Concept

```text id="q5gn7w"
user input
    ↓
input policy
    ↓
LLM
    ↓
agent loop
    ↓
output policy
    ↓
user
```

A simple input gate might be:

```python id="4b54x0"
if not input_allowed(task):
    return "Request rejected"
```

An output gate can similarly inspect the final response before it reaches the user.

The important point is that these controls belong to the **application**, not to the model itself.

### What this teaches

The LLM is one component inside a larger control structure.

---

# 11. Diagnostics and tracing

As the implementation grew, we needed ways to see what the agent was doing.

A small `utils.py` module was used for diagnostics and helper functions such as:

```python id="xekm11"
trace(...)
```

and:

```python id="w3xs4k"
extract_memory(...)
```

Tracing could be enabled or disabled independently of normal execution:

```text id="6r2g5b"
normal run
    → normal output

trace-enabled run
    → normal output + diagnostics
```

### What this teaches

Observability is a **separate concern** from the agent's main control flow.

---

# 12. Backend configuration

The local agent should not need to know which LLM provider it is talking to.

Instead, environment-specific details were moved into `config.py`.

### Simplified example

```python id="k2h6jm"
LLM_BACKEND = "mock"
LLM_BASE_URL = "http://127.0.0.1:8001"
```

The architecture becomes:

```text id="9f2nko"
nano-agent
    ↓
configuration
    ↓
selected backend
```

This later allowed the same core to use real providers without rewriting the agent loop.

### What this teaches

The core should depend on **configuration and interfaces**, not on hard-coded environment details.

---

# 13. Local HTTP mocking

The mock LLM deserves separate emphasis because it was central to the local reconstruction.

Instead of:

```text id="8fl0jx"
nano-agent
    ↓
Internet
    ↓
real LLM
```

we had:

```text id="2n7eim"
nano-agent
    ↓ HTTP
localhost
    ↓
mock LLM server
```

The mock could deliberately return:

```text id="pw1g4t"
normal response
tool call
malformed response
HTTP error
```

This made difficult cases deterministic.

A simple Python fake function could have replaced the LLM at some points, but the HTTP mock preserved the real external-service boundary:

```text id="npk1v2"
agent
   ↓
HTTP client
   ↓
remote-style service
```

That exposed:

```text id="iwz2iz"
request structure
response structure
HTTP status
JSON parsing
error handling
```

### What this teaches

A good mock preserves the **interface** of the real dependency while making its behaviour controllable.

---

# 14. Error handling

Once the agent crossed a real HTTP boundary, different kinds of failure had to be distinguished.

At minimum:

```text id="i7pmw3"
successful response
HTTP error
malformed JSON
unexpected response structure
```

For example:

```python id="wh4n1y"
response = requests.post(...)

if not response.ok:
    raise RuntimeError(
        f"LLM API returned HTTP {response.status_code}"
    )
```

Only then should a successful response be parsed according to the expected JSON structure.

### What this teaches

Handle errors at the **boundary where they occur**, and preserve the distinction between transport errors, parsing errors, and application errors.

---

# 15. Testing the core

The local mock also made deterministic testing practical.

Tests could exercise components such as:

```text id="p26j4a"
tool dispatch
message construction
response validation
error handling
memory extraction
```

For example:

```text id="a2a1gi"
test input
    ↓
mock LLM returns tool call
    ↓
agent executes tool
    ↓
tool result added to conversation
    ↓
next LLM call
    ↓
final answer
```

The important point is that the test does not need a live model to verify the control flow.

### What this teaches

**Deterministic dependencies make agent behaviour testable.**

---

# 16. Lesson 8 — Self-scheduling

The course then introduces an agent that can enqueue future work.

The basic idea is:

```text id="f9v6o4"
agent
  ↓
schedule follow-up
  ↓
queue
  ↓
future agent run
```

### Simplified example

```python id="t0rbi7"
queue = []

def schedule(task):
    queue.append(task)

while queue:
    task = queue.pop(0)
    agent(task)
```

This introduces another useful distinction:

```text id="m6tq4x"
current agent run
        ≠
future scheduled work
```

### What we chose for nano-agent

We deliberately did not make scheduling central to the minimal implementation.

That is itself an architectural lesson:

> Understanding a capability does not mean that the capability belongs in the minimal product.

Scheduling can remain a future extension until there is a concrete use case for it.

---

# 17. Lesson 9 — The whole thing

The final lesson composes the earlier concepts into one agent.

The resulting mental model is:

```text id="55h3y3"
                         state
                ┌─────────────────────┐
                │ messages             │
                │ turns                │
                │ memory               │
                └──────────┬──────────┘
                           ↕
                         agent
                           ↕
                    LLM client
                           ↕
                          LLM
                           ↕
                    external service

                           ↕

                    tool registry
                           ↓
                      Python tools
```

The essential loop remains:

```python id="n6f8mw"
while True:
    response = ask_llm(...)

    if response contains a tool call:
        result = run_tool(...)
        append result
        continue

    return response
```

The surrounding pieces answer different questions:

```text id="rdm9j8"
messages  → What context does the model receive?

state     → What does the application keep track of?

tools     → What actions can the model request?

memory    → What information is deliberately retained?

policy    → What may be accepted or returned?

config    → Which environment/backend is being used?

tracing   → What happened during execution?
```

### What this teaches

The apparent complexity of an agent comes largely from **composing a small number of mechanisms**.

---

# 18. Implementation milestones

The local project developed incrementally:

```text id="p1a2bd"
1. Local Python agent
       ↓
2. Local HTTP mock
       ↓
3. Tool registry and tool calls
       ↓
4. Agent loop
       ↓
5. Conversation history
       ↓
6. Structured state
       ↓
7. Memory
       ↓
8. Diagnostics / tracing
       ↓
9. Backend configuration
       ↓
10. Policy / guardrails
       ↓
11. Minimal core complete
```

A useful Git milestone was:

```text id="2v2k8f"
v0.1.0
Establish minimal agent core
```

After this milestone, the production work could be developed separately around the stable core.

---

# 19. What changed from the course?

The local project preserved the **agent concepts**, but changed the execution environment and development machinery.

```text id="x2x5zt"
Course
  → browser + Pyodide + direct LLM access

nano-agent
  → normal Python + local HTTP mock + configurable backend
```

The goal of the adaptation was therefore:

```text id="3m4gwy"
reproduce the concepts
        +
expose the engineering boundaries
```

The result is somewhat larger than the tiny course example, but the additional machinery is largely there to make those boundaries visible.

---

# 20. What we learned

The core lessons can be summarized without repeating the implementation details.

```text id="u1o7fo"
An agent is not a framework
    → it can be built from ordinary programming primitives.

The LLM is a dependency
    → the surrounding application controls the process.

Tool calling is a protocol
    → the model requests; Python executes.

Conversation is explicit
    → context must be supplied to the model.

State is broader than conversation
    → messages, memory, counters, and metadata may coexist.

Memory is application state
    → the application decides what to retain.

Policy surrounds the model
    → input and output gates are application concerns.

Mocks expose boundaries
    → deterministic external behaviour makes development and testing easier.

Configuration belongs outside the core
    → the same agent can operate in different environments.

Not every capability belongs in the minimal core
    → deliberate omission is part of good architecture.
```

---

# 21. Raw core vs. production system

The raw `nano-agent` is the **agent itself**.

The production stage adds infrastructure around that core:

```text id="jp8xj6"
RAW NANO-AGENT
      ↓
HTTP API
      ↓
Browser UI
      ↓
Docker
      ↓
runtime configuration
      ↓
automated tests
      ↓
persistent storage
      ↓
production operation
      ↓
deployment
      ↓
secure external access
```

So:

```text id="xqbbn4"
nano-agent
    = agent logic

production system
    = nano-agent
      + interface
      + runtime
      + storage
      + testing
      + deployment
      + operations
```

The production work therefore extends the core rather than replacing it.

---

# 22. Final mental model

The entire raw agent can be reduced to:

```text id="rzx6tp"
user
 ↓
agent loop
 ↓
LLM
 ↓
tool call?
 ├── yes → execute tool → append result → LLM again
 │
 └── no  → final response
```

with state surrounding the loop:

```text id="f55nh6"
                 ┌───────────────┐
                 │     state     │
                 │               │
                 │  messages     │
                 │  memory       │
                 │  metadata     │
                 └───────┬───────┘
                         ↕
                      agent
                         ↕
                        LLM
```

And the complete learning path is:

```text id="84ymgu"
understand the concept
        ↓
implement the mechanism
        ↓
make the boundary visible
        ↓
test the behaviour
        ↓
compose the pieces
        ↓
wrap the core in production infrastructure
```

The important outcome is therefore not merely a working Python program.

It is the ability to look at a larger agent framework and recognise the machinery underneath:

```text id="7fw9hg"
LLM call
+
messages
+
state
+
tool dispatch
+
loop
+
policy
```

`nano-agent` exists to make those mechanisms small enough to read, understand, modify, and debug directly.

The next step is to take that understandable core and turn it into something that can actually be operated as a product:

```text
understand the agent
        ↓
build the agent
        ↓
expose the agent
        ↓
test the agent
        ↓
package the agent
        ↓
persist its state
        ↓
operate the service
        ↓
deploy the product
```