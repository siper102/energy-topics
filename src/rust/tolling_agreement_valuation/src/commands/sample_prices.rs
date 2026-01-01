use crate::cli::SamplePathsArgs;
use crate::data::data_reader::DataReader;
use crate::processes::simulate_prices::Simulator;
use crate::processes::simulation_result::SimulationResult;
use anyhow::Result;

pub struct SamplePricesCommand;

impl SamplePricesCommand {
    pub fn execute(args: SamplePathsArgs) -> Result<SimulationResult> {
        // 1. Initialize Components (Using the args struct)
        let reader =
            DataReader::new_without_unit(&args.gas_curve, &args.power_curve, &args.model_params);

        // 2. Load Data (Bubbling context errors up)
        let gas_forward_curve = reader.read_gas_forward_curve()?;
        let power_forward_curve = reader.read_power_forward_curve()?;
        let model_parameters = reader.read_model_parameters()?;

        // 3. Simulate prices
        let prices = Simulator::simulate(
            &gas_forward_curve,
            &power_forward_curve,
            &model_parameters,
            args.num_paths,
        )?;

        Ok(prices)
    }
}
