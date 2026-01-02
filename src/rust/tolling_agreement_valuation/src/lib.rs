#[cfg(feature = "python")]
use crate::cli::{CalculateProfitArgs, SamplePathsArgs};
#[cfg(feature = "python")]
use crate::commands::calculate_profit::CalculateProfitCommand;
#[cfg(feature = "python")]
use crate::commands::sample_prices::SamplePricesCommand;

#[cfg(feature = "python")]
use numpy::PyArray3;
#[cfg(feature = "python")]
use pyo3::prelude::*;

// This exposes the modules to the library so they are compiled in
pub mod cli;
pub mod commands;
pub mod data;
pub mod data_reader;
pub mod engine;
pub mod processes;

/// Python Wrapper for Calculate Profit
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(name = "calculate_profit")]
pub fn calculate_profit_py(
    gas_curve: String,
    power_curve: String,
    model_params: String,
    unit_params: String,
    num_paths: usize,
) -> PyResult<f64> {
    let args = CalculateProfitArgs {
        gas_curve,
        power_curve,
        model_params,
        unit_params,
        num_paths,
    };

    let result = CalculateProfitCommand::execute(args)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(result)
}

/// Python Wrapper for Sample Prices
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(name = "sample_prices")]
pub fn sample_prices_py<'py>(
    py: Python<'py>,
    gas_curve: String,
    power_curve: String,
    model_params: String,
    num_paths: usize,
) -> PyResult<Bound<'py, PyArray3<f64>>> {
    // 1. Convert Python args to your Rust Struct
    let args = SamplePathsArgs {
        gas_curve,
        power_curve,
        model_params,
        num_paths,
    };

    // Run your logic
    // Assuming execute returns your SimulationResult struct
    let result = SamplePricesCommand::execute(args)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    // 3. Convert Rust ndarray -> Python NumPy Array
    let np_array = result.into_pyarray(py);

    Ok(np_array)
}

#[cfg(feature = "python")]
#[pymodule]
fn tolling_agreement_valuation(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_profit_py, m)?)?;
    m.add_function(wrap_pyfunction!(sample_prices_py, m)?)?;
    Ok(())
}
