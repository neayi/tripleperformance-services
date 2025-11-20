#!/bin/bash
set -e

# Start cron in the background
echo "Starting cron service..."
cron

# Start the FastAPI application with uvicorn
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
