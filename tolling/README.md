# Tolling Agreement Valuation Model

This repository contains the **Tolling Agreement Valuation Model**, a core component of the broader Energy Trading Collection. This project combines Python for high-level analysis and interactive exploration with a high-performance Rust backend for computationally intensive tasks.

## What is a Tolling Agreement?

A tolling agreement is a contract where a party (the "Tolling Party") supplies fuel (e.g., Natural Gas) to a power plant and, in return, receives the electricity generated. The Tolling Party pays a "toll" for the conversion service, but owns the input fuel and the output power.

The intrinsic value of this agreement is driven by the **Spark Spread**: the difference between the market price of electricity and the cost of the natural gas required to produce it. This model values the optionality of running the power plant when the spark spread is favorable.

## Quantitative Description

The model employs Monte Carlo simulation to generate future price scenarios for the underlying commodities (Natural Gas and Electricity).

-   **Price Sampling**:
    -   **Natural Gas ($G_t$)**: Modeled using a Geometric Brownian Motion (GBM) process, suitable for commodities with a stochastic, trending behavior.
    -   **Electricity ($P_t$)**: Modeled using a Mean-Reverting Jump Diffusion (MRJD) process, capturing the characteristic spikes and mean-reverting tendencies of electricity prices, in addition to stochastic jumps.
    -   **Correlation**: The stochastic drivers of Gas and Power prices are correlated, reflecting their economic interdependency.

-   **Profit Calculation**:
    Daily profits are calculated based on the simulated spark spread, which is the difference between the revenue from selling electricity and the cost of purchasing natural gas, adjusted for the plant's heat rate (efficiency). The model also incorporates operational constraints and costs of the power plant, such as start-up costs, to determine the optimal dispatch strategy (when to run the plant) and thus the resulting profits for each simulated path.

## Project Structure

-   `src/python/`: Contains Python scripts, including the main Jupyter notebook for valuation analysis (`valuation_tutorial.ipynb`) and Python model wrappers (`models/tolling.py`).
-   `src/rust/tolling_agreement_valuation/`: The Rust crate implementing the core valuation logic. This provides the performance-critical calculations.
-   `rust-crates/aad/`: An auxiliary Rust crate likely used by the `tolling_agreement_valuation` crate, possibly for automatic differentiation or similar functionalities.
-   `latex/`: LaTeX source files and generated PDF documentation for the tolling agreement.
-   `Justfile`: Defines convenient commands for project setup, building, and running.

## Getting Started

### Prerequisites

-   Rust (install via `rustup`)
-   Python 3.13+
-   `uv` (install via `pip install uv`)
-   `just` (install via `cargo install just`)

### Setup

To set up the development environment, including installing Python dependencies and building the Rust backend, navigate to the `tolling` directory and run:

```bash
just setup
```

This command will:
1.  Synchronize Python dependencies using `uv`.
2.  Build the `tolling_agreement_valuation` Rust crate.

### Running the Jupyter Notebook

To launch Jupyter Lab and open the valuation tutorial notebook, run:

```bash
just notebook
```

This will open `src/python/valuation_tutorial.ipynb` in your browser, allowing you to interact with the model and perform analyses.

## Tutorial: `valuation_tutorial.ipynb`

The Jupyter notebook provides a comprehensive, step-by-step guide to valuing a tolling agreement using this framework. The key steps covered are:

1.  **Model Setup**: Configuring the financial models (e.g., GBM for Gas, MRJD for Power) and loading market data like forward curves.
2.  **Monte Carlo Simulation**: Generating thousands of possible future price scenarios for gas and power using the high-performance Rust engine.
3.  **Profit Calculation**: Determining the daily profit for each simulated scenario based on the spark spread and the plant's operational constraints.
4.  **Present Value (PV) Calculation**: Discounting the future profits to arrive at the total present value of the agreement, providing a clear valuation figure.
5.  **Risk Analysis**: Analyzing the distribution of profits and the PV to understand the contract's risk profile.
6.  **Greeks Calculation**: Using Adjoint Algorithmic Differentiation (AAD) to efficiently calculate the "Greeks" (e.g., Delta and Vega), which measure the contract's sensitivity to changes in market parameters.

## Development

### Rust Backend

The core performance-critical calculations are implemented in Rust. The `tolling_agreement_valuation` crate is exposed to Python via `maturin`.

### Python Interface

The `src/python/models/tolling.py` file likely contains the Python object-oriented interface (`ValuationModel` ABC and `TollingModel` wrapper) that interacts with the Rust backend.

## Documentation

Detailed mathematical and conceptual documentation for the tolling agreement valuation can be found in the `latex/tolling-agreement.pdf` file.
