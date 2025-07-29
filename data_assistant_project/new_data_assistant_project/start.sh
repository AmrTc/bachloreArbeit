#!/bin/bash

# Simple startup script for Data Assistant
# This script can be used for local development or simple deployment

echo "🚀 Starting Data Assistant..."

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.12 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing/updating requirements..."
pip install -r requirements.txt

# Set PYTHONPATH
export PYTHONPATH=$(pwd)

# Create necessary directories
mkdir -p data/user_profiles
mkdir -p evaluation/results
mkdir -p logs

# Start the application
echo "Starting Streamlit application..."
streamlit run frontend/app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true

echo "Application stopped." 