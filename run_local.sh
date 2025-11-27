#!/bin/bash

# Script to run the quiz solver locally

echo "Starting LLM Quiz Solver..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file with required variables."
    echo "See .env.example for reference."
    exit 1
fi

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

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

# Run the application
echo "Starting server..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload