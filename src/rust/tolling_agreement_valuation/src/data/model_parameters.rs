use serde::Deserialize;

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[derive(Debug, Deserialize, Clone)]
#[cfg_attr(feature = "python", pyclass(get_all, set_all))]
pub struct ModelParameters {
    // Volatility of gas price (in percent)
    pub sigma_g: f64,
    // Volatility of power price (in percent)
    pub sigma_p: f64,
    // mean reversion speed (unitless)
    pub kappa: f64,
    // number of jumps per day (jumps / day)
    pub lambda_j: f64,
    // mean jump height of power price (€ / mwh)
    pub mu_j: f64,
    // variance of jump height (€ / mwh)
    pub sigma_j: f64,
    // correlation of gas- and power prices (€ / mwh^2)
    pub rho: f64,
    // Risk-free interest
    pub r: f64,
}

#[cfg(feature = "python")]
#[pymethods]
impl ModelParameters {
    #[new]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        sigma_g: f64,
        sigma_p: f64,
        kappa: f64,
        lambda_j: f64,
        mu_j: f64,
        sigma_j: f64,
        rho: f64,
        r: f64,
    ) -> Self {
        ModelParameters {
            sigma_g,
            sigma_p,
            kappa,
            lambda_j,
            mu_j,
            sigma_j,
            rho,
            r,
        }
    }
}
