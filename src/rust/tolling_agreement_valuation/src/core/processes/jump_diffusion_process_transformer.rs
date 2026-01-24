use ndarray::{Array1, ArrayViewMut1};
use ndarray_rand::rand::prelude::ThreadRng;
use ndarray_rand::rand::Rng;
use ndarray_rand::rand_distr::{Distribution, Poisson, StandardNormal};
use num_traits::{Float, FromPrimitive};

// Struct that provides functions to transform pure gaussian noise to a Mean-Reverting Jump Diffusion (MRJD).
// It samples from the process: X_{t} = F(t) * \exp(V_{t})
// Where V_{t} is the solution for:
// dV_t = -\kappa V_t dt + \sigma dW_t + J dN_t - \lambda(E[exp(J)] - 1)dt
// Where J is normal and N_{t} is a Poisson process with intensity \lambda.
pub struct JumpDiffusionProcessTransformer;

impl JumpDiffusionProcessTransformer {
    #[inline(always)]
    pub fn transform_path_to_ou<T: Float + FromPrimitive>(
        sigma_p: T,
        kappa: T,
        mu_j: T,
        sigma_j: T,
        dt: T,
        dt_sqrt: T,
        jump_drift_correction: T,
        poisson_dist: &Poisson<f64>,
        mut path: ArrayViewMut1<T>,
        rng: &mut ThreadRng,
    ) {
        let n_points = path.len();
        // Weiner process starts at 0 at time 0.
        path[0] = T::zero();
        for t in 1..n_points {
            let p = path[t - 1];
            let dw = path[t] * dt_sqrt;
            let jump_val = Self::sample_jump(rng, poisson_dist, mu_j, sigma_j);
            let dx = -kappa * p * dt + sigma_p * dw + jump_val - jump_drift_correction;
            path[t] = p + dx;
        }
    }

    #[inline(always)]
    pub fn transform_path_to_jdp<T: Float + FromPrimitive>(
        f: &Array1<T>,
        sigma_p: T,
        kappa: T,
        lambda_j: T,
        mu_j: T,
        sigma_j: T,
        mut path: ArrayViewMut1<T>,
        rng: &mut ThreadRng,
    ) {
        let n_points = path.len();
        let dt_val = 1.0 / n_points as f64;
        let dt = T::from_f64(dt_val).unwrap();
        let dt_sqrt = dt.sqrt();
        
        let half = T::from_f64(0.5).unwrap();
        let drift_term = (mu_j + half * sigma_j.powi(2)).exp() - T::one();
        let jump_drift_correction = lambda_j * dt * drift_term;
        
        // Poisson parameter must be f64. Using to_f64() implies we treat lambda as constant for RNG intensity.
        let lambda_f64 = lambda_j.to_f64().unwrap();
        let poisson_dist = Poisson::new(lambda_f64 * dt_val).unwrap();

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
    fn sample_jump<T: Float + FromPrimitive>(rng: &mut ThreadRng, poisson: &Poisson<f64>, mu: T, sigma: T) -> T {
        let n_jumps = poisson.sample(rng);

        if n_jumps > 0.0 {
            let n_jumps_t = T::from_f64(n_jumps).unwrap();
            let z: f64 = rng.sample(StandardNormal);
            let z_t = T::from_f64(z).unwrap();
            
            (mu * n_jumps_t) + (z_t * (sigma * n_jumps_t.sqrt()))
        } else {
            T::zero()
        }
    }
}
