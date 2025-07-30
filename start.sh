#!/bin/bash
# Startup script for Digital Ocean App Platform

# Set default port if not provided
export PORT=${PORT:-8000}

# Log startup info
echo "Starting IBAN Calculator API..."
echo "Port: $PORT"
echo "Environment: ${CHROME_HEADLESS:-true}"
echo "Python Path: $PYTHONPATH"

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 65