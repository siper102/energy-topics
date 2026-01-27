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

/// An index enum to provide clear, type-safe access to asset data in arrays.
#[repr(usize)]
#[derive(Debug, Copy, Clone)]
pub enum TollingAssetIndex {
    /// The index corresponding to the Gas asset.
    Gas = 0,
    /// The index corresponding to the Power asset.
    Power = 1,
}

impl TollingAssetIndex {
    /// Returns the `usize` representation of the enum variant.
    pub fn idx(self) -> usize {
        self as usize
    }
}

/// A stateless struct that serves as a namespace for simulation functions.
pub struct Simulator;

impl Simulator {
    /// Simulates multiple price paths for all assets in parallel.
    ///
    /// # Arguments
    ///
    /// * `forward_curve_gas`: The forward curve for gas prices.
    /// * `forward_curve_power`: The forward curve for power prices.
    /// * `model_parameters`: The parameters for the stochastic models.
    /// * `num_paths`: The total number of simulation paths to generate.
    ///
    /// # Returns
    ///
    /// A `Result` containing a `SimulationResult`, which wraps the simulated price data
    /// in an `Array3` of shape `(num_paths, num_assets, num_points)`.
    pub fn simulate<T>(
        forward_curve_gas: &Array1<T>,
        forward_curve_power: &Array1<T>,
        model_parameters: &ModelParameters<T>,
        num_paths: usize,
    ) -> Result<SimulationResult<T>>
    where
        T: Float + FromPrimitive + Send + Sync + 'static,
    {
        // Pre-calculate the Cholesky matrix once to be shared across all parallel tasks.
        // This is a performance optimization.
        let l = cholesky_2d(model_parameters.rho);

        // Run the path simulations in parallel.
        // The `map` operation creates a simulation for each path index.
        // The `collect` operation gathers the results from all parallel tasks into a Vec.
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

        // After collection, stack the individual 2D path arrays into a single 3D array.
        // This is more memory-intensive than writing to a pre-allocated array but allows
        // for a cleaner functional pattern (map-collect).
        let n_assets = 2;
        let n_points = forward_curve_gas.len();
        let mut prices = Array3::<T>::zeros((num_paths, n_assets, n_points));
        for (i, path) in paths.iter().enumerate() {
            prices.index_axis_mut(Axis(0), i).assign(path);
        }

        Ok(SimulationResult::new(prices))
    }

    /// Simulates a single price path for both gas and power.
    ///
    /// This function performs the following steps:
    /// 1. Generates standard normal random noise for both assets.
    /// 2. Applies the Cholesky decomposition to correlate the noise.
    /// 3. Transforms the correlated noise into a GBM process for gas.
    /// 4. Transforms the correlated noise into a MRJD process for power.
    ///
    /// # Returns
    ///
    /// An `Array2` of shape `(num_assets, num_points)` containing the simulated prices.
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
        let mut rng = rand::thread_rng();

        // 1. Generate independent standard normal noise.
        // The source of randomness is always f64, which is then cast to type T.
        let z_f64 = Array2::random_using((2, n_points), StandardNormal, &mut rng);
        let z = z_f64.mapv(|x| T::from_f64(x).unwrap());

        // 2. Correlate the noise using the pre-calculated Cholesky matrix.
        let correlated = cholesky_l.dot(&z);

        // Allocate a buffer for the path results.
        let mut assets = Array2::zeros((2, n_points));
        let (mut gas_part, mut power_part) = assets.view_mut().split_at(Axis(0), 1);
        let mut gas_path = gas_part.index_axis_mut(Axis(0), 0);
        let mut power_path = power_part.index_axis_mut(Axis(0), 0);

        // Overwrite the asset buffer with the correlated noise before transformation.
        gas_path.assign(&correlated.index_axis(Axis(0), 0));
        power_path.assign(&correlated.index_axis(Axis(0), 1));

        // 3. Transform the gas path noise into a GBM process.
        GeometricBrownianMotionTransformer::transform_path_to_gbm(
            forward_curve_gas,
            model_parameters.sigma_g,
            n_points,
            gas_path.view_mut(),
        );

        // 4. Transform the power path noise into a Mean-Reverting Jump Diffusion process.
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

