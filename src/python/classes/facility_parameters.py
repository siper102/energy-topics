import dataclasses
from dataclasses import dataclass

@dataclass
class FacilityParameters:
    # Heat rate of the facility (MwH / MMBTU)
    heat_rate: float
    # capacity of the facility (MwH)
    capacity: float
    # costs for startup of facility (€)
    start_up_costs: float

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
    
    @staticmethod
    def from_dict(dictionary: dict) -> "FacilityParameters":
        return FacilityParameters(**dictionary)
