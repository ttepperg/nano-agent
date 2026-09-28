#!/bin/bash

# Start a HTTP service (input argument)
# E.g.
# ./start_server.sh server (for server.py)
# ./start_server.sh server_ui (for server_ui.py)

python3.12 -m uvicorn ${1}:app --reload
