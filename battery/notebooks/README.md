# Notebooks

This directory contains Jupyter notebooks for data analysis, model evaluation, and experimentation.

## Setup

This directory is managed by [uv](https://github.com/astral-sh/uv). 

To set up the environment:

1.  **Install dependencies**:
    ```bash
    uv sync
    ```

2.  **Run Jupyter Lab/Notebook**:
    You can run Jupyter within the `uv` environment:
    ```bash
    uv run jupyter lab
    ```
    (Note: You might need to add `jupyterlab` to the dependencies if you want to run it directly from here, or use a global installation that points to this venv's kernel.)

## Adding Dependencies

To add new packages to the notebook environment:
```bash
uv add <package-name>
```

## Notebooks

- `price_spread_analysis.ipynb`: Analysis of energy price spreads.
- `model_evaluation.ipynb`: Evaluation of machine learning models.
