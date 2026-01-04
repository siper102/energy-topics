#[cfg(feature = "python")]
use crate::core::parameters::ModelParameters;
#[cfg(feature = "python")]
use crate::core::parameters::UnitParameter;
#[cfg(feature = "python")]
use crate::python::calculate_profit::calculate_profit_py;
#[cfg(feature = "python")]
use crate::python::sample_paths::sample_prices_py;
#[cfg(feature = "python")]
use pyo3::prelude::*;

// This exposes the modules to the library so they are compiled in
mod core;
pub mod python;

#[cfg(feature = "python")]
#[pymodule]
fn tolling_agreement_valuation(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_profit_py, m)?)?;
    m.add_function(wrap_pyfunction!(sample_prices_py, m)?)?;
    m.add_class::<ModelParameters>()?;
    m.add_class::<UnitParameter>()?;
    Ok(())
}
