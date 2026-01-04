use crate::core::analytics::calculate_profit::ProfitCalculator;
use crate::core::parameters::ModelParameters;
use crate::core::parameters::UnitParameter;
use crate::core::simulator::simulate_prices::Simulator;
use anyhow::Result;
use ndarray::Array1;

// This calculates the profit given forward curves and parameters and returns it as
// a single number
pub fn calculate_profit(args: CalculateProfitArgs) -> Result<f64> {
    // 1. Simulate prices
    let prices = Simulator::simulate(
        &args.gas_curve,
        &args.power_curve,
        &args.model_params,
        args.num_paths,
    )?;

    // 2. Calculate Profit
    let profit =
        ProfitCalculator::calculate_profit(&prices, &args.unit_params, &args.model_params.r)?;

    Ok(profit)
}

pub struct CalculateProfitArgs {
    pub gas_curve: Array1<f64>,
    pub power_curve: Array1<f64>,
    pub model_params: ModelParameters,
    pub unit_params: Vec<UnitParameter>,
    pub num_paths: usize,
}
