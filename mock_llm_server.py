"""

About
    A mock HTTP server that emulates an Large Language Model (LLM) application programming interface  (API)


    Created with Sphynx

Run
    $> py312 mock_server.py

    [and leave running...then run nano_agent.py]

Needed by
    nano_agent.py

Calls
    mock_llm.py

"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import mock_llm

 # BEWARE: Use *only* for development:
import importlib
import utils
import config

class LLMHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        # Refresh modules content (in case it is modified while running)
        # BEWARE: Use *only* for development
        importlib.reload(mock_llm)
        importlib.reload(utils)
        importlib.reload(config)

        # How many bytes are in the request body?
        length = int(self.headers["Content-Length"])

        # Read and decode the request body
        body = self.rfile.read(length).decode("utf-8")

        # Turn JSON text into a Python dictionary
        request = json.loads(body)

        # Can also simply print(body), but this is formatted:
        utils.debug("\nReceived:\n", json.dumps(request, indent=2))

        # Construct a *fake* LLM response
        # In reality, the 'request' is POSTed to a real LLM API,
        # which provides a 'response'
        response = mock_llm.llm_api(request)

        # Convert our Python dictionary to JSON text to bytes
        response_json = json.dumps(response).encode("utf-8")

        # Send the HTTP response
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_json)))
        self.end_headers()

        self.wfile.write(response_json)


# Start the server
server = HTTPServer(("localhost", config.MOCK_PORT), LLMHandler)
print(f"Mock LLM listening on http://localhost:{config.MOCK_PORT}")
server.serve_forever() # keep running...
