use crate::cli::CalculateProfitArgs;
use crate::engine::calculate_profit::ProfitCalculator;
use crate::data::market_data::MarketData;
use crate::data::unit_parameters::UnitParameter;
use crate::processes::simulate_prices::Simulator;
use anyhow::Result;

pub struct CalculateProfitCommand;

impl CalculateProfitCommand {
    pub fn execute(args: CalculateProfitArgs) -> Result<f64> {
        // 1. Load Market Data
        let market_data = MarketData::load(
            &args.gas_curve,
            &args.power_curve,
            &args.model_params,
        )?;

        // 2. Load Unit Parameters
        let unit_parameters = UnitParameter::from_json_file(&args.unit_params)?;

        // 3. Simulate prices
        let prices = Simulator::simulate(
            &market_data.gas_curve,
            &market_data.power_curve,
            &market_data.model_params,
            args.num_paths,
        )?;

        // 4. Calculate Profit
        let profit = ProfitCalculator::calculate_profit(
            &prices, 
            &unit_parameters, 
            &market_data.model_params.r
        )?;

        Ok(profit)
    }
}
