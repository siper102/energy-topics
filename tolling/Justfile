# Justfile for Energy Trading Collection

# Use uv for python execution
python := "uv run python"

# Check code for errors
check:
    cargo check

# Install dependencies and build Rust extension
setup:
    @echo "Syncing dependencies and building Rust extension..."
    uv sync

# Compile Rust extension (Release Mode - Optimized for Performance)
compile:
    @echo "Compiling Rust extension (Release)..."
    cd src/rust/tolling_agreement_valuation && uv run maturin develop --release

# Compile Rust extension (Debug Mode - Faster Compilation)
compile-debug:
    @echo "Compiling Rust extension (Debug)..."
    cd src/rust/tolling_agreement_valuation && uv run maturin develop

# Start Jupyter Lab
notebook:
    @echo "Starting Jupyter Lab..."
    # Ensure src/python is in PYTHONPATH so the notebook can import models
    PYTHONPATH=src/python uv run --with jupyter jupyter lab src/python/notebooks/valuation_tutorial.ipynb

# Clean build artifacts
clean:
    rm -rf src/rust/tolling_agreement_valuation/target
    find . -type d -name "__pycache__" -exec rm -rf {} +
    rm -rf .venv
