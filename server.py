"""
    For the mock production version, I'd aim for a very small but real vertical slice:

            client
              ↓
            HTTP API
              ↓
            agent
              ↓
            LLM
              ↓
            tools
              ↓
            response

    A web application: here, a Python program designed to receive requests over a network and send responses back:

        client  ─── HTTP request ───→  Python program
        client  ←── HTTP response ─── Python program

    To start the server:

    py312 -m uvicorn server:app --reload

"""
from fastapi import FastAPI
from nano_agent import agent
from pydantic import BaseModel

class RunRequest(BaseModel):
    task: str

# Create a web application
app = FastAPI()


# When an HTTP POST arrives at /run (e.g. http:someurl/run), execute this function (run_agent)
@app.post("/run")
def run_agent(request: RunRequest):
    return {"response": agent(request.task)}
