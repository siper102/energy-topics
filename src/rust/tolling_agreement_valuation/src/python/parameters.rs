use crate::core::parameters::{ModelParameters, UnitParameter};
use num_traits::{Float, FromPrimitive};
use pyo3::prelude::*;

/// A Python-compatible wrapper for the stochastic model parameters.
///
/// This struct is exposed to Python as the `ModelParameters` class. It holds all parameters
/// as `f64` and can be converted into the generic `ModelParameters<T>` used by the core
/// Rust logic.
#[pyclass(name = "ModelParameters")]
#[derive(Clone, Debug)]
pub struct PyModelParameters {
    /// Volatility of the gas price process (in percent).
    #[pyo3(get, set)]
    pub sigma_g: f64,
    /// Volatility of the power price process (in percent).
    #[pyo3(get, set)]
    pub sigma_p: f64,
    /// Mean reversion speed of the power price process (unitless).
    #[pyo3(get, set)]
    pub kappa: f64,
    /// The average number of jumps per day in the power price (jumps / day).
    #[pyo3(get, set)]
    pub lambda_j: f64,
    /// The mean size of a jump in the power price (€ / MWh).
    #[pyo3(get, set)]
    pub mu_j: f64,
    /// The standard deviation of the jump size in the power price (€ / MWh).
    #[pyo3(get, set)]
    pub sigma_j: f64,
    /// The correlation between the gas and power price processes.
    #[pyo3(get, set)]
    pub rho: f64,
}

#[pymethods]
impl PyModelParameters {
    /// Creates a new instance of the ModelParameters class.
    ///
    /// This is the constructor (`__init__` in Python) for the class.
    #[new]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        sigma_g: f64,
        sigma_p: f64,
        kappa: f64,
        lambda_j: f64,
        mu_j: f64,
        sigma_j: f64,
        rho: f64,
    ) -> Self {
        Self {
            sigma_g,
            sigma_p,
            kappa,
            lambda_j,
            mu_j,
            sigma_j,
            rho,
        }
    }
}

impl PyModelParameters {
    /// Converts the Python-facing `f64` parameters to the generic `ModelParameters<T>`.
    ///
    /// This is a crucial step to allow the core Rust functions to be generic over the
    /// number type `T`, which can be `f64` for simulation or `AADVar` for differentiation.
    pub fn to_domain<T: Float + FromPrimitive>(&self) -> ModelParameters<T> {
        ModelParameters {
            sigma_g: T::from_f64(self.sigma_g).unwrap(),
            sigma_p: T::from_f64(self.sigma_p).unwrap(),
            kappa: T::from_f64(self.kappa).unwrap(),
            lambda_j: T::from_f64(self.lambda_j).unwrap(),
            mu_j: T::from_f64(self.mu_j).unwrap(),
            sigma_j: T::from_f64(self.sigma_j).unwrap(),
            rho: T::from_f64(self.rho).unwrap(),
        }
    }
}

/// A Python-compatible wrapper for the power generation unit parameters.
///
/// This struct is exposed to Python as the `UnitParameter` class.
#[pyclass(name = "UnitParameter")]
#[derive(Clone, Debug)]
pub struct PyUnitParameter {
    /// The efficiency of the unit (MWh / MMBtu).
    #[pyo3(get, set)]
    pub heat_rate: f64,
    /// The maximum power output (MWh).
    #[pyo3(get, set)]
    pub capacity: f64,
    /// The fixed cost to start the unit (€).
    #[pyo3(get, set)]
    pub start_up_costs: f64,
}

#[pymethods]
impl PyUnitParameter {
    /// Creates a new instance of the UnitParameter class.
    ///
    /// This is the constructor (`__init__` in Python) for the class.
    #[new]
    pub fn new(heat_rate: f64, capacity: f64, start_up_costs: f64) -> Self {
        Self {
            heat_rate,
            capacity,
            start_up_costs,
        }
    }
}

impl PyUnitParameter {
    /// Converts the Python-facing `f64` parameters to the generic `UnitParameter<T>`.
    pub fn to_domain<T: Float + FromPrimitive>(&self) -> UnitParameter<T> {
        UnitParameter {
            heat_rate: T::from_f64(self.heat_rate).unwrap(),
            capacity: T::from_f64(self.capacity).unwrap(),
            start_up_costs: T::from_f64(self.start_up_costs).unwrap(),
        }
    }
}
