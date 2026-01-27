use aad::{backward, clear_tape, get_tape_len, AADVar};
use ndarray::Array1;
use num_traits::Zero;
use rayon::prelude::*;

use crate::core::common::cholesky::cholesky_2d;
use crate::core::parameters::{ModelParameters, UnitParameter};
use crate::core::simulator::simulate_prices::{Simulator, TollingAssetIndex};
use crate::core::valuation::profit_and_loss::ProfitCalculator;
use anyhow::Result;

/// A tuple representing the greeks calculated for a single path.
/// Contents are: (delta_gas, delta_power, vega_gas, vega_power).
type PathGreeks = (Array1<f64>, Array1<f64>, f64, f64);

/// Calculates the Greeks (sensitivities) of the tolling agreement value.
///
/// This function uses Algorithmic Automatic Differentiation (AAD) to compute the derivatives
/// of the total portfolio value with respect to model and market parameters. It orchestrates
/// the calculation in parallel across many simulation paths.
///
/// The process follows a map-reduce pattern:
/// 1.  **Map**: For each path, `calculate_greeks_for_path` is called. This function performs
///     the full simulation and valuation for one path using `AADVar` types and runs the
///     backward AAD pass to get the path-specific gradients.
/// 2.  **Reduce**: The gradients from all paths are summed together.
///
/// Finally, the summed gradients are averaged to produce the final reported Greeks.
///
/// # Arguments
///
/// * `args`: A reference to `CalculateGreeksArgs` containing all necessary input parameters.
pub fn calculate_greeks(args: &CalculateGreeksArgs) -> Result<GreeksResult> {
    let num_paths = args.num_paths;

    // Use a parallel map-reduce approach.
    // Each task runs `calculate_greeks_for_path`, which handles the AAD tape locally,
    // ensuring thread safety.
    let (total_delta_gas, total_delta_power, total_vega_gas, total_vega_power) = (0..num_paths)
        .into_par_iter()
        .map(|_| calculate_greeks_for_path(args))
        .reduce(
            || {
                // Identity for the reduction: zero-filled arrays and zero scalars.
                (
                    Array1::zeros(args.gas_curve.raw_dim()),
                    Array1::zeros(args.power_curve.raw_dim()),
                    0.0,
                    0.0,
                )
            },
            // The reduction operation: element-wise sum for arrays and standard sum for scalars.
            |a, b| (a.0 + b.0, a.1 + b.1, a.2 + b.2, a.3 + b.3),
        );

    // Average the gradients by the number of paths.
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

/// Performs the full forward and backward AAD pass to calculate greeks for a single path.
///
/// This function encapsulates the entire logic for one Monte Carlo path in the AAD context:
/// 1.  Clears the thread-local AAD tape.
/// 2.  Promotes all input parameters from `f64` to `AADVar`.
/// 3.  Simulates the price paths for gas and power.
/// 4.  Calculates the total discounted profit (NPV) for the path.
/// 5.  Triggers the backward AAD pass to compute adjoints (gradients).
/// 6.  Extracts the relevant gradients (Deltas and Vegas) from the tape.
fn calculate_greeks_for_path(args: &CalculateGreeksArgs) -> PathGreeks {
    // 1. AAD Tape Management: Start with a fresh, empty tape for this thread.
    clear_tape();

    // 2. AAD Variable Initialization: Register all inputs as constants on the tape.
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

    // 3. Simulation using AAD variables.
    let l = cholesky_2d(model_params_aad.rho);
    let assets = Simulator::simulate_single_path(
        &gas_curve_aad,
        &power_curve_aad,
        &model_params_aad,
        &l,
    );

    // 4. Valuation: Calculate the profit for the simulated path.
    let n_points = gas_curve_aad.len();
    let path_gas = assets.row(TollingAssetIndex::Gas.idx());
    let path_power = assets.row(TollingAssetIndex::Power.idx());
    let daily_profits = ProfitCalculator::calculate_single_path(
        &path_gas,
        &path_power,
        &unit_params_aad,
        risk_free_rate_aad,
        n_points / 24, // Assuming hourly resolution
    );

    // 5. Aggregation: Sum daily profits to get the total NPV for the path.
    // This `total_value` is the final node in our computation graph.
    let total_value: AADVar = daily_profits.iter().fold(AADVar::zero(), |acc, x| acc + *x);

    // 6. Backward Pass: Trigger the core AAD operation.
    // We set the derivative of the final value with respect to itself to 1.
    let tape_len = get_tape_len();
    let mut adjoints = vec![0.0; tape_len];
    adjoints[total_value.index] = 1.0;
    backward(&mut adjoints);

    // 7. Gradient Extraction: Read the computed derivatives from the adjoints vector.
    // The index of each AADVar points to its location in the adjoints vector.
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

/// Arguments required for the `calculate_greeks` function.
pub struct CalculateGreeksArgs {
    /// The forward curve for gas prices.
    pub gas_curve: Array1<f64>,
    /// The forward curve for power prices.
    pub power_curve: Array1<f64>,
    /// Parameters for the stochastic models.
    pub model_params: ModelParameters<f64>,
    /// Parameters defining the power generation units.
    pub unit_params: Vec<UnitParameter<f64>>,
    /// The number of Monte Carlo simulation paths to run.
    pub num_paths: usize,
    /// The annual risk-free rate for discounting.
    pub risk_free_rate: f64,
}

/// Holds the results of the greeks calculation.
pub struct GreeksResult {
    /// Delta with respect to the gas forward curve.
    pub delta_gas: Array1<f64>,
    /// Delta with respect to the power forward curve.
    pub delta_power: Array1<f64>,
    /// Vega with respect to the gas price volatility (`sigma_g`).
    pub vega_gas: f64,
    /// Vega with respect to the power price volatility (`sigma_p`).
    pub vega_power: f64,
}