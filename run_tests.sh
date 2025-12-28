#!/bin/bash
set -e

# Determine python executable
if [ -f "venv/bin/python" ]; then
    PYTHON_EXEC="venv/bin/python"
else
    PYTHON_EXEC="python"
fi

echo "Using Python: $PYTHON_EXEC"
echo "Running Tests..."
$PYTHON_EXEC -m pytest tests/

echo "Done."