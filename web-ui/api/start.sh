#!/bin/bash
# Start the FastAPI backend bridge

# Change to the API directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the server
echo "Starting Hypr-Voice Web UI Bridge on http://localhost:8080"
python bridge.py

