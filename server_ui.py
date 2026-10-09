"""
HTTP interface for the nano-agent with a minimal browser-based UI.

This module exposes the nano-agent through FastAPI and provides:
    - a simple web page at ``/`` with a text input and "Run" button;
    - a JSON API at ``POST /run`` that executes the agent.

The browser UI is implemented with plain HTML and JavaScript and
communicates with the FastAPI endpoint using HTTP.

Architecture:
    Browser
        ↓
    FastAPI
        ↓
    nano-agent
        ↓
    LLM
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from nano_agent import agent
from pydantic import BaseModel


class RunRequest(BaseModel):
    task: str


# Create a web application
app = FastAPI()

# health endpoint
@app.get("/health")
def health():
    return {"status": "OK"}

# Simple browser interface
# When a browser makes a GET request to / (relative to the server's origin), this script calls homepage() and return HTML.
# The response_class=HTMLResponse tells FastAPI that we're returning HTML, rather than JSON.
# async function runAgent(): JavaScript sends the HTTP request
# So the browser UI is essentially doing automatically what our curl command was doing manually (compare to post_request.sh):
# curl                    Browser JavaScript
# ────                    ──────────────────
# -X POST                 method: "POST"
# -H "Content-Type: ..."  headers: ...
# -d '{"task": ...}'      body: JSON.stringify(...)
@app.get("/", response_class=HTMLResponse)
def homepage():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Nano Agent</title>

        <style>
            html, body {
                height: 100%;
                margin: 0;
            }

            body {
                height: 100vh;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }

            header {
                padding: 0.25rem 1rem;
            }

            #conversation {
                flex: 1;
                min-height: 0;
                overflow-y: auto;
                padding: 1rem;
                display: flex;
                flex-direction: column;
            }

            #composer {
                display: flex;
                gap: 0.5rem;
                padding: 0.75rem 1rem;
                border-top: 1px solid #ddd;
                background: white;
            }

            #task {
                flex: 1;
                min-width: 0;
                padding: 0.6rem;
            }

            #composer button {
                padding: 0.6rem 1rem;
            }

            .message {
                max-width: 85%;
                margin: 0.75rem 0;
                padding: 0.75rem 1rem;
                border-radius: 8px;
                white-space: pre-wrap;
                overflow-wrap: anywhere;
            }

            .user {
                margin-left: auto;
                background: #e8f2ff;
            }

            .agent {
                margin-right: auto;
                background: #f1f1f1;
            }

            .message-label {
                display: block;
                font-weight: bold;
                margin-bottom: 0.25rem;
            }
        </style>

    </head>
    <body>

        <header>
            <h1>Nano Agent</h1>
        </header>

        <div id="conversation"></div>

        <footer id="composer">
            <input id="task" type="text"
                   placeholder="Enter a task">
            <button onclick="runAgent()">Run</button>
        </footer>

        <script>

            function scrollToBottom() {
                const conversation = document.getElementById("conversation");

                conversation.scrollTo({
                    top: conversation.scrollHeight,
                    behavior: "smooth"
                });
            }
            function addMessage(role, text) {
                const message = document.createElement("div");
                message.className = `message ${role}`;

                const label = document.createElement("strong");
                label.className = "message-label";
                label.textContent = role === "user" ? "You" : "Nano Agent";

                const content = document.createElement("div");
                content.textContent = text;

                message.append(label, content);
                document.getElementById("conversation").appendChild(message);

                scrollToBottom();

                return content;
            }

            async function runAgent() {
                const taskInput = document.getElementById("task");
                const task = taskInput.value.trim();

                if (!task) return;

                addMessage("user", task);
                const agentContent = addMessage("agent", "Thinking...");
                taskInput.value = "";

                try {
                    const response = await fetch("/run", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({task: task})
                    });

                    if (!response.ok) {
                        const errorText = await response.text();
                        agentContent.textContent =
                            `Server error (${response.status}): ` +
                            (errorText || "The request failed.");
                        return;
                    }

                    const data = await response.json();
                    agentContent.textContent = data.response;

                } catch (error) {
                    agentContent.textContent =
                        "Could not connect to the server.";
                } finally {
                    scrollToBottom();
                }
            }
        </script>

    </body>
    </html>
    """


# When an HTTP POST arrives at /run, execute the agent
@app.post("/run")
def run_agent(request: RunRequest):
    return {"response": agent(request.task)}
