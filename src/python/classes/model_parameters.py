import dataclasses
from dataclasses import dataclass

@dataclass
class StochasticParameters:
    # Volatility of gas price (in per cent)
    sigma_g: float
    # Volatility of power price (in per cent)
    sigma_p: float
    # mean reversion speed (unitless)
    kappa: float
    # number of jumps per day (jumps / day)
    lambda_j: float
    # mean jump height of power price (€ / mwh)
    mu_j: float
    # variance of jump height (€ / mwh)
    sigma_j: float
    # correlation of gas- and power prices (€ / mwh^2)
    rho: float
    # Risk free interest (% / year)
    r: float

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
    
    @staticmethod
    def from_dict(dictionary: dict) -> "StochasticParameters":
        return StochasticParameters(**dictionary)
