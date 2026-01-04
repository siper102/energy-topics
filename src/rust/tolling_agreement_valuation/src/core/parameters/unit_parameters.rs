use serde::Deserialize;

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[derive(Debug, Deserialize, Clone)]
#[cfg_attr(feature = "python", pyclass(get_all, set_all))]
pub struct UnitParameter {
    // How many MwH can we generate from one BBTU (MwH / BBTU)
    pub heat_rate: f64,
    // How many MwH can be generated (MwH)
    pub capacity: f64,
    // How expensive is the startup (€)
    pub start_up_costs: f64,
}

#[cfg(feature = "python")]
#[pymethods]
impl UnitParameter {
    #[new]
    pub fn new(heat_rate: f64, capacity: f64, start_up_costs: f64) -> Self {
        UnitParameter {
            heat_rate,
            capacity,
            start_up_costs,
        }
    }
}
