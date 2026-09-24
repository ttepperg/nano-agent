#!/bin/bash

# Start a HTTP service

python3.12 -m uvicorn server:app --reload
