use crate::core::parameters::UnitParameter;
use crate::core::simulator::simulate_prices::TollingAssetIndex;
use crate::core::simulator::simulation_result::SimulationResult;
use anyhow::Result;
use ndarray::Array2;
use rayon::prelude::*;

pub struct ProfitCalculator;

impl ProfitCalculator {
    /// Calculate daily profits for each simulation path
    /// Returns a (num_paths, num_days) matrix of non-discounted daily profits
    pub fn calculate_daily_profits(
        simulation_result: &SimulationResult<f64>,
        unit_parameters: &[UnitParameter],
    ) -> Result<Array2<f64>> {
        let num_paths = simulation_result.num_paths();
        let num_hours = simulation_result.num_points();
        let n_days = num_hours / 24;

        let gas_prices = simulation_result.get_asset_data(TollingAssetIndex::Gas.idx());
        let power_prices = simulation_result.get_asset_data(TollingAssetIndex::Power.idx());

        // Calculate daily profits per path in parallel
        let daily_profits: Vec<f64> = (0..num_paths)
            .into_par_iter()
            .flat_map(|path_idx| {
                let mut path_daily_profits = Vec::with_capacity(n_days);

                for day in 0..n_days {
                    let mut daily_profit = 0.0;
                    let day_offset = day * 24;

                    for unit in unit_parameters {
                        let mut unit_day_gross = 0.0;
                        for hour_of_day in 0..24 {
                            let h = day_offset + hour_of_day;
                            // Cache-friendly access: path is fixed, hour varies
                            let p = power_prices[[path_idx, h]];
                            let g = gas_prices[[path_idx, h]];
                            unit_day_gross += (p - (unit.heat_rate * g)) * unit.capacity;
                        }

                        let unit_day_net = unit_day_gross - unit.start_up_costs;
                        if unit_day_net > 0.0 {
                            daily_profit += unit_day_net;
                        }
                    }
                    path_daily_profits.push(daily_profit);
                }
                path_daily_profits
            })
            .collect();

        // Convert to Array2 with shape (num_paths, n_days)
        Array2::from_shape_vec((num_paths, n_days), daily_profits)
            .map_err(|e| anyhow::anyhow!("Failed to reshape daily profits: {}", e))
    }
}
