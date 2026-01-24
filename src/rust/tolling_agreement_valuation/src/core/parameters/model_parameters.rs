use serde::Deserialize;

#[derive(Debug, Deserialize, Clone)]
pub struct ModelParameters<T> {
    // Volatility of gas price (in percent)
    pub sigma_g: T,
    // Volatility of power price (in percent)
    pub sigma_p: T,
    // mean reversion speed (unitless)
    pub kappa: T,
    // number of jumps per day (jumps / day)
    pub lambda_j: T,
    // mean jump height of power price (€ / mwh)
    pub mu_j: T,
    // variance of jump height (€ / mwh)
    pub sigma_j: T,
    // correlation of gas- and power prices (€ / mwh^2)
    pub rho: T,
}

impl<T> ModelParameters<T> {
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
