use crate::core::services::calculate_greeks::{calculate_greeks, CalculateGreeksArgs, GreeksResult};
use crate::python::parameters::{PyModelParameters, PyUnitParameter};
use numpy::{IntoPyArray, PyArray1, PyReadonlyArray1};
use pyo3::{pyclass, pyfunction, Py, PyErr, PyResult, Python};

/// Calculates the Greeks (sensitivities) of the tolling agreement value.
///
/// This function is a Python wrapper around the core Rust `calculate_greeks` implementation.
/// It uses Algorithmic Automatic Differentiation (AAD) in batch mode to efficiently
/// compute the derivatives of the portfolio value with respect to market data and model
/// parameters.
///
/// Parameters
/// ----------
/// gas_curve : numpy.ndarray
///     A 1D NumPy array representing the forward curve for gas prices.
/// power_curve : numpy.ndarray
///     A 1D NumPy array representing the forward curve for power prices.
/// model_params : ModelParameters
///     An instance of the `ModelParameters` class containing parameters for the
///     stochastic models.
/// unit_params : list[UnitParameter]
///     A list of `UnitParameter` objects defining the power generation units.
/// num_paths : int
///     The number of Monte Carlo simulation paths to run for the calculation.
/// risk_free_rate : float
///     The annual risk-free rate for discounting profits.
///
/// Returns
/// -------
/// GreeksResult
///     An object containing the calculated Greeks as NumPy arrays and floats.
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
    // 1. Convert Python inputs to the core Rust domain types.
    let args = CalculateGreeksArgs {
        gas_curve: gas_curve.as_array().to_owned(),
        power_curve: power_curve.as_array().to_owned(),
        model_params: model_params.to_domain(),
        unit_params: unit_params.iter().map(|p| p.to_domain()).collect(),
        num_paths,
        risk_free_rate,
    };

    // 2. Call the core Rust function.
    let greeks_result = calculate_greeks(&args)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    // 3. Convert the Rust result back to a Python-compatible type.
    let py_result = PyGreeksResult::from_domain(greeks_result, py);
    Ok(py_result)
}

/// A Python class to hold the results of the greeks calculation.
///
/// Attributes
/// ----------
/// delta_power : numpy.ndarray
///     The sensitivity of the portfolio value to changes in the power forward curve.
/// delta_gas : numpy.ndarray
///     The sensitivity of the portfolio value to changes in the gas forward curve.
/// vega_power : float
///     The sensitivity of the portfolio value to changes in the power price volatility.
/// vega_gas : float
///     The sensitivity of the portfolio value to changes in the gas price volatility.
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

impl PyGreeksResult {
    /// Creates a `PyGreeksResult` from a core `GreeksResult`.
    fn from_domain(domain: GreeksResult, py: Python) -> Self {
        Self {
            delta_power: domain.delta_power.into_pyarray(py).unbind(),
            delta_gas: domain.delta_gas.into_pyarray(py).unbind(),
            vega_power: domain.vega_power,
            vega_gas: domain.vega_gas,
        }
    }
}
