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
# So the browser UI is essentially doing automatically what our curl command was doing manually.
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
    </head>
    <body>
        <h1>Nano Agent</h1>

        <input id="task" type="text" size="50"
               placeholder="Enter a task">
        <button onclick="runAgent()">Run</button>

        <pre id="result"></pre>

        <script>

            async function runAgent() {
                const task = document.getElementById("task").value;
                const result = document.getElementById("result");

                result.textContent = "Running...";

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

                        result.textContent =
                            `Server error (${response.status}): ` +
                            (errorText || "The request failed.");
                        return;
                    }

                    const data = await response.json();
                    result.textContent = data.response;

                } catch (error) {
                    result.textContent =
                        "Could not connect to the server.";
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
