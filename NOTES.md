# Minimal production agent — notes

The goal is to expose the existing `nano-agent` core as a small HTTP service and run it in a Docker container.

## 1. HTTP interface

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

This starts Uvicorn, which runs the FastAPI application and listens for HTTP requests.

`/run` is the HTTP endpoint handled by `run_agent()`.

## 2. Test with an HTTP request

For example:

```bash
curl -X POST http://127.0.0.1:8000/run \
     -H "Content-Type: application/json" \
     -d '{"task":"add 2 and 3"}' \
     -w '\n'
```

The request is:

```text
curl
  ↓
FastAPI :8000
  ↓
agent()
  ↓
LLM
  ↓
HTTP JSON response
```

During development, the mock LLM runs separately on port `8001`.

## 3. Declare Python dependencies

Create `requirements.txt` with the packages needed by the service.

For example:

```text
fastapi==0.133.1
uvicorn==0.41.0
pydantic==2.11.10
requests==2.32.5
```

In a larger project, dependency management should eventually be automated with a proper project/lock-file workflow.

## 4. Containerise the service

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

This creates an image containing the application and its runtime environment.

## 5. Run the container

```bash
docker run --rm \
    -p 8000:8000 \
    -e LLM_BACKEND=gpt \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    nano_agent
```

The container starts Uvicorn automatically via the `CMD` in the `Dockerfile`.

No separate `server.py` process needs to be launched on the host.

The port mapping means:

```text
host :8000  →  container :8000
```

## 6. End-to-end production-style test

With the container running, from another terminal:

```bash
./post_request.sh
```

The complete path is now:

```text
client
  ↓ HTTP POST
host :8000
  ↓
Docker container
  ↓
FastAPI / Uvicorn
  ↓
nano-agent
  ↓
GPT API
  ↓
HTTP JSON response
```

Example:

```json
{"response":"5"}
```

## Mental model

Docker is **not** the HTTP interface.

Docker provides the packaged runtime and starts the application.

FastAPI provides the HTTP interface.

So:

```text
Docker
  → starts and contains the application

FastAPI
  → receives HTTP requests

nano-agent
  → does the actual agent work
```

On macOS, Docker Desktop runs Linux containers inside its Linux environment.

## Development vs. containerised setup

Development with the mock LLM:

```text
HTTP client
  ↓
FastAPI :8000
  ↓
nano-agent
  ↓
mock LLM :8001
```

Containerised test with the real LLM:

```text
HTTP client
  ↓
Docker :8000
  ↓
FastAPI
  ↓
nano-agent
  ↓
GPT API
```

The container is started once and remains available to receive HTTP requests; the HTTP request does **not** start the container.
