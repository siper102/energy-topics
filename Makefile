# Makefile for Energy Trading Collection

PYTHON := python
MATURIN := maturin
RUST_DIR := src/rust/tolling_agreement_valuation

.PHONY: all build data clean help

all: build data

help:
	@echo "Available commands:"
	@echo "  make build   - Build the Rust extension (release mode) and install it"
	@echo "  make data    - Generate input parameters and forward curves"
	@echo "  make clean   - Remove build artifacts and generated data"

build:
	cd $(RUST_DIR) && $(MATURIN) develop --release

data:
	$(PYTHON) src/python/write_stochastic_parameters.py
	$(PYTHON) src/python/write_facility_parameters.py
	$(PYTHON) src/python/write_forward_curves.py

clean:
	rm -rf $(RUST_DIR)/target
	rm -rf data/facility/*.json
	rm -rf data/parameters/*.json
	rm -rf data/forward-curve/*.csv
	find . -type d -name "__pycache__" -exec rm -rf {} +
