#!/bin/bash

# This script provides an easy way to run MetaSpidey.
# It activates the Python virtual environment and starts the application.

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating Python virtual environment..."
    source venv/bin/activate
else
    echo "Warning: Virtual environment 'venv' not found. Running with system Python."
fi

# Run the application
echo "Launching MetaSpidey..."
python3 MetaSpidey/main.py
