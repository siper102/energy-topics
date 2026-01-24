use num_traits::{Float, FromPrimitive};
use crate::core::parameters::{ModelParameters, UnitParameter};
use pyo3::prelude::*;

#[pyclass(name = "ModelParameters")]
#[derive(Clone, Debug)]
pub struct PyModelParameters {
    #[pyo3(get, set)]
    pub sigma_g: f64,
    #[pyo3(get, set)]
    pub sigma_p: f64,
    #[pyo3(get, set)]
    pub kappa: f64,
    #[pyo3(get, set)]
    pub lambda_j: f64,
    #[pyo3(get, set)]
    pub mu_j: f64,
    #[pyo3(get, set)]
    pub sigma_j: f64,
    #[pyo3(get, set)]
    pub rho: f64,
}

#[pymethods]
impl PyModelParameters {
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

#[pyclass(name = "UnitParameter")]
#[derive(Clone, Debug)]
pub struct PyUnitParameter {
    #[pyo3(get, set)]
    pub heat_rate: f64,
    #[pyo3(get, set)]
    pub capacity: f64,
    #[pyo3(get, set)]
    pub start_up_costs: f64,
}

#[pymethods]
impl PyUnitParameter {
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
    pub fn to_domain<T: Float + FromPrimitive>(&self) -> UnitParameter<T> {
        UnitParameter {
            heat_rate: T::from_f64(self.heat_rate).unwrap(),
            capacity: T::from_f64(self.capacity).unwrap(),
            start_up_costs: T::from_f64(self.start_up_costs).unwrap(),
        }
    }
}
