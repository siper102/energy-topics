use crate::core::parameters::UnitParameter;
use crate::core::simulator::simulate_prices::TollingAssetIndex;
use crate::core::simulator::simulation_result::SimulationResult;
use anyhow::Result;
use ndarray::{Array2, ArrayView1};
use num_traits::{Float, FromPrimitive, Zero};
use rayon::prelude::*;

/// A stateless struct that serves as a namespace for profit calculation functions.
pub struct ProfitCalculator;

impl ProfitCalculator {
    /// Calculates the discounted daily profits for every path in a simulation result.
    ///
    /// This function orchestrates the profit calculation in parallel across all simulation paths.
    ///
    /// # Arguments
    ///
    /// * `simulation_result`: The result of a Monte Carlo simulation.
    /// * `unit_parameters`: A slice of `UnitParameter` structs defining the power units.
    /// * `risk_free_rate`: The annual risk-free rate for discounting.
    ///
    /// # Returns
    ///
    /// A `Result` containing a 2D array of shape `(num_paths, num_days)` with the
    /// discounted daily profits for each path and each day.
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

        // Process each path in parallel using `flat_map` to collect all daily profits
        // into a single Vec.
        let daily_profits: Vec<T> = (0..num_paths)
            .into_par_iter()
            .flat_map(|path_idx| {
                let path_gas = gas_prices.row(path_idx);
                let path_power = power_prices.row(path_idx);

                Self::calculate_single_path(
                    &path_gas,
                    &path_power,
                    unit_parameters,
                    risk_free_rate,
                    n_days,
                )
            })
            .collect();

        // Reshape the flat Vec of profits into a 2D array.
        Array2::from_shape_vec((num_paths, n_days), daily_profits)
            .map_err(|e| anyhow::anyhow!("Failed to reshape daily profits: {}", e))
    }

    /// Calculates the discounted daily profits for a single simulation path.
    ///
    /// For each day, this function calculates the total profit from all generation units
    /// based on an optimal dispatch decision (i.e., only run a unit if it's profitable
    /// for that day). The daily profit is then discounted to present value.
    ///
    /// # Arguments
    ///
    /// * `gas_prices`: A 1D view of the simulated hourly gas prices for the path.
    /// * `power_prices`: A 1D view of the simulated hourly power prices for the path.
    /// * `unit_parameters`: A slice of `UnitParameter` structs defining the power units.
    /// * `risk_free_rate`: The annual risk-free rate for discounting.
    /// * `n_days`: The number of days in the simulation path.
    ///
    /// # Returns
    ///
    /// A `Vec<T>` where each element is the discounted profit for a single day.
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

            // Calculate the profit for each generation unit for the current day.
            for unit in unit_parameters {
                let mut unit_day_gross = T::zero();
                for hour_of_day in 0..24 {
                    let h = day_offset + hour_of_day;
                    let p = power_prices[h];
                    let g = gas_prices[h];
                    // Profit for one hour = (Power Price - Gas Cost) * Capacity
                    let hourly_profit = (p - (unit.heat_rate * g)) * unit.capacity;
                    unit_day_gross = unit_day_gross + hourly_profit;
                }

                // The net profit for the unit is the gross profit minus startup costs.
                let unit_day_net = unit_day_gross - unit.start_up_costs;

                // Optimal dispatch decision: only add the unit's profit if it's positive.
                if unit_day_net > T::zero() {
                    daily_profit = daily_profit + unit_day_net;
                }
            }

            // Discount the total daily profit to its present value.
            // The time `t` is represented in years.
            // We use `day + 1` because the first day's cash flow occurs at the end of day 1.
            let t = T::from_usize(day + 1).unwrap() / T::from_f64(365.0).unwrap();
            let discount_factor = (-risk_free_rate * t).exp();

            path_daily_profits.push(daily_profit * discount_factor);
        }
        path_daily_profits
    }
}
