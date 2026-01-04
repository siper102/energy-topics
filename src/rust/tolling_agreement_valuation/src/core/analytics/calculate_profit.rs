use crate::core::parameters::UnitParameter;
use crate::core::simulator::simulate_prices::TollingAssetIndex;
use crate::core::simulator::simulation_result::SimulationResult;
use anyhow::Result;
use ndarray::Array1;
use rayon::prelude::*;

pub struct ProfitCalculator;

impl ProfitCalculator {
    pub fn calculate_profit(
        simulation_result: &SimulationResult,
        unit_parameters: &[UnitParameter],
        interest_rate: &f64,
    ) -> Result<f64> {
        let num_paths = simulation_result.num_paths();
        let num_hours = simulation_result.num_points();
        let n_days = num_hours / 24;

        let gas_prices = simulation_result.get_asset_data(TollingAssetIndex::Gas.idx());
        let power_prices = simulation_result.get_asset_data(TollingAssetIndex::Power.idx());

        // 1. Pre-calculate discount factors (constant across paths)
        let discount_factors = Array1::from_shape_fn(n_days, |day| {
            let t = (day as f64 + 1.0) / 365.0;
            (-interest_rate * t).exp()
        });

        // 2. Calculate NPV per path in parallel
        let total_npv: f64 = (0..num_paths)
            .into_par_iter()
            .map(|path_idx| {
                let mut path_npv = 0.0;

                for day in 0..n_days {
                    let mut daily_profit = 0.0;
                    let df = discount_factors[day];
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
                    path_npv += daily_profit * df;
                }
                path_npv
            })
            .sum();

        Ok(total_npv / (num_paths as f64))
    }
}
