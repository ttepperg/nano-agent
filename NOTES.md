# Minimal production agent — notes

The goal is to expose the existing `nano-agent` core as a small HTTP service, run it in a Docker container, and eventually provide a simple browser interface.

## 1. Overall architecture

The basic idea is to place an HTTP interface around the existing agent code:

```text
client
  ↓ HTTP
FastAPI
  ↓
nano-agent
  ↓
LLM
```

During development, the mock LLM can run separately:

```text
HTTP client
  ↓
FastAPI :8000
  ↓
nano-agent
  ↓
mock LLM :8001
```

In the containerised setup, the real LLM is used:

```text
HTTP client
  ↓
host :8000
  ↓
Docker container
  ↓
FastAPI / Uvicorn
  ↓
nano-agent
  ↓
GPT API
```

---

## 2. HTTP interface

Create `server.py` **outside the core agent code**:

```python
from fastapi import FastAPI
from nano_agent import agent
from pydantic import BaseModel


class RunRequest(BaseModel):
    task: str


app = FastAPI()


@app.post("/run")
def run_agent(request: RunRequest):
    return {"response": agent(request.task)}
```

Locally, the service can be started with:

```bash
python -m uvicorn server:app --reload
```

### FastAPI and Uvicorn

A useful mental model is:

```text
network
   ↕
Uvicorn
   ↕
FastAPI
   ↕
nano-agent
```

**Uvicorn** is the web server process. It listens for network connections and passes HTTP requests to FastAPI.

**FastAPI** is the application layer that translates HTTP requests into Python function calls and Python results back into HTTP responses.

So, loosely:

```text
Uvicorn = courier
FastAPI = bilingual interpreter
nano-agent = the part actually doing the work
```

For example:

```text
HTTP request
    ↓
POST /run + JSON
    ↓
Uvicorn
    ↓
FastAPI
    ↓
run_agent(request)
    ↓
agent(request.task)
```

---

## 3. Test with an HTTP request

For example:

```bash
curl -X POST http://127.0.0.1:8000/run \
     -H "Content-Type: application/json" \
     -d '{"task":"add 2 and 3"}' \
     -w '\n'
```

The response is HTTP JSON:

```json
{"response":"5"}
```

The `-w '\n'` adds a newline after the response so that the shell prompt does not appear on the same line.

---

## 4. Python dependencies

Create `requirements.txt` with the **third-party packages directly required by the service**:

```text
fastapi==0.133.1
uvicorn==0.41.0
pydantic==2.11.10
requests==2.32.5
```

Python's standard library does not need to be listed. For example:

```python
import json
```

works because `json` is included with Python itself.

Third-party packages may themselves have dependencies. For example:

```text
fastapi
  ├── starlette
  ├── pydantic
  └── ...

requests
  ├── urllib3
  ├── certifi
  ├── charset_normalizer
  └── idna
```

`pip` installs these transitive dependencies automatically.

For larger projects, dependency management should eventually be automated with a proper project/lock-file workflow rather than manually maintaining a list.

---

## 5. Containerise the service

Create a file named exactly:

```text
Dockerfile
```

with no extension:

```dockerfile
# Base Python environment
FROM python:3.12-slim

# Working directory inside the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Document the port used by the application
EXPOSE 8000

# Start FastAPI automatically when the container starts
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build the Docker image (Docker Desktop must be running):

```bash
docker build -t nano-agent .
```

This creates an **image** containing the application and its runtime environment.

---

## 6. Image vs. container

A useful analogy is:

```text
Docker image      → executable / blueprint
Docker container  → instance of that image
```

An image can therefore have multiple containers:

```text
nano_agent image
   ├── container A
   ├── container B
   └── container C
```

The image contains the packaged application and runtime environment.

The container is the isolated instance in which the application actually runs.

A closer process analogy is:

```text
program / executable  → process
Docker image         → container
                         ↑
                       instance
```

A container is more than just a process, however: it also has its own filesystem, networking, environment, etc.

---

## 7. Run the container

Run the image with:

```bash
docker run --rm \
    -p 8000:8000 \
    -e LLM_BACKEND=gpt \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    nano_agent
```

The container starts Uvicorn automatically via the `CMD` in the `Dockerfile`.

No separate `server.py` or Uvicorn process needs to be launched on the host.

The important point is:

> **The container starts the application; the HTTP request does not start the container.**

The container is started first and then remains available to receive HTTP requests.

---

## 8. Where does Uvicorn run?

In our setup, **Uvicorn runs inside the container**.

```text
Mac / host
┌───────────────────────────────────────┐
│                                       │
│   host :8000                          │
│       │                               │
└───────●───────────────────────────────┘
        │
        │ port mapping
        │
┌───────●──────────────────────────────────────┐
│ Docker container                             │
│                                              │
│   container :8000                            │
│       │                                      │
│     Uvicorn                                  │
│       ↓                                      │
│     FastAPI                                  │
│       ↓                                      │
│    nano-agent                                │
│                                              │
└──────────────────────────────────────────────┘
```

The `CMD` in the `Dockerfile`:

```dockerfile
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

means:

> When the container starts, run Uvicorn inside it.

---

## 9. Networking and port mapping

The `-p 8000:8000` option creates a **port mapping** between the host and the container.

A useful mental picture is a plug through the Docker wall:

```text
Mac :8000
    ↕
Docker port mapping
    ↕
container :8000
    ↕
Uvicorn
    ↕
FastAPI
    ↕
nano-agent
```

More explicitly:

```text
Mac / host
┌───────────────────────────┐
│                           │
│       :8000               │
│          │                │
└──────────●────────────────┘
           │
           │ port mapping
           │
┌──────────●──────────────────────┐
│ Docker container                │
│                                 │
│ container :8000                 │
│        ↓                        │
│      Uvicorn                    │
│        ↓                        │
│      FastAPI                    │
│        ↓                        │
│     nano-agent                  │
└─────────────────────────────────┘
```

For example:

```bash
docker run -p 9000:8000 ...
```

would mean:

```text
Mac :9000  →  container :8000
```

The application still listens on port `8000` inside the container; only the externally exposed host port changes.

---

## 10. Docker lifecycle

The basic lifecycle is:

```text
docker run    → create a new container from an image + start it
docker stop   → stop the container
docker start  → start an existing stopped container
docker restart → stop + start the same container
```

For example:

```bash
docker run --name nano-agent-test ...
```

creates and starts a new container.

Then:

```bash
docker stop nano-agent-test
```

stops that container.

The container still exists:

```text
container → Exited
```

and can be started again:

```bash
docker start nano-agent-test
```

or restarted directly:

```bash
docker restart nano-agent-test
```

### `docker run` vs `docker start`

```text
docker run
    ↓
image
    ↓
NEW container
    ↓
start it
```

whereas:

```text
docker start
    ↓
EXISTING stopped container
    ↓
start it again
```

If a container is started with `--rm`, Docker automatically removes it when it stops.

Useful inspection commands:

```bash
docker ps
```

show running containers.

```bash
docker ps -a
```

show running and stopped containers.

```bash
docker logs nano-agent-test
```

show the container's output.

---

## 11. Environment variables

Environment variables are inherited by processes.

For example:

```bash
export LLM_BACKEND=gpt
```

affects:

```text
this shell
    ↓
processes launched from this shell
```

It does **not** affect other already-running shells or processes:

```text
Terminal A
    export LLM_BACKEND=gpt
        ↓
    Uvicorn
        ↓
    nano-agent
        ↓
    sees LLM_BACKEND=gpt ✓


Terminal B
    ./post_request.sh
        ↓
    does NOT change Uvicorn's environment
```

> **⚠️ IMPORTANT:** The process that needs an environment variable must inherit it.

For example:

```bash
LLM_BACKEND=gpt python -m uvicorn server_ui:app --reload
```

sets `LLM_BACKEND` specifically for the Uvicorn process.

The same principle applies to containers: the environment variables passed with `docker run -e ...` become part of the container's environment.

---

## 12. Browser interface

FastAPI automatically provides an interactive API interface at:

```text
http://127.0.0.1:8000/docs
```

This is useful for testing `POST /run` without writing a separate client.

A minimal custom browser UI can also be provided by `server_ui.py`.

The browser-facing application keeps the same `/run` API but adds a homepage containing:

* a text input;
* a **Run** button;
* an area for the response.

The flow becomes:

```text
Browser
   ↓
GET /
   ↓
FastAPI
   ↓
HTML page
```

Then, after pressing **Run**:

```text
Browser
   ↓ POST /run
FastAPI
   ↓
nano-agent
   ↓
GPT
   ↓
JSON response
   ↓
Browser
```

The browser UI therefore sits **on top of the same HTTP API** rather than replacing it.

---

## 13. Current end-to-end architecture

At this stage, the complete system is:

```text
Browser / curl
       │
       │ HTTP
       ↓
 host :8000
       │
       │ Docker port mapping
       ↓
┌──────────────────────────────────┐
│ Docker container                 │
│                                  │
│   Uvicorn :8000                  │
│      ↓                           │
│   FastAPI                        │
│      ↓                           │
│   nano-agent                     │
│      ↓                           │
└──────┬───────────────────────────┘
       │
       │ HTTP API
       ↓
     GPT
```

The key conceptual layers are therefore:

```text
Docker      → packages and runs the application
Uvicorn     → handles the network connection
FastAPI     → translates HTTP ↔ Python
nano-agent  → performs the agent work
LLM API     → provides the language model
```
