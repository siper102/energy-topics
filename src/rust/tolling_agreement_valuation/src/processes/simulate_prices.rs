use crate::data::model_parameters::ModelParameters;
use crate::processes::geometric_brownian_motion_transformer::GeometricBrownianMotionTransformer;
use crate::processes::jump_diffusion_process_transformer::JumpDiffusionProcessTransformer;
use crate::processes::simulation_result::SimulationResult;
use anyhow::Result;
use ndarray::{array, Array1, Array2, Array3, Axis};
use ndarray_linalg::cholesky::Cholesky;
use ndarray_linalg::UPLO;
use ndarray_rand::rand_distr::StandardNormal;
use ndarray_rand::RandomExt;

pub struct Simulator;

impl Simulator {
    pub const IDX_GAS: usize = 0;
    pub const IDX_POWER: usize = 1;

    pub fn simulate(
        forward_curve_gas: &Array1<f64>,
        forward_curve_power: &Array1<f64>,
        model_parameters: &ModelParameters,
        num_paths: usize,
    ) -> Result<SimulationResult> {
        let n_points = forward_curve_gas.len();

        // 1. Generate Correlated Noise
        let mut eps = Self::simulate_noise(model_parameters.rho, num_paths, n_points)?;

        // 2. Map Gas (GBM)
        GeometricBrownianMotionTransformer::transform_to_gbm(
            forward_curve_gas,
            model_parameters.sigma_g,
            n_points,
            eps.index_axis_mut(Axis(0), Self::IDX_GAS),
        )?;

        // 3. Map Power (OU Jump Diffusion)
        JumpDiffusionProcessTransformer::transform_to_jdp(
            forward_curve_power,
            model_parameters.sigma_p,
            model_parameters.kappa,
            model_parameters.lambda_j,
            model_parameters.mu_j,
            model_parameters.sigma_j,
            eps.index_axis_mut(Axis(0), Self::IDX_POWER),
        )?;

        Ok(SimulationResult::new(eps))
    }

    fn simulate_noise(rho: f64, num_paths: usize, num_points: usize) -> Result<Array3<f64>> {
        let sigma = array![[1.0, rho], [rho, 1.0]];
        let l = sigma.cholesky(UPLO::Lower)?;
        let total_samples = num_paths * num_points;
        let z = Array2::random((2, total_samples), StandardNormal);
        let correlated_flat = l.dot(&z);
        let mut correlated_3d = correlated_flat.into_shape((2, num_paths, num_points))?;
        // Since Wiener Process starts at 0 at time 0 a.s.
        correlated_3d.index_axis_mut(Axis(2), 0).fill(0.0);
        Ok(correlated_3d)
    }
}
