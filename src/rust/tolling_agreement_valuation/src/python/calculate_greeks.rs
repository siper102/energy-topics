use crate::core::services::calculate_greeks::{
    calculate_greeks, CalculateGreeksArgs,
};
use crate::python::parameters::{PyModelParameters, PyUnitParameter};
use numpy::{IntoPyArray, PyArray1, PyReadonlyArray1};
use pyo3::{pyclass, pyfunction, Py, PyErr, PyResult, Python};

/// Python Wrapper for Calculate Greeks
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(name = "calculate_greeks")]
pub fn calculate_greeks_py<'py>(
    py: Python<'py>,
    gas_curve: PyReadonlyArray1<f64>,
    power_curve: PyReadonlyArray1<f64>,
    model_params: PyModelParameters,
    unit_params: Vec<PyUnitParameter>,
    num_paths: usize,
    risk_free_rate: f64,
) -> PyResult<PyGreeksResult> {
    
    let args = CalculateGreeksArgs {
        gas_curve: gas_curve.as_array().to_owned(),
        power_curve: power_curve.as_array().to_owned(),
        model_params: model_params.to_domain(),
        unit_params: unit_params.iter().map(|p| p.to_domain()).collect(),
        num_paths,
        risk_free_rate,
    };
    
    let result = calculate_greeks(args)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let py_result = PyGreeksResult {
        delta_power: result.delta_power.into_pyarray(py).unbind(),
        delta_gas: result.delta_gas.into_pyarray(py).unbind(),
        vega_power: result.vega_power,
        vega_gas: result.vega_gas,
    };
    Ok(py_result)
}

#[pyclass(name = "GreeksResult")]
pub struct PyGreeksResult {
    #[pyo3(get)]
    pub delta_power: Py<PyArray1<f64>>,
    #[pyo3(get)]
    pub delta_gas: Py<PyArray1<f64>>,
    #[pyo3(get)]
    pub vega_power: f64,
    #[pyo3(get)]
    pub vega_gas: f64,
}
