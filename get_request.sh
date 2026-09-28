#!/bin/bash

# Get a health request to server (launched by start_server.sh)

curl -X GET http://127.0.0.1:8000/health \
     -w '\n'
