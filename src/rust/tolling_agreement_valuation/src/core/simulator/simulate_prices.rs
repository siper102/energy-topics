use crate::core::parameters::ModelParameters;
use crate::core::processes::geometric_brownian_motion_transformer::GeometricBrownianMotionTransformer;
use crate::core::processes::jump_diffusion_process_transformer::JumpDiffusionProcessTransformer;
use crate::core::simulator::simulation_result::SimulationResult;
use anyhow::Result;
use ndarray::{array, Array1, Array2, Array3, Axis};
use ndarray_linalg::cholesky::Cholesky;
use ndarray_linalg::UPLO;
use ndarray_rand::rand::thread_rng;
use ndarray_rand::rand_distr::StandardNormal;
use ndarray_rand::RandomExt;
use rayon::prelude::*;

#[repr(usize)]
#[derive(Debug, Copy, Clone)]
pub enum TollingAssetIndex {
    Gas = 0,
    Power = 1,
}

impl TollingAssetIndex {
    pub fn idx(self) -> usize {
        self as usize
    }
}

pub struct Simulator;

impl Simulator {
    pub fn simulate(
        forward_curve_gas: &Array1<f64>,
        forward_curve_power: &Array1<f64>,
        model_parameters: &ModelParameters,
        num_paths: usize,
    ) -> Result<SimulationResult> {
        let n_points = forward_curve_gas.len();
        let n_assets = 2;

        // 1. Pre-calculate Cholesky for correlation
        let sigma = array![[1.0, model_parameters.rho], [model_parameters.rho, 1.0]];
        let l = sigma.cholesky(UPLO::Lower)?;

        // 2. Allocate output array (prices)
        // Standard Layout: (num_paths, asset_idx, n_points)
        let mut prices = Array3::<f64>::zeros((num_paths, n_assets, n_points));

        // 3. Parallel simulation over paths
        // We iterate over Axis(0) which is num_paths
        prices
            .axis_iter_mut(Axis(0))
            .into_par_iter()
            .for_each(|assets| {
                let mut rng = thread_rng();
                // Correlated noise: (2, n_points)
                let z = Array2::random_using((2, n_points), StandardNormal, &mut rng);
                let correlated = l.dot(&z);

                // Split Asset axis: [Gas, Power]
                let (mut gas_part, mut power_part) = assets.split_at(Axis(0), 1);
                let mut gas_path = gas_part.index_axis_mut(Axis(0), 0);
                let mut power_path = power_part.index_axis_mut(Axis(0), 0);

                // Assign noise to paths (re-using buffer)
                gas_path.assign(&correlated.index_axis(Axis(0), 0));
                power_path.assign(&correlated.index_axis(Axis(0), 1));

                // Transform Gas Path (GBM)
                GeometricBrownianMotionTransformer::transform_path_to_gbm(
                    forward_curve_gas,
                    model_parameters.sigma_g,
                    n_points,
                    gas_path.view_mut(),
                );

                // Transform Power Path (MRJD)
                JumpDiffusionProcessTransformer::transform_path_to_jdp(
                    forward_curve_power,
                    model_parameters.sigma_p,
                    model_parameters.kappa,
                    model_parameters.lambda_j,
                    model_parameters.mu_j,
                    model_parameters.sigma_j,
                    power_path.view_mut(),
                    &mut rng,
                );
            });

        Ok(SimulationResult::new(prices))
    }
}
