"""
Script to generate and save stochastic model parameters to a JSON file.

This script creates a `StochasticParameters` object with defined model parameters
(volatility, mean reversion, jumps, etc.) and saves it as a JSON object to
`data/parameters/parameters.json`.
"""

import json
import pathlib

from classes.model_parameters import StochasticParameters

# path if data
path = pathlib.Path(__file__).parent.parent.parent.joinpath("data").joinpath("parameters")

if __name__ == "__main__":
    path.mkdir(parents=True, exist_ok=True)

    parameters = StochasticParameters(
        sigma_g=0.4,
        sigma_p=0.5,
        kappa=50.0,
        lambda_j=5.0,
        mu_j=0.5,
        sigma_j=0.3,
        rho=0.6,
        r=0.02,
    )

    print(f"Writing stochastic parameters to {path.joinpath('parameters.json')}")
    with open(path.joinpath("parameters.json"), "w") as f:
        json.dump(parameters.to_dict(), f, indent=4)
