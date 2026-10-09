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
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from nano_agent import agent
from pydantic import BaseModel


class RunRequest(BaseModel):
    task: str


# Create a web application
app = FastAPI()

# mount static folder, which provides stylesheet and JavaScript files
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
)

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
@app.get("/")
def homepage():
    html_path = Path(__file__).parent / "static" / "index.html"
    return FileResponse(html_path)

# When an HTTP POST arrives at /run, execute the agent
@app.post("/run")
def run_agent(request: RunRequest):
    return {"response": agent(request.task)}
