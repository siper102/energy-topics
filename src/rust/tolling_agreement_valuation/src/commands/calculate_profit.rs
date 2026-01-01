use crate::cli::CalculateProfitArgs;
use crate::engine::calculate_profit::ProfitCalculator;
use crate::data::data_reader::DataReader;
use crate::processes::simulate_prices::Simulator;
use anyhow::Result;

pub struct CalculateProfitCommand;

impl CalculateProfitCommand {
    pub fn execute(args: CalculateProfitArgs) -> Result<f64> {
        // 1. Initialize Components (Using the args struct)
        let reader = DataReader::new(
            &args.gas_curve,
            &args.power_curve,
            &args.model_params,
            &args.unit_params,
        );

        // 2. Load Data (Bubbling context errors up)
        let gas_forward_curve = reader.read_gas_forward_curve()?;
        let power_forward_curve = reader.read_power_forward_curve()?;
        let model_parameters = reader.read_model_parameters()?;
        let unit_parameters = reader.read_unit_parameters()?;

        // 3. Simulate prices
        let prices = Simulator::simulate(
            &gas_forward_curve,
            &power_forward_curve,
            &model_parameters,
            args.num_paths,
        )?;
        // 3. Call the Core Engine
        // (Notice: The engine doesn't know about CLI args, just Arrays/Structs)
        let profit =
            ProfitCalculator::calculate_profit(&prices, &unit_parameters, &model_parameters.r)?;
        Ok(profit)
    }
}
