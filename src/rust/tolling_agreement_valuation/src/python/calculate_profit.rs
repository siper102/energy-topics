use crate::core::parameters::ModelParameters;
use crate::core::parameters::UnitParameter;
use crate::core::services::calculate_profit::{calculate_profit, CalculateProfitArgs};
use numpy::PyReadonlyArray1;
use pyo3::{pyfunction, PyErr, PyResult};

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

    let result = calculate_profit(args)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(result)
}
