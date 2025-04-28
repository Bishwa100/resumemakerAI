# Resume Maker CLI wrapper script for Windows
# This script provides an easy way to run the resume maker CLI tools

# Set the base directory to where this script is located
$BASE_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PYTHON_PATH = $BASE_DIR

# Ensure we have the virtual environment
if (Test-Path -Path ".venv") {
    # Activate virtual environment
    try {
        if (Test-Path -Path ".venv\Scripts\Activate.ps1") {
            . ".venv\Scripts\Activate.ps1"
            Write-Host "Activated virtual environment"
        } else {
            Write-Host "Warning: Virtual environment activation script not found"
        }
    } catch {
        Write-Host "Error activating virtual environment: $_"
    }
} else {
    Write-Host "Warning: Virtual environment not found. Commands may not work correctly."
    Write-Host "Consider creating a virtual environment with: python -m venv .venv"
}

# Set the PYTHONPATH environment variable
$env:PYTHONPATH = $PYTHON_PATH

# Execute the command
try {
    python -m resumemaker.cli $args
    $EXIT_CODE = $LASTEXITCODE
} catch {
    Write-Host "Error executing command: $_"
    $EXIT_CODE = 1
}

# Deactivate virtual environment if it was activated
if ($env:VIRTUAL_ENV) {
    deactivate
}

exit $EXIT_CODE 