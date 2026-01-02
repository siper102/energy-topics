"""
Script to generate and save hourly forward curves for Gas and Power.

Generates synthetic hourly data for 2025 using a simple sine-wave seasonality model
and saves the result as CSV files in `data/forward-curve/`.
"""

import pathlib

import numpy as np
import pandas as pd

# -------------------------------------------------------------------
# Time grid (hourly for 2025)
# -------------------------------------------------------------------
dates = pd.date_range(
    start="2025-01-01 00:00:00",
    end="2025-12-31 23:00:00",
    freq="H"
)

hours = np.arange(len(dates))
t_years = hours / (365.0 * 24.0)  # convert hours to fraction of year

# -------------------------------------------------------------------
# Gas Forward Curve parameters
# -------------------------------------------------------------------
base_price_gas = 3.50
seasonality_gas = 0.50

# -------------------------------------------------------------------
# Power Forward Curve parameters
# -------------------------------------------------------------------
base_price_power = 45
seasonality_power = 10

# -------------------------------------------------------------------
# Data path
# -------------------------------------------------------------------
path = pathlib.Path(__file__).parent.parent.parent.joinpath("data").joinpath("forward-curve")

# -------------------------------------------------------------------
# Forward curve functions
# -------------------------------------------------------------------
def get_FG(t: np.ndarray) -> pd.DataFrame:
    """
    Get the hourly forward curve of gas prices.

    Args:
        t: Array of time points in years.

    Returns:
        pd.DataFrame: DataFrame with 'date' index and 'price' column.
    """
    curve = base_price_gas + seasonality_gas * np.sin(2 * np.pi * t)
    return pd.DataFrame(
        {
            "date": dates,
            "price": curve,
        }
    ).set_index("date")

def get_FP(t: np.ndarray) -> pd.DataFrame:
    """
    Get the hourly forward curve of electricity prices.

    Args:
        t: Array of time points in years.

    Returns:
        pd.DataFrame: DataFrame with 'date' index and 'price' column.
    """
    curve = base_price_power + seasonality_power * np.sin(2 * np.pi * t)
    return pd.DataFrame(
        {
            "date": dates,
            "price": curve,
        }
    ).set_index("date")

# -------------------------------------------------------------------
# Run & export
# -------------------------------------------------------------------
if __name__ == "__main__":
    path.mkdir(parents=True, exist_ok=True)

    gas_forward_curve = get_FG(t_years)
    power_forward_curve = get_FP(t_years)

    print(f"Writing CSV files to {path.absolute()}...")
    gas_forward_curve.to_csv(path.joinpath("gas-forward-hourly.csv"))
    power_forward_curve.to_csv(path.joinpath("power-forward-hourly.csv"))
