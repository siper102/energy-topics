use crate::core::parameters::ModelParameters;
use crate::core::simulator::simulate_prices::Simulator;
use crate::core::simulator::simulation_result::SimulationResult;
use anyhow::Result;
use ndarray::Array1;

pub fn sample_paths(args: SamplePathsArgs) -> Result<SimulationResult> {
    // 1. Simulate prices
    let prices = Simulator::simulate(
        &args.gas_curve,
        &args.power_curve,
        &args.model_params,
        args.num_paths,
    )?;

    Ok(prices)
}

pub struct SamplePathsArgs {
    pub gas_curve: Array1<f64>,
    pub power_curve: Array1<f64>,
    pub model_params: ModelParameters,
    pub num_paths: usize,
}
