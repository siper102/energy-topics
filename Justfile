# Justfile for Energy Trading Collection

# Use uv for python execution
python := "uv run python"

# Default recipe
default: setup data

# Install dependencies and build Rust extension
setup:
    @echo "Syncing dependencies and building Rust extension..."
    uv sync

# Generate input parameters and forward curves
data:
    @echo "Generating data..."
    PYTHONPATH=src/python {{python}} src/python/write_stochastic_parameters.py
    PYTHONPATH=src/python {{python}} src/python/write_facility_parameters.py
    PYTHONPATH=src/python {{python}} src/python/write_forward_curves.py

# Start Jupyter Lab
notebook:
    @echo "Starting Jupyter Lab..."
    # Ensure src/python is in PYTHONPATH so the notebook can import models
    PYTHONPATH=src/python uv run --with jupyter jupyter lab src/python/notebooks/valuation_tutorial.ipynb

# Clean build artifacts
clean:
    rm -rf src/rust/tolling_agreement_valuation/target
    rm -rf data/facility/*.json
    rm -rf data/parameters/*.json
    rm -rf data/forward-curve/*.csv
    find . -type d -name "__pycache__" -exec rm -rf {} +
    rm -rf .venv
