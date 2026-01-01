use crate::data::unit_parameters::UnitParameter;
use crate::processes::simulation_result::SimulationResult;
use anyhow::Result;
use ndarray::{Array1, Array3, Axis, Zip};

pub struct ProfitCalculator;

impl ProfitCalculator {
    pub fn calculate_profit(
        simulation_result: &SimulationResult,
        unit_parameters: &Vec<UnitParameter>,
        interest_rate: &f64,
    ) -> Result<f64> {
        let num_paths = simulation_result.num_paths();
        let num_hours = simulation_result.num_points();
        let shape = (unit_parameters.len(), num_paths, num_hours);
        let mut pi = Array3::<f64>::zeros(shape);
        let gas_prices = simulation_result.gas_prices();
        let power_prices = simulation_result.power_prices();

        for (unit_idx, mut unit_slice) in pi.axis_iter_mut(Axis(0)).enumerate() {
            let unit = &unit_parameters[unit_idx];
            let hr = unit.heat_rate;
            let cap = unit.capacity;

            Zip::from(&mut unit_slice)
                .and(&power_prices)
                .and(&gas_prices)
                .for_each(|out, &p, &g| {
                    *out = (p - (hr * g)) * cap;
                });
        }

        let n_days = num_hours / 24;
        let n_units = unit_parameters.len();
        // Reshape by day to calculate daily profits
        let reshaped = pi
            .into_shape((n_units, num_paths, n_days, 24))
            .expect("Data layout must be contiguous for reshape");
        // Sum over hours to get daily profits (shape: n_units, num_paths, n_days)
        let mut daily_gross_profit = reshaped.sum_axis(Axis(3));

        for (unit_idx, mut unit_slice) in daily_gross_profit.axis_iter_mut(Axis(0)).enumerate() {
            let k_start = unit_parameters[unit_idx].start_up_costs;
            // max(sum p_i - start, 0)
            unit_slice.mapv_inplace(|val| {
                let net = val - k_start;
                if net > 0.0 { net } else { 0.0 }
            });
        }
        // 1. Reduce [Units, Paths, Days] -> [Paths, Days]
        // This is the correct first step (minimizes operations)
        let path_daily_cashflows = daily_gross_profit.sum_axis(Axis(0));

        // 2. Create Discount Vector [Days]
        let discount_factors = Array1::from_shape_fn(n_days, |d| {
            let t = (d as f64 + 1.0) / 365.0;
            (-interest_rate * t).exp()
        });

        let npv_per_path = path_daily_cashflows.dot(&discount_factors);

        // 4. Final Result
        let profit = npv_per_path.mean().unwrap();
        Ok(profit)
    }
}
