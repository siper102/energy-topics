use ndarray::{Array1, ArrayViewMut1};
use ndarray_rand::rand::prelude::ThreadRng;
use ndarray_rand::rand::Rng;
use ndarray_rand::rand_distr::{Distribution, Poisson, StandardNormal};

// Struct that provides functions to transform pure gaussian noise to a Mean-Reverting Jump Diffusion (MRJD).
// It samples from the process: X_{t} = F(t) * \exp(V_{t})
// Where V_{t} is the solution for:
// dV_t = -\kappa V_t dt + \sigma dW_t + J dN_t - \lambda(E[exp(J)] - 1)dt
// Where J is normal and N_{t} is a Poisson process with intensity \lambda.
pub struct JumpDiffusionProcessTransformer;

impl JumpDiffusionProcessTransformer {
    #[inline(always)]
    pub fn transform_path_to_ou(
        sigma_p: f64,
        kappa: f64,
        mu_j: f64,
        sigma_j: f64,
        dt: f64,
        dt_sqrt: f64,
        jump_drift_correction: f64,
        poisson_dist: &Poisson<f64>,
        mut path: ArrayViewMut1<f64>,
        rng: &mut ThreadRng,
    ) {
        let n_points = path.len();
        // Weiner process starts at 0 at time 0.
        path[0] = 0.0;
        for t in 1..n_points {
            let p = path[t - 1];
            let dw = path[t] * dt_sqrt;
            let jump_val = Self::sample_jump(rng, poisson_dist, mu_j, sigma_j);
            let dx = -kappa * p * dt + sigma_p * dw + jump_val - jump_drift_correction;
            path[t] = p + dx;
        }
    }

    #[inline(always)]
    pub fn transform_path_to_jdp(
        f: &Array1<f64>,
        sigma_p: f64,
        kappa: f64,
        lambda_j: f64,
        mu_j: f64,
        sigma_j: f64,
        mut path: ArrayViewMut1<f64>,
        rng: &mut ThreadRng,
    ) {
        let n_points = path.len();
        let dt = 1.0 / n_points as f64;
        let dt_sqrt = dt.sqrt();
        let jump_drift_correction = lambda_j * dt * ((mu_j + 0.5 * sigma_j.powi(2)).exp() - 1.0);
        let poisson_dist = Poisson::new(lambda_j * dt).unwrap();

        Self::transform_path_to_ou(
            sigma_p,
            kappa,
            mu_j,
            sigma_j,
            dt,
            dt_sqrt,
            jump_drift_correction,
            &poisson_dist,
            path.view_mut(),
            rng,
        );

        // Map to process: f * exp(V)
        for i in 0..n_points {
            path[i] = f[i] * path[i].exp();
        }
    }

    #[inline(always)]
    fn sample_jump(rng: &mut ThreadRng, poisson: &Poisson<f64>, mu: f64, sigma: f64) -> f64 {
        let n_jumps = poisson.sample(rng);

        if n_jumps > 0.0 {
            let z: f64 = rng.sample(StandardNormal);
            (mu * n_jumps) + (z * (sigma * n_jumps.sqrt()))
        } else {
            0.0
        }
    }
}
