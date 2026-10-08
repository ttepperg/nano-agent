#!/bin/bash

# Deploy the production service using Docker Compose
# Creates the persistent conversation volume if it does not exist

docker volume inspect nano-agent-data >/dev/null 2>&1 || \
    docker volume create nano-agent-data

docker compose up -d
