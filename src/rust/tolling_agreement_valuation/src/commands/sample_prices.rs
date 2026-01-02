use crate::cli::SamplePathsArgs;
use crate::data::market_data::MarketData;
use crate::processes::simulate_prices::Simulator;
use crate::processes::simulation_result::SimulationResult;
use anyhow::Result;

pub struct SamplePricesCommand;

impl SamplePricesCommand {
    pub fn execute(args: SamplePathsArgs) -> Result<SimulationResult> {
        // 1. Load Market Data
        let market_data = MarketData::load(
            &args.gas_curve,
            &args.power_curve,
            &args.model_params,
        )?;

        // 2. Simulate prices
        let prices = Simulator::simulate(
            &market_data.gas_curve,
            &market_data.power_curve,
            &market_data.model_params,
            args.num_paths,
        )?;

        Ok(prices)
    }
}
