import json
from classes.facility_parameters import FacilityParameters
import pathlib

# path if data
path = pathlib.Path(__file__).parent.parent.parent.joinpath("data").joinpath("facility")

if __name__ == "__main__":
    path.mkdir(parents=True, exist_ok=True)

    parameters = [
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

    with open(path.joinpath("parameters.json"), "w") as f:
        json.dump(list(map(lambda f: f.to_dict(), parameters)), f, indent=4)
