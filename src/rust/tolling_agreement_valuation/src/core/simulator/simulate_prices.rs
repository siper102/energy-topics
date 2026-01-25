use anyhow::Result;
use ndarray::{Array1, Array2, Array3, Axis};
use ndarray_rand::rand;
use ndarray_rand::rand_distr::num_traits::{Float, FromPrimitive};
use ndarray_rand::rand_distr::StandardNormal;
use ndarray_rand::RandomExt;
use rayon::prelude::*;

use crate::core::common::cholesky::cholesky_2d;
use crate::core::parameters::ModelParameters;
use crate::core::processes::geometric_brownian_motion_transformer::GeometricBrownianMotionTransformer;
use crate::core::processes::jump_diffusion_process_transformer::JumpDiffusionProcessTransformer;
use crate::core::simulator::simulation_result::SimulationResult;

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
    pub fn simulate<T>(
        forward_curve_gas: &Array1<T>,
        forward_curve_power: &Array1<T>,
        model_parameters: &ModelParameters<T>,
        num_paths: usize,
    ) -> Result<SimulationResult<T>>
    where
        T: Float + FromPrimitive + Send + Sync + 'static,
    {
        // 1. Pre-calculate Cholesky for correlation
        let l = cholesky_2d(model_parameters.rho);

        // 2. Parallel simulation over paths using map-collect
        let paths: Vec<Array2<T>> = (0..num_paths)
            .into_par_iter()
            .map(|_| {
                Self::simulate_single_path(
                    forward_curve_gas,
                    forward_curve_power,
                    model_parameters,
                    &l,
                )
            })
            .collect();

        // 3. Stack the collected paths into a single Array3
        let n_assets = 2;
        let n_points = forward_curve_gas.len();
        let mut prices = Array3::<T>::zeros((num_paths, n_assets, n_points));
        for (i, path) in paths.iter().enumerate() {
            prices.index_axis_mut(Axis(0), i).assign(path);
        }

        Ok(SimulationResult::new(prices))
    }

    /// Simulates a single path for all assets and returns it.
    pub fn simulate_single_path<T>(
        forward_curve_gas: &Array1<T>,
        forward_curve_power: &Array1<T>,
        model_parameters: &ModelParameters<T>,
        cholesky_l: &Array2<T>,
    ) -> Array2<T>
    where
        T: Float + FromPrimitive + 'static,
    {
        let n_points = forward_curve_gas.len();
        let mut rng = rand::rng();

        // Correlated noise: (2, n_points)
        let z_f64 = Array2::random_using((2, n_points), StandardNormal, &mut rng);
        let z = z_f64.mapv(|x| T::from_f64(x).unwrap());

        let correlated = cholesky_l.dot(&z);

        // Allocate buffer for the path
        let mut assets = Array2::zeros((2, n_points));
        let (mut gas_part, mut power_part) = assets.view_mut().split_at(Axis(0), 1);
        let mut gas_path = gas_part.index_axis_mut(Axis(0), 0);
        let mut power_path = power_part.index_axis_mut(Axis(0), 0);

        // Assign noise to paths
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

        assets
    }
}

