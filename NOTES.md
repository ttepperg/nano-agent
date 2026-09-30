# Minimal production agent — notes

The goal is to expose the existing `nano-agent` core as a small HTTP service, run it in a Docker container, and provide a simple browser interface.

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

The HTTP interface is implemented separately from the core agent code.

### 2.1 API-only interface: `server.py`

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

### 2.2 Browser-enabled interface: `server_ui.py`

`server_ui.py` provides essentially the same `POST /run` API as `server.py`, but additionally serves a simple browser interface.

It therefore combines:

```text
HTTP API
    +
browser UI
```

Locally, the browser-enabled service can be started with:

```bash
python -m uvicorn server_ui:app --reload
```

The two modules therefore provide two ways of running essentially the same service:

```text
server.py
    → HTTP API only

server_ui.py
    → HTTP API + browser UI
```

The details of how the browser interface is implemented are described in Section 13.


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
Uvicorn = web server
FastAPI = HTTP ↔ Python interface
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

FastAPI also provides an interactive API interface at:

```text
http://127.0.0.1:8000/docs
```

This can be used to test `POST /run` without writing a separate client.

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

with no extension.

Build the Docker image (Docker Desktop must be running):

```bash
docker build -t nano-agent .
```

This creates an **image** containing the application and its runtime environment.

### 5.1 The Dockerfile

A `Dockerfile` is a set of instructions for **building a Docker image**. It describes the environment our application needs and what should happen when a container is started from the resulting image.

Our Dockerfile is:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --create-home appuser

RUN mkdir -p /app/data \
    && chown -R appuser:appuser /app/data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["uvicorn", "server_ui:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 What the instructions mean

```text
FROM
```

Selects the **base image** on which our image is built. Here, we start from a minimal Python 3.12 environment.

```text
WORKDIR /app
```

Sets `/app` as the working directory inside the image/container.

```text
COPY requirements.txt .
```

Copies the dependency file from the build context into `/app`.

```text
RUN pip install --no-cache-dir -r requirements.txt
```

Runs a command **while building the image**, installing the Python dependencies.

```text
COPY . .
```

Copies the application files from the build context into the image. Files excluded by `.dockerignore` are not included.

```text
RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --create-home appuser
```

Runs commands **while building the image** to create an ordinary, unprivileged Linux user called `appuser`.

The `groupadd` command creates a group named `appuser` with GID `10001`.

The `useradd` command creates the user `appuser` with UID `10001`, makes `appuser` a member of the `appuser` group, and creates its home directory at `/home/appuser`.

These commands can run without a password because Docker executes the build steps as `root` by default.

```text
RUN mkdir -p /app/data \
    && chown -R appuser:appuser /app/data
```

Ensures that the application's writable data directory exists and gives ownership of it to `appuser`.

`mkdir -p` creates `/app/data` if it does not already exist. If the directory already exists, it does not replace or overwrite it.

`chown -R appuser:appuser` changes the owner and group of `/app/data` and everything inside it to `appuser`.

This happens **inside the Docker image**; it does not modify the corresponding `data/` directory on the host.

The result is that application code can remain owned by `root`, while the specific directory that the application needs to modify is writable by `appuser`.

```text
USER appuser
```

Sets `appuser` as the user for subsequent instructions and, importantly, as the default user when a container is started from the image.

Thus, Uvicorn, FastAPI, and `nano-agent` run as `appuser` rather than `root`.

```text
EXPOSE 8000
```

Documents that the application is expected to listen on port `8000` inside the container. It does **not** itself publish the port to the host; that is done when the container is run with `-p`.

```text
HEALTHCHECK ...
```

Defines a test Docker periodically performs to determine whether the application inside the container is responding correctly.

```text
CMD [...]
```

Defines the **default command executed when a container is started from the image**.

In our case, this launches Uvicorn, which loads `server_ui:app` and listens on port `8000`.

### 5.3 Build time vs. container runtime

A useful distinction is:

```text
docker build
    ↓
Dockerfile instructions
    ↓
IMAGE
```

Some instructions act during image construction, such as `FROM`, `COPY`, and `RUN`.

Then, later:

```text
docker run / docker start
    ↓
CONTAINER
    ↓
USER appuser
    ↓
CMD starts Uvicorn
```

`USER` therefore affects the identity under which the application runs, while `RUN groupadd ...`, `RUN useradd ...`, and `RUN chown ...` have already prepared the filesystem and users inside the image during the build.

---

## 6. Image vs. container

A useful analogy is:

```text
Docker image      → executable / blueprint
Docker container  → instance of that image
```

An image can therefore have multiple containers:

```text
nano-agent image
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
docker run --name nano-agent-test \
    -p 8000:8000 \
    -e LLM_BACKEND=gpt \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    nano-agent
```

The container starts Uvicorn automatically via the `CMD` in the `Dockerfile`.

No separate `server_ui.py` or Uvicorn process needs to be launched on the host.

The important point is:

> **The container starts the application; the HTTP request does not start the container.**

The container is started first and then remains available to receive HTTP requests.

### Inspecting a running container

A useful way to inspect a running container is:

```bash
docker exec -it nano-agent-test /bin/sh
```

This starts an interactive shell **inside the existing running container**.

The `-i` flag keeps the session interactive, while `-t` allocates a terminal (TTY). The `/bin/sh` argument specifies the shell process to start.

For example:

```bash
whoami
id
pwd
ls -la /app
ls -ld /home/appuser
```

These commands inspect the container's user, filesystem, permissions, and application files.

`docker exec` starts an **additional process** inside the container; it does not replace or attach to the application's main process.

For example, while Uvicorn is running:

```text
container
├── Uvicorn
│    └── FastAPI
│         └── nano-agent
│
└── /bin/sh     ← shell started with docker exec
```

`exit` leaves the shell, but the container and its main application process continue running.

The container's application files may be owned by `root` while the application itself runs as the unprivileged `appuser`. With permissions such as:

```text
-rw-r--r-- 1 root root ... server_ui.py
```

`appuser` can read the file but cannot modify it.

This is consistent with the least-privilege principle: the application does not need to run as `root` merely because `root` owns the application files.

### Writable application data

Running the application as a non-root user can expose directories that the application needs to write to.

In our case, `nano-agent` stores conversation state in:

```text
/app/data/conversation.json
```

The application files copied by:

```dockerfile
COPY . .
```

are initially owned by `root`. Rather than making the whole application tree writable, we give `appuser` ownership of only the directory that needs to be modified:

```dockerfile
RUN mkdir -p /app/data \
    && chown -R appuser:appuser /app/data
```

`mkdir -p` ensures that the directory exists without replacing an existing directory or its contents. `chown -R` changes the ownership of the directory and everything inside it **within the image/container**; it does **not** change the file contents.

This results in a useful separation:

```text
/app
├── application code      root:root
│                         └── appuser can read
│
└── data/                 appuser:appuser
                          └── appuser can read/write
```

This is an example of the **least-privilege principle**: give the application write access only where it actually needs it.

---

### Running the agent from the CLI

The same Docker image can also be used to run the agent directly from the command line, without starting Uvicorn or the browser interface.

Override the image's default `CMD`:

```bash
docker run --rm -it \
    -e LLM_BACKEND=gpt \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    nano-agent python nano_agent.py
```

The final argument:

```text
python nano_agent.py
```

replaces the `CMD` defined in the `Dockerfile` for this particular container.

Thus the same image can be used for different purposes:

```text
nano-agent image
    ├── web container
    │     └── Uvicorn → FastAPI → nano-agent
    │
    └── CLI container
          └── python nano_agent.py
```

`--rm` removes the CLI container automatically when it exits, while `-it` provides an interactive terminal.

An alternative during development is to enter an already-running web container with:

```bash
docker exec -it nano-agent-test /bin/sh
```

and then run:

```bash
python nano_agent.py
```

This works, but starts an additional process inside the web container. Running a separate CLI container keeps the two roles independent.

Because a new CLI container has its own filesystem, changes to `data/conversation.json` are not shared with another container and are lost when a container created with `--rm` is removed. Persistent shared application data will therefore need a separate storage mechanism.


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
CMD ["uvicorn", "server_ui:app", "--host", "0.0.0.0", "--port", "8000"]
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

For example:

```bash
docker run -p 9000:8000 ...
```

would mean:

```text
Mac :9000  →  container :8000
```

The application still listens on port `8000` inside the container; only the externally exposed host port changes.

### Ports and IP addresses

A simplified mental model is:

```text
IP address = which machine/network endpoint?
Port       = which numbered network endpoint?
```

A port is not itself a service. A service is a program that listens on a port.

For example:

```text
127.0.0.1:8000
│             │
│             └── port
└──────────────── IP address
```

The IP address and port together identify the network endpoint to which a client connects.

A machine can have multiple network interfaces and addresses, and the same port number may be used on different addresses.

### Loopback

`127.0.0.1` is the standard IPv4 **loopback** address. It means:

> “this machine itself.”

Traffic sent to `127.0.0.1` is sent back into the same machine rather than out onto the network.

In Docker, the container has its own network namespace, so its `127.0.0.1` refers to the **container itself**, not the Mac.

This is why the health check can use:

```text
127.0.0.1:8000
```

from inside the container.

### `0.0.0.0`

When Uvicorn is started with:

```text
--host 0.0.0.0
```

it listens on port `8000` on all available IPv4 network interfaces inside the container.

This allows Docker's port mapping to deliver traffic to Uvicorn.

The browser, however, connects to the host:

```text
http://127.0.0.1:8000/
```

The two addresses therefore refer to different network contexts:

```text
host:
127.0.0.1 → the Mac itself

container:
127.0.0.1 → the container itself
```

---

## 10. Docker lifecycle

The basic lifecycle is:

```text
docker run     → create a new container from an image + start it
docker stop    → stop the container
docker start   → start an existing stopped container
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

### `docker run` vs. `docker start`

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

## 11. Container health checks

A Docker `HEALTHCHECK` tests whether the application inside the container is actually responding, rather than merely checking whether the container's main process is running.

Our health check calls:

```text
GET http://127.0.0.1:8000/health
```

from **inside the container**.

The timing parameters control how Docker performs these checks:

```text
--interval=30s
--timeout=3s
--start-period=5s
--retries=3
```

`--start-period` is an initial grace period for the application to start; it is **not** added before every health check. After startup, Docker performs checks at the configured `--interval`.

The `--timeout` sets the maximum duration of each individual check. If a check takes the full timeout, the next check begins roughly `timeout + interval` later.

With our settings, a failed check can therefore take up to about **33 seconds** before the next check is attempted, rather than `5 + 30 + 3` seconds.

A health check can fail even while the application continues to run. For example, when we temporarily changed the check from:

```text
/health
```

to:

```text
/health-does-not-exist
```

the application continued to serve `POST /run`, but Docker reported:

```text
Up ... (unhealthy)
```

This demonstrates:

```text
container process:  running ✓
health check:       failing ✗
```

A `HEALTHCHECK` is therefore a **diagnostic signal**. It does not by itself restart or stop the container.

---

## 12. Environment variables

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

### `.env`, runtime configuration and secrets

Environment-specific configuration can be kept in a local `.env` file rather than being embedded in the Docker image or written directly into the `docker run` command.

For example:

```text
LLM_BACKEND=gpt
OPENAI_API_KEY=your-real-api-key
```

The `.env` file contains the actual local values, including secrets, and should **not** be committed to Git or copied into the Docker image. It is therefore listed in both `.gitignore` and `.dockerignore`.

A `.env.example` file can be committed to the repository as a template:

```text
LLM_BACKEND=gpt
OPENAI_API_KEY=your-openai-api-key-here
```

It documents which variables are required without containing real credentials.

The variables can be supplied to the container at runtime with:

```bash
docker run --name nano-agent-test \
    -p 8000:8000 \
    --env-file .env \
    nano-agent
```

This keeps the Docker image independent of the environment in which it is run: the same image can be used with different runtime configuration and credentials.

The variables supplied with `--env-file` become part of the container's environment. They can be verified from inside the running container, for example:

```bash
docker exec nano-agent-test sh -c 'echo "LLM_BACKEND=$LLM_BACKEND" ; test -n "$OPENAI_API_KEY" && echo "OPENAI_API_KEY is set"'
'
```
This confirms that the ordinary configuration variable has the expected value and that the API key is present, without printing the secret itself.

## 13. Browser interface

`server_ui.py` provides the browser-facing part of the application.

### 13.1 Serving the homepage

The homepage is implemented by a FastAPI route:

```python
@app.get("/", response_class=HTMLResponse)
def homepage():
    ...
```

The `@app.get("/")` decorator tells FastAPI to call `homepage()` when a client sends a `GET /` request.

`response_class=HTMLResponse` tells FastAPI that the function returns HTML rather than JSON.

The function returns the HTML for the browser interface as a Python multi-line string. The browser receives that HTML and renders the page.

Thus:

```text
Browser
   ↓ GET /
FastAPI
   ↓
homepage()
   ↓
HTML response
   ↓
Browser renders the UI
```

The page contains:

```text
text input
Run button
result area
```

### 13.2 Submitting a task

The **Run** button is handled by JavaScript embedded in the HTML page.

When the button is pressed, the JavaScript:

1. reads the text from the input field;
2. sends a `POST /run` request;
3. waits for the HTTP response;
4. displays the returned result in the page.

For example, entering:

```text
add 2 and 3
```

causes the browser to send approximately:

```text
POST /run
Content-Type: application/json

{"task":"add 2 and 3"}
```

The `/run` endpoint then invokes `nano-agent` and returns:

```json
{"response":"5"}
```

The browser displays:

```text
5
```

The browser is therefore simply another HTTP client of the API.

The distinction between the two main browser requests is:

```text
GET /
    → retrieve the browser interface

POST /run
    → submit a task for the agent to process
```

The browser UI does not replace the API; it uses the same API.


### 13.3 Error handling

The browser UI explicitly distinguishes between a server-side HTTP error and a failure to connect to the server.

If the server is reached but the request fails, for example with HTTP `500`, the UI reports:

```text
Server error (500): Internal Server Error
```

If the server cannot be reached at all, the JavaScript `fetch()` call fails and the UI reports:

```text
Could not connect to the server.
```

These are different failure modes:

```text
server reachable
    ↓
HTTP 500
    ↓
Server error (...)


server not reachable
    ↓
fetch() fails
    ↓
Could not connect to the server.
```

During testing, an additional bug was discovered: the initial error-handling code attempted to parse every response as JSON before checking the HTTP status. FastAPI's default `500 Internal Server Error` response is not JSON, so the JSON parsing itself failed and incorrectly triggered the connection-error message.

The fix is to check `response.ok` before attempting to parse a successful response as JSON, and to read the error response as text when the HTTP status indicates failure.

This means the UI now provides useful feedback for both backend failures and genuine connection failures.


### Automated API tests

The FastAPI application is tested with `pytest` and FastAPI's `TestClient`. `TestClient` allows the application to be exercised directly, without starting Uvicorn or making a real network connection.

The current tests cover three basic cases:

```text
test_health.py
    → GET /health
    → expected HTTP 200 response

test_run.py
    → valid POST /run request
    → agent is replaced by a fake during the test
    → expected HTTP 200 response and JSON result

test_validation.py
    → invalid POST /run request with no task
    → FastAPI/Pydantic rejects the request
    → expected HTTP 422 response
```

Together they cover:

```text
happy paths
    → /health
    → valid /run request

failure path
    → invalid /run request
```

The `test_run.py` test deliberately does not call the real agent or GPT API. It replaces `server_ui.agent` temporarily with a small fake function, allowing the HTTP layer to be tested independently of the agent and external services.

The tests can be run with:

```bash
pytest
```

A successful run currently reports:

```text
3 passed
```


## 14. Current end-to-end architecture

At this stage, the complete system is:

```text
Browser / curl
       │
       ↕ HTTP
 host :8000
       │
       ↕ Docker port mapping
       │
┌─────────────────────────────┐
│ Docker container            │
│                             │
│   Uvicorn :8000             │
│       ↕                     │
│   FastAPI                   │
│       ↕                     │
│   nano-agent                │
│       ↕                     │
└───────┬─────────────────────┘
        │
        ↕ HTTP
      GPT API
```

The key conceptual layers are therefore:

```text
Docker      → packages and runs the application
Uvicorn     → handles the network connection
FastAPI     → translates HTTP ↔ Python
nano-agent  → performs the agent work
LLM API     → provides the language model
```
