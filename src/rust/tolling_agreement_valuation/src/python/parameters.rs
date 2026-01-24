use crate::core::parameters::ModelParameters;
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
    #[pyo3(get, set)]
    pub r: f64,
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
        r: f64,
    ) -> Self {
        Self {
            sigma_g,
            sigma_p,
            kappa,
            lambda_j,
            mu_j,
            sigma_j,
            rho,
            r,
        }
    }
}

impl PyModelParameters {
    pub fn to_domain(&self) -> ModelParameters<f64> {
        ModelParameters {
            sigma_g: self.sigma_g,
            sigma_p: self.sigma_p,
            kappa: self.kappa,
            lambda_j: self.lambda_j,
            mu_j: self.mu_j,
            sigma_j: self.sigma_j,
            rho: self.rho,
            r: self.r,
        }
    }
}
