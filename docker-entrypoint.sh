#!/bin/bash
set -e

# Start cron in the background
echo "Starting cron service..."
cron

# Start the FastAPI application with uvicorn
echo "Starting FastAPI application..."

# If DEBUG is set, start with debugpy
if [ "$DEBUG" = "1" ]; then
    echo "Starting in DEBUG mode with debugpy on port 5678..."
    exec python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
