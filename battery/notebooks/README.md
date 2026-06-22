# Notebooks

This directory contains Jupyter notebooks for data analysis, model evaluation, and experimentation.

## Setup

The workspace is managed globally by [pixi](https://pixi.sh/). All python dependencies, packages, and system-level solvers (like `ipopt`) are managed via the root `pixi.toml` file.

To run Jupyter Lab:
```bash
pixi run notebook
```

## Adding Dependencies

To add new packages to the environment, use pixi from the root directory:
*   For conda packages: `pixi add <package-name>`
*   For PyPI packages: `pixi add --pypi <package-name>`

## Notebooks

- `price_spread_analysis.ipynb`: Analysis of energy price spreads.
- `model_evaluation.ipynb`: Evaluation of machine learning models.
- `optimization_routine.ipynb`: Demonstration of the stochastic battery dispatch optimization routine with GARCH price spread scenarios.
