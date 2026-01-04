use ndarray::{Array1, ArrayViewMut1};

// Struct that provides functions to transform pure gaussian noise to a Geometric Brownian Motion (GBM).
// It calculates the solution of the following SDE:
// dX_{t} = \mu(t) X_{t} dt + \sigma X_{t} dW_{t}
// which has the closed-form solution:
// X_{t} = F(t) * \exp(-\frac{1}{2} \sigma^{2} t + \sigma W_{t})
pub struct GeometricBrownianMotionTransformer;

impl GeometricBrownianMotionTransformer {
    #[inline(always)]
    pub fn transform_path_to_gbm(
        f: &Array1<f64>,
        sigma: f64,
        n_points: usize,
        mut path: ArrayViewMut1<f64>,
    ) {
        let dt = 1.0 / ((n_points - 1) as f64);
        let dt_sqrt = dt.sqrt();
        let drift_term = -0.5 * sigma.powi(2);

        let mut w_t = 0.0;
        // At t=0, the noise is 0.0, so exp(...) = 1.0. X_0 = F_0.
        path[0] = f[0];

        for i in 1..n_points {
            w_t += path[i] * dt_sqrt;
            let t_i = (i as f64) * dt;
            let f_i = f[i];
            path[i] = f_i * (drift_term * t_i + sigma * w_t).exp();
        }
    }
}
