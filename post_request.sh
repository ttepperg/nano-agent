#!/bin/bash

# Post a request to server (launched by start_server.sh)

curl -X POST http://127.0.0.1:8000/run \
     -H "Content-Type: application/json" \
     -d '{"task":"add 2 and 3"}'
