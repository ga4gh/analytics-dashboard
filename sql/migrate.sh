#!/bin/bash

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Read command (up/down) from the first argument
CMD=$1

# Validate input
if [[ "$CMD" != "up" && "$CMD" != "down" ]]; then
  echo "Usage: $0 [up|down]"
  exit 1
fi

# Load environment variables from .env file if it exists
if [[ -f .env ]]; then
  export $(grep -v '^#' .env | xargs)
fi

# Ensure DATABASE_URL is set
if [[ -z "$DATABASE_URL" ]]; then
  echo "Error: DATABASE_URL is not set. Define it in .env or export it."
  exit 1
fi

# Check if running in GitHub Actions
if [[ -n "$GITHUB_ACTIONS" ]]; then
  NETWORK=""
else
  NETWORK="--network analytics-dashboard_default"
fi

# Run the migrate container
if [[ "$CMD" == "down" ]]; then
  docker run --rm \
    $NETWORK \
    -v "$SCRIPT_DIR/migrations:/migrations" \
    migrate/migrate \
    -path=/migrations \
    -database="$DATABASE_URL" \
    down 1
else
  echo "Running: docker run --rm $NETWORK -v \"$SCRIPT_DIR/migrations:/migrations\" migrate/migrate -path=/migrations -database=\"$DATABASE_URL\" \"$CMD\""
  docker run --rm \
    $NETWORK \
    -v "$SCRIPT_DIR/migrations:/migrations" \
    migrate/migrate \
    -path=/migrations \
    -database="$DATABASE_URL" \
    "$CMD"
fi
