#!/bin/bash

# Resume Maker CLI wrapper script
# This script provides an easy way to run the resume maker CLI tools

# Set the base directory to where this script is located
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH="$BASE_DIR"

# Ensure we have the virtual environment
if [ -d ".venv" ]; then
    # Activate virtual environment
    source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null
    echo "Activated virtual environment"
else
    echo "Warning: Virtual environment not found. Commands may not work correctly."
    echo "Consider creating a virtual environment with: python -m venv .venv"
fi

# Export the PYTHONPATH
export PYTHONPATH=$PYTHON_PATH

# Execute the command
python -m resumemaker.cli "$@"

# Check the exit code
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "Command failed with exit code $EXIT_CODE"
fi

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

exit $EXIT_CODE 