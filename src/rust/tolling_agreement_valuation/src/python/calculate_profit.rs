use crate::core::parameters::UnitParameter;
use crate::core::services::calculate_profit::{calculate_daily_profits, CalculateProfitArgs};
use crate::python::parameters::PyModelParameters;
use numpy::{IntoPyArray, PyArray2, PyReadonlyArray1};
use pyo3::{pyfunction, Bound, PyErr, PyResult, Python};

/// Python Wrapper for Calculate Daily Profits
/// Returns a (num_paths, num_days) matrix of non-discounted daily profits
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(name = "calculate_daily_profits")]
pub fn calculate_daily_profits_py<'py>(
    py: Python<'py>,
    gas_curve: PyReadonlyArray1<f64>,
    power_curve: PyReadonlyArray1<f64>,
    model_params: PyModelParameters,
    unit_params: Vec<UnitParameter>,
    num_paths: usize,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let args = CalculateProfitArgs {
        gas_curve: gas_curve.as_array().to_owned(),
        power_curve: power_curve.as_array().to_owned(),
        model_params: model_params.to_domain(),
        unit_params,
        num_paths,
    };

    let result = calculate_daily_profits(args)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(result.into_pyarray(py))
}
