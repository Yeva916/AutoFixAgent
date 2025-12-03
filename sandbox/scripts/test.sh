#!/bin/bash

RUN_ID="$1"
HOST_RUN_DIR=$(pwd)/backend/runs/"$RUN_ID"
echo "Using host run directory: $HOST_RUN_DIR"
mkdir -p "$HOST_RUN_DIR/sandbox/scripts/logs"
#Remove the container after it exits
docker run --rm \
    -v "$HOST_RUN_DIR/repo":/repo:rw \
    -v "$HOST_RUN_DIR/test_results":/test_results:rw \
    -w /repo \
    --user "$(id -u):$(id -g)" \
    autofix-sanbox bash -lc "pytest -q --maxfail=1 --junitxml=/test_results/jnit.xml" \
    > "$HOST_RUN_DIR/test_results/test.log" 2>&1 || true


# Run the container and remove it after it exits
# Mount the repo and test_results directories
# Set the working directory to /repo
# Run pytest with specified options
# Redirect output to test.log  backend/runs/b1bff0df-9c35-4b4b-a5c0-ea447611e856

