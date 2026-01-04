#[cfg(feature = "python")]
use crate::commands::calculate_profit::{CalculateProfitArgs, CalculateProfitCommand};
#[cfg(feature = "python")]
use crate::commands::sample_paths::{SamplePathsArgs, SamplePricesCommand};
#[cfg(feature = "python")]
use crate::data::model_parameters::ModelParameters;
#[cfg(feature = "python")]
use crate::data::unit_parameters::UnitParameter;

#[cfg(feature = "python")]
use numpy::{PyArray3, PyReadonlyArray1};
#[cfg(feature = "python")]
use pyo3::prelude::*;

// This exposes the modules to the library so they are compiled in
pub mod commands;
pub mod data;
pub mod engine;
pub mod processes;

/// Python Wrapper for Calculate Profit
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(name = "calculate_profit")]
pub fn calculate_profit_py(
    gas_curve: PyReadonlyArray1<f64>,
    power_curve: PyReadonlyArray1<f64>,
    model_params: ModelParameters,
    unit_params: Vec<UnitParameter>,
    num_paths: usize,
) -> PyResult<f64> {
    let args = CalculateProfitArgs {
        gas_curve: gas_curve.as_array().to_owned(),
        power_curve: power_curve.as_array().to_owned(),
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
    gas_curve: PyReadonlyArray1<f64>,
    power_curve: PyReadonlyArray1<f64>,
    model_params: ModelParameters,
    num_paths: usize,
) -> PyResult<Bound<'py, PyArray3<f64>>> {
    // 1. Convert Python args to your Rust Struct
    let args = SamplePathsArgs {
        gas_curve: gas_curve.as_array().to_owned(),
        power_curve: power_curve.as_array().to_owned(),
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
    m.add_class::<ModelParameters>()?;
    m.add_class::<UnitParameter>()?;
    Ok(())
}
