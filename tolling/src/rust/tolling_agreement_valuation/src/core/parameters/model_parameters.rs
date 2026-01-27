use serde::Deserialize;

/// Contains the parameters for the stochastic models used in the simulation.
///
/// This struct holds the parameters that define the behavior of the gas and power
/// price processes. It is generic over the number type `T`, allowing it to be used
/// with both standard floats (`f64`) for simulation and `AADVar` for greeks calculation.
#[derive(Debug, Deserialize, Clone)]
pub struct ModelParameters<T> {
    /// Volatility of the gas price process (in percent).
    pub sigma_g: T,
    /// Volatility of the power price process (in percent).
    pub sigma_p: T,
    /// Mean reversion speed of the power price process (unitless).
    pub kappa: T,
    /// The average number of jumps per day in the power price (jumps / day).
    pub lambda_j: T,
    /// The mean size of a jump in the power price (€ / MWh).
    pub mu_j: T,
    /// The standard deviation of the jump size in the power price (€ / MWh).
    pub sigma_j: T,
    /// The correlation between the gas and power price processes.
    pub rho: T,
}

impl<T> ModelParameters<T> {
    /// Constructs a new `ModelParameters` instance.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        sigma_g: T,
        sigma_p: T,
        kappa: T,
        lambda_j: T,
        mu_j: T,
        sigma_j: T,
        rho: T,
    ) -> Self {
        ModelParameters {
            sigma_g,
            sigma_p,
            kappa,
            lambda_j,
            mu_j,
            sigma_j,
            rho,
        }
    }
}
