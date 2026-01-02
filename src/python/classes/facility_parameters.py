import dataclasses
from dataclasses import dataclass
from typing import Dict

@dataclass
class FacilityParameters:
    """
    Physical and economic parameters for a single power generation unit.
    """
    
    heat_rate: float
    """Efficiency of the unit (MMBtu of gas required to produce 1 MWh of electricity)."""
    
    capacity: float
    """Maximum power output of the unit in MW (or MWh per hour)."""
    
    start_up_costs: float
    """Fixed cost incurred every time the unit is started (in EUR)."""

    def to_dict(self) -> Dict:
        """Converts the parameters to a dictionary."""
        return dataclasses.asdict(self)
    
    @staticmethod
    def from_dict(dictionary: Dict) -> "FacilityParameters":
        """Creates a FacilityParameters instance from a dictionary."""
        return FacilityParameters(**dictionary)
