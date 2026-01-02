import dataclasses
from dataclasses import dataclass
from typing import Dict

@dataclass
class StochasticParameters:
    """
    Parameters for the stochastic processes used in the tolling agreement valuation.
    """
    
    sigma_g: float
    """Volatility of gas price (annualized, e.g., 0.4 for 40%). Calibrated to GBM."""
    
    sigma_p: float
    """Volatility of power price (annualized). Diffusion component of MRJD."""
    
    kappa: float
    """Mean reversion speed for power prices (unitless). High value means fast reversion."""
    
    lambda_j: float
    """Jump intensity for power prices (expected number of jumps per year)."""
    
    mu_j: float
    """Mean of the log-jump size for power prices."""
    
    sigma_j: float
    """Standard deviation of the log-jump size for power prices."""
    
    rho: float
    """Correlation between the Brownian motions of Gas and Power."""
    
    r: float
    """Risk-free interest rate (annualized, e.g., 0.02 for 2%)."""

    def to_dict(self) -> Dict:
        """Converts the parameters to a dictionary."""
        return dataclasses.asdict(self)
    
    @staticmethod
    def from_dict(dictionary: Dict) -> "StochasticParameters":
        """Creates a StochasticParameters instance from a dictionary."""
        return StochasticParameters(**dictionary)
