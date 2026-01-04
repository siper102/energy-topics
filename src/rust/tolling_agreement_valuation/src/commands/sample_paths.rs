use crate::commands::args::SamplePathsArgs;
use crate::processes::simulate_prices::Simulator;
use crate::processes::simulation_result::SimulationResult;
use anyhow::Result;

pub struct SamplePricesCommand;

impl SamplePricesCommand {
    pub fn execute(args: SamplePathsArgs) -> Result<SimulationResult> {
        // 1. Simulate prices
        let prices = Simulator::simulate(
            &args.gas_curve,
            &args.power_curve,
            &args.model_params,
            args.num_paths,
        )?;

        Ok(prices)
    }
}