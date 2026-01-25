use aad::{backward, clear_tape, get_tape_len, AADVar};
use ndarray::{Array1};
use num_traits::Zero;
use rayon::prelude::*;

use crate::core::common::cholesky::cholesky_2d;
use crate::core::parameters::{ModelParameters, UnitParameter};
use crate::core::simulator::simulate_prices::{Simulator, TollingAssetIndex};
use crate::core::valuation::profit_and_loss::ProfitCalculator;
use anyhow::Result;

type PathGreeks = (Array1<f64>, Array1<f64>, f64, f64);

pub fn calculate_greeks(args: &CalculateGreeksArgs) -> Result<GreeksResult> {
    let num_paths = args.num_paths;

    // We use a parallel map-reduce approach.
    // Each task processes a chunk of paths.
    // Inside the task, we handle AAD completely independently to ensure thread-local tape safety.
    let (total_delta_gas, total_delta_power, total_vega_gas, total_vega_power) = (0..num_paths)
        .into_par_iter()
        .map(|_| calculate_greeks_for_path(args))
        .reduce(
            || {
                (
                    Array1::zeros(args.gas_curve.raw_dim()),
                    Array1::zeros(args.power_curve.raw_dim()),
                    0.0,
                    0.0,
                )
            },
            |a, b| (a.0 + b.0, a.1 + b.1, a.2 + b.2, a.3 + b.3),
        );

    // Average the gradients
    let num_paths_f64 = num_paths as f64;
    let delta_gas = total_delta_gas / num_paths_f64;
    let delta_power = total_delta_power / num_paths_f64;
    let vega_gas = total_vega_gas / num_paths_f64;
    let vega_power = total_vega_power / num_paths_f64;

    let greeks = GreeksResult {
        delta_gas,
        delta_power,
        vega_gas,
        vega_power,
    };
    Ok(greeks)
}

/// Performs the full forward and backward pass to calculate greeks for a single path.
fn calculate_greeks_for_path(args: &CalculateGreeksArgs) -> PathGreeks {
    // 1. Clear Tape for this path (thread-local)
    clear_tape();

    // 2. Initialize Inputs as AADVars (registering them on the fresh local tape)
    let gas_curve_aad = args.gas_curve.mapv(AADVar::constant);
    let power_curve_aad = args.power_curve.mapv(AADVar::constant);

    let model_params_aad = ModelParameters::new(
        AADVar::constant(args.model_params.sigma_g),
        AADVar::constant(args.model_params.sigma_p),
        AADVar::constant(args.model_params.kappa),
        AADVar::constant(args.model_params.lambda_j),
        AADVar::constant(args.model_params.mu_j),
        AADVar::constant(args.model_params.sigma_j),
        AADVar::constant(args.model_params.rho),
    );

    let unit_params_aad: Vec<UnitParameter<AADVar>> = args
        .unit_params
        .iter()
        .map(|p| {
            UnitParameter::new(
                AADVar::constant(p.heat_rate),
                AADVar::constant(p.capacity),
                AADVar::constant(p.start_up_costs),
            )
        })
        .collect();

    let risk_free_rate_aad = AADVar::constant(args.risk_free_rate);

    // 3. Pre-calc Cholesky using the new utility
    let l = cholesky_2d(model_params_aad.rho);

    // 4. Simulate Single Path
    let assets = Simulator::simulate_single_path(
        &gas_curve_aad,
        &power_curve_aad,
        &model_params_aad,
        &l,
    );

    // 5. Calculate Profit Single Path
    let n_points = gas_curve_aad.len();
    let path_gas = assets.row(TollingAssetIndex::Gas.idx());
    let path_power = assets.row(TollingAssetIndex::Power.idx());

    let daily_profits = ProfitCalculator::calculate_single_path(
        &path_gas,
        &path_power,
        &unit_params_aad,
        risk_free_rate_aad,
        n_points / 24, // Assuming hourly resolution, n_days = points / 24
    );

    // 7. Aggregate to Scalar NPV
    let total_value: AADVar = daily_profits.iter().fold(AADVar::zero(), |acc, x| acc + *x);

    // 8. Backward Pass
    let tape_len = get_tape_len();
    let mut adjoints = vec![0.0; tape_len];
    adjoints[total_value.index] = 1.0;

    backward(&mut adjoints);

    // 9. Extract Gradients for this path
    let mut local_delta_gas = Array1::<f64>::zeros(gas_curve_aad.raw_dim());
    let mut local_delta_power = Array1::<f64>::zeros(power_curve_aad.raw_dim());

    for (i, point) in gas_curve_aad.iter().enumerate() {
        local_delta_gas[i] = adjoints[point.index];
    }
    for (i, point) in power_curve_aad.iter().enumerate() {
        local_delta_power[i] = adjoints[point.index];
    }

    let local_vega_gas = adjoints[model_params_aad.sigma_g.index];
    let local_vega_power = adjoints[model_params_aad.sigma_p.index];

    (
        local_delta_gas,
        local_delta_power,
        local_vega_gas,
        local_vega_power,
    )
}

pub struct CalculateGreeksArgs {
    pub gas_curve: Array1<f64>,
    pub power_curve: Array1<f64>,
    pub model_params: ModelParameters<f64>,
    pub unit_params: Vec<UnitParameter<f64>>,
    pub num_paths: usize,
    pub risk_free_rate: f64,
}

pub struct GreeksResult {
    pub delta_gas: Array1<f64>,
    pub delta_power: Array1<f64>,
    pub vega_gas: f64,
    pub vega_power: f64,
}