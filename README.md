# nano-agent

**A minimal AI agent framework, built from scratch.**

`nano-agent` is a small, transparent implementation of an LLM-based agent. It provides the core machinery behind an agent without hiding it behind an agent SDK.

> **Current milestone:** The minimal agent core has been established. It provides a small, SDK-free agent loop with multi-step tool use, pluggable LLM backends, guardrails, conversation persistence, and a command-line interface.

## What it does

The agent can:

* interact with an LLM through an OpenAI-compatible API
* call Python tools using function calling
* maintain conversation state and long-term memory
* apply input and output guardrails
* schedule follow-up tasks
* trace its execution
* retry or diagnose API failures

## Architecture

```text
User
  │
  ▼
Agent
  ├── Input guardrails
  ├── Conversation / memory
  ├── LLM client
  │      │
  │      ▼
  │     LLM
  │      │
  │      ├── final response
  │      └── tool call
  │             │
  │             ▼
  │           Tool
  │
  ├── Scheduler
  └── Output guardrails
```

The project started with a mock LLM and was later connected to a real LLM, keeping the agent architecture unchanged.

## Project structure

```text
nano-agent/
├── cli.py
├── config.py
├── guardrails.py
├── llm_client.py
├── mock_llm.py
├── mock_server.py
├── nano_agent.py
├── tool_defs.py
├── tools.py
└── utils.py
```

## Why?

The goal is not to build a production-ready agent framework. It is to make the fundamental mechanisms of agentic systems small enough to understand, inspect, and modify.

## Status

Experimental / educational.

Built as a learning project while exploring LLMs, tool use, memory, guardrails, scheduling, and agent architecture.

## Usage

Select the LLM backend by setting the `LLM_BACKEND` environment variable to one of `mock`, `gemini` or `openai` (default: `mock`).

The LLM and server settings are defined in `config.py`. Adjust these settings to match your local setup or chosen LLM provider. API keys should be supplied via environment variables rather than stored in the repository.

For the Gemini backend, set `GEMINI_API_KEY` to your API key.

For the OpenAI backend, set `OPENAI_API_KEY` to your API key.

When using the mock backend, start the mock server with:

```text
python mock_server.py
```

Then start the agent with:

```text
python nano_agent.py
```

The agent runs interactively, accepting tasks at the `[user] >>` prompt and returning its responses at the `[nano-agent] <<` prompt.

<p align="center">
  <img src="images/nano-agent-demo.png"
       alt="nano-agent interactive session"
       width="300">
</p>

The agent can be terminated by entering `exit` or `quit`.

A single user request may involve multiple LLM/tool iterations. The agent executes these steps internally and returns one final response for the overall task.

For example:

```text
user task
   ↓
LLM → tool
   ↓
tool result
   ↓
LLM → tool
   ↓
tool result
   ↓
LLM → final response
```


### Command-line options

Optional runtime parameters can be supplied when starting the agent:

```text
python nano_agent.py --max-iter 5
```

`--max-iter` sets the maximum number of LLM iterations allowed for each task.

Run:

```text
python nano_agent.py --help
```

to see all available options.

### Model API testing

The `extras/model_api_test.py` script can be used to test the configured model APIs independently of the agent.

Run it from the repository root with:

```text
python -m extras.model_api_test --model <model-name>
```

The available model names are taken from the backend definitions in `config.py`. For example:

```text
python -m extras.model_api_test --model mock
python -m extras.model_api_test --model gemini
python -m extras.model_api_test --model openai
```

Use:

```text
python -m extras.model_api_test --help
```

to see the available model options.

### Response validation

Response validation is **optional but recommended**. The framework validates the HTTP response, JSON format, and expected Chat Completions response structure. This adds a defensive layer around the LLM client while keeping the core framework minimal.


## Acknowledgement

`nano-agent` was inspired by **[A Tour of Agents](https://tinyagents.dev/learn)**, a tutorial by Arun Purushothaman that explores the core concepts behind AI agent frameworks by building an agent from scratch.

*Created with Sphynx.* 🐈
