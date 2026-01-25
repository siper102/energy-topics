use ndarray::{Array1, ArrayViewMut1};
use num_traits::{Float, FromPrimitive};

/// A stateless transformer that converts a path of standard normal random numbers
/// into a path following a Geometric Brownian Motion (GBM) process.
///
/// The transformation is based on the closed-form solution to the GBM
/// stochastic differential equation (SDE):
///
/// `dX_t = mu(t) * X_t * dt + sigma * X_t * dW_t`
///
/// Where the drift `mu(t)` is derived from the forward curve `F(t)`.
pub struct GeometricBrownianMotionTransformer;

impl GeometricBrownianMotionTransformer {
    /// Transforms a path of random noise in-place to follow a GBM process.
    ///
    /// This function implements the closed-form solution for a GBM process driven
    /// by a forward curve `F(t)`:
    ///
    /// `X_t = F(t) * exp(-0.5 * sigma^2 * t + sigma * W_t)`
    ///
    /// Where `W_t` is the cumulative Wiener process at time `t`.
    ///
    /// # Arguments
    ///
    /// * `f`: A reference to an `Array1` representing the forward curve `F(t)`.
    /// * `sigma`: The volatility of the process.
    /// * `n_points`: The number of time steps in the path.
    /// * `path`: A mutable view of an `Array1` containing the standard normal noise.
    ///           The transformation happens in-place, and this buffer is overwritten
    ///           with the resulting GBM path.
    #[inline(always)]
    pub fn transform_path_to_gbm<T: Float + FromPrimitive>(
        f: &Array1<T>,
        sigma: T,
        n_points: usize,
        mut path: ArrayViewMut1<T>,
    ) {
        let dt = T::one() / T::from_usize(n_points - 1).unwrap();
        let dt_sqrt = dt.sqrt();
        let half = T::from_f64(0.5).unwrap();

        // Pre-calculate the constant part of the drift term in the exponent.
        let drift_term = -half * sigma.powi(2);

        // `w_t` will accumulate the Wiener process `W_t = sum(Z_i * sqrt(dt))`.
        // The input `path` contains the standard normal variables `Z_i`.
        let mut w_t = T::zero();

        // At t=0, the noise is 0.0, so exp(...) is 1.0. The price is just the forward price.
        // We set this explicitly as the loop starts from i=1.
        path[0] = f[0];

        // Iterate through the time steps to calculate the price at each point.
        for i in 1..n_points {
            // The Wiener process W_t is the cumulative sum of the scaled noise.
            // path[i] currently holds the random shock Z_i for this step.
            w_t = w_t + path[i] * dt_sqrt;

            let t_i = T::from_usize(i).unwrap() * dt;
            let f_i = f[i];

            // Apply the closed-form solution. The original noise in path[i] is overwritten.
            path[i] = f_i * (drift_term * t_i + sigma * w_t).exp();
        }
    }
}
