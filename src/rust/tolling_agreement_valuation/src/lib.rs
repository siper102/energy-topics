#[cfg(feature = "python")]
use crate::python::parameters::{PyModelParameters, PyUnitParameter};
#[cfg(feature = "python")]
use crate::python::calculate_profit::calculate_daily_profits_py;
#[cfg(feature = "python")]
use crate::python::calculate_greeks::{calculate_greeks_py, PyGreeksResult};
#[cfg(feature = "python")]
use crate::python::sample_paths::sample_prices_py;
#[cfg(feature = "python")]
use pyo3::prelude::*;

// This exposes the modules to the library so they are compiled in
mod core;
#[cfg(feature = "python")]
pub mod python;

#[cfg(feature = "python")]
#[pymodule]
fn tolling_agreement_valuation(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_daily_profits_py, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_greeks_py, m)?)?;
    m.add_function(wrap_pyfunction!(sample_prices_py, m)?)?;
    m.add_class::<PyModelParameters>()?;
    m.add_class::<PyUnitParameter>()?;
    m.add_class::<PyGreeksResult>()?;
    Ok(())
}
