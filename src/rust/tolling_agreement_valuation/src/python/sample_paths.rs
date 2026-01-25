//! # DEPRECATED: This module is no longer used and is a candidate for removal.
//!
//! The `sample_paths` service has been superseded by the more direct `Simulator::simulate`
//! method, which is called from the `valuation_tutorial.ipynb` notebook. This file
//! remains for historical purposes but should be deleted.

use crate::core::services::sample_paths::{sample_paths, SamplePathsArgs};
use crate::python::parameters::PyModelParameters;
use numpy::{PyArray3, PyReadonlyArray1};
use pyo3::{pyfunction, Bound, PyErr, PyResult, Python};

/// Python Wrapper for Sample Prices
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(name = "sample_prices")]
pub fn sample_prices_py<'py>(
    py: Python<'py>,
    gas_curve: PyReadonlyArray1<f64>,
    power_curve: PyReadonlyArray1<f64>,
    model_params: PyModelParameters,
    num_paths: usize,
) -> PyResult<Bound<'py, PyArray3<f64>>> {
    // 1. Convert Python args to your Rust Struct
    let args = SamplePathsArgs {
        gas_curve: gas_curve.as_array().to_owned(),
        power_curve: power_curve.as_array().to_owned(),
        model_params: model_params.to_domain(),
        num_paths,
    };

    // Run your logic
    // Assuming execute returns your SimulationResult struct
    let result = sample_paths(args)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    // 3. Convert Rust ndarray -> Python NumPy Array
    let np_array = result.into_pyarray(py);

    Ok(np_array)
}
