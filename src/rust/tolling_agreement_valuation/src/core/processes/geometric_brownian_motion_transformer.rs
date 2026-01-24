use ndarray::{Array1, ArrayViewMut1};
use num_traits::{Float, FromPrimitive};

// Struct that provides functions to transform pure gaussian noise to a Geometric Brownian Motion (GBM).
// It calculates the solution of the following SDE:
// dX_{t} = \mu(t) X_{t} dt + \sigma X_{t} dW_{t}
// which has the closed-form solution:
// X_{t} = F(t) * \exp(-\frac{1}{2} \sigma^{2} t + \sigma W_{t})
pub struct GeometricBrownianMotionTransformer;

impl GeometricBrownianMotionTransformer {
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
        let drift_term = -half * sigma.powi(2);

        let mut w_t = T::zero();
        // At t=0, the noise is 0.0, so exp(...) = 1.0. X_0 = F_0.
        path[0] = f[0];

        for i in 1..n_points {
            w_t = w_t + path[i] * dt_sqrt;
            let t_i = T::from_usize(i).unwrap() * dt;
            let f_i = f[i];
            path[i] = f_i * (drift_term * t_i + sigma * w_t).exp();
        }
    }
}
