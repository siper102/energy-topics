use crate::core::analytics::calculate_profit::ProfitCalculator;
use crate::core::parameters::ModelParameters;
use crate::core::parameters::UnitParameter;
use crate::core::simulator::simulate_prices::Simulator;
use anyhow::Result;
use ndarray::{Array1, Array2};

// This calculates the daily profits given forward curves and parameters
// Returns a (num_paths, num_days) matrix of non-discounted daily profits
pub fn calculate_daily_profits(args: CalculateProfitArgs) -> Result<Array2<f64>> {
    // 1. Simulate prices
    let prices = Simulator::simulate(
        &args.gas_curve,
        &args.power_curve,
        &args.model_params,
        args.num_paths,
    )?;

    // 2. Calculate Daily Profits
    let daily_profits = ProfitCalculator::calculate_daily_profits(&prices, &args.unit_params)?;

    Ok(daily_profits)
}

pub struct CalculateProfitArgs {
    pub gas_curve: Array1<f64>,
    pub power_curve: Array1<f64>,
    pub model_params: ModelParameters<f64>,
    pub unit_params: Vec<UnitParameter>,
    pub num_paths: usize,
}
