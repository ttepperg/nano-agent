# nano-agent

**A minimal AI agent framework, built from scratch.**

`nano-agent` is a small, transparent implementation of an LLM-based agent. It provides the core machinery behind an agent without hiding it behind an agent SDK.

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
├── agent.py
├── tools.py
├── tool_defs.py
├── guardrails.py
├── mock_llm.py
├── utils.py
└── config.py
```

## Why?

The goal is not to build a production-ready agent framework. It is to make the fundamental mechanisms of agentic systems small enough to understand, inspect, and modify.

## Status

Experimental / educational.

Built as a learning project while exploring LLMs, tool use, memory, guardrails, scheduling, and agent architecture.

## Acknowledgement

`nano-agent` was inspired by **[A Tour of Agents](https://tinyagents.dev/learn)**, a tutorial by Arun Purushothaman that explores the core concepts behind AI agent frameworks by building an agent from scratch.

*Created with Sphynx.* 🐈
