"""
Script to generate and save facility parameters to a JSON file.

This script creates a list of `FacilityParameters` objects representing different
power plant units and saves them as a JSON array to `data/facility/parameters.json`.
"""

import json
import pathlib
from typing import List

from classes.facility_parameters import FacilityParameters

# path if data
path = pathlib.Path(__file__).parent.parent.parent.joinpath("data").joinpath("facility")

if __name__ == "__main__":
    path.mkdir(parents=True, exist_ok=True)

    parameters: List[FacilityParameters] = [
        FacilityParameters(
            heat_rate=1.67, 
            capacity=400,
            start_up_costs=15000
        ),
        FacilityParameters(
            heat_rate=3.33,
            capacity=100,
            start_up_costs=2000
        )

    ]

    print(f"Writing facility parameters to {path.joinpath('parameters.json')}")
    with open(path.joinpath("parameters.json"), "w") as f:
        json.dump(list(map(lambda f: f.to_dict(), parameters)), f, indent=4)
