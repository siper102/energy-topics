use crate::data_reader::json_reader::JsonFileReader;
use anyhow::Result;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
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

impl ModelParameters {
    pub fn from_json_file(path: &str) -> Result<Self> {
        JsonFileReader::read(path)
    }
}
