use crate::core::parameters::{UnitParameter};
use crate::core::simulator::simulate_prices::TollingAssetIndex;
use crate::core::simulator::simulation_result::SimulationResult;
use anyhow::Result;
use ndarray::{Array2, ArrayView1};
use num_traits::{Float, FromPrimitive};
use rayon::prelude::*;

pub struct ProfitCalculator;

impl ProfitCalculator {
    /// Calculate daily profits for each simulation path with discounting
    /// Returns a (num_paths, num_days) matrix of discounted daily profits
    pub fn calculate_daily_profits<T: Float + FromPrimitive + Send + Sync + 'static>(
        simulation_result: &SimulationResult<T>,
        unit_parameters: &[UnitParameter<T>],
        risk_free_rate: T,
    ) -> Result<Array2<T>> {
        let num_paths = simulation_result.num_paths();
        let num_hours = simulation_result.num_points();
        let n_days = num_hours / 24;

        let gas_prices = simulation_result.get_asset_data(TollingAssetIndex::Gas.idx());
        let power_prices = simulation_result.get_asset_data(TollingAssetIndex::Power.idx());

        // Calculate daily profits per path in parallel
        let daily_profits: Vec<T> = (0..num_paths)
            .into_par_iter()
            .flat_map(|path_idx| {
                // Slice rows for this path
                let path_gas = gas_prices.row(path_idx);
                let path_power = power_prices.row(path_idx);
                
                Self::calculate_single_path(
                    &path_gas,
                    &path_power,
                    unit_parameters,
                    risk_free_rate,
                    n_days
                )
            })
            .collect();

        // Convert to Array2 with shape (num_paths, n_days)
        Array2::from_shape_vec((num_paths, n_days), daily_profits)
            .map_err(|e| anyhow::anyhow!("Failed to reshape daily profits: {}", e))
    }

    /// Calculates discounted daily profits for a single path
    pub fn calculate_single_path<T: Float + FromPrimitive>(
        gas_prices: &ArrayView1<T>,
        power_prices: &ArrayView1<T>,
        unit_parameters: &[UnitParameter<T>],
        risk_free_rate: T,
        n_days: usize,
    ) -> Vec<T> {
        let mut path_daily_profits = Vec::with_capacity(n_days);

        for day in 0..n_days {
            let mut daily_profit = T::zero();
            let day_offset = day * 24;

            for unit in unit_parameters {
                let mut unit_day_gross = T::zero();
                for hour_of_day in 0..24 {
                    let h = day_offset + hour_of_day;
                    let p = power_prices[h];
                    let g = gas_prices[h];
                    unit_day_gross = unit_day_gross + (p - (unit.heat_rate * g)) * unit.capacity;
                }

                let unit_day_net = unit_day_gross - unit.start_up_costs;
                if unit_day_net > T::zero() {
                    daily_profit = daily_profit + unit_day_net;
                }
            }
            
            // Discounting: NPV = Profit * exp(-r * t)
            let t = T::from_usize(day).unwrap() / T::from_f64(365.0).unwrap();
            let discount_factor = (-risk_free_rate * t).exp();
            
            path_daily_profits.push(daily_profit * discount_factor);
        }
        path_daily_profits
    }
}
