use ndarray::{Array1, ArrayViewMut1};
use ndarray_rand::rand::prelude::ThreadRng;
use ndarray_rand::rand::Rng;
use ndarray_rand::rand_distr::{Distribution, Poisson, StandardNormal};
use num_traits::{Float, FromPrimitive};

/// A stateless transformer that converts a path of standard normal random numbers
/// into a path following a Mean-Reverting Jump Diffusion (MRJD) process.
///
/// The final process `X_t` is modeled as `X_t = F(t) * exp(V_t)`, where `F(t)` is the
/// deterministic forward curve and `V_t` is a stochastic component. `V_t` follows
/// an Ornstein-Uhlenbeck process with jumps, governed by the SDE:
///
/// `dV_t = -kappa * V_t * dt + sigma * dW_t + J * dN_t - lambda * (E[exp(J)] - 1) * dt`
///
/// Where:
/// - `kappa` is the mean-reversion speed.
/// - `sigma` is the volatility of the OU process.
/// - `dW_t` is the Wiener process component.
/// - `J` is the jump size, `J ~ N(mu_j, sigma_j^2)`.
/// - `dN_t` is a Poisson process with intensity `lambda`.
/// - The final term is a drift correction to ensure the process is a martingale.
pub struct JumpDiffusionProcessTransformer;

impl JumpDiffusionProcessTransformer {
    /// Transforms a path of random noise in-place to follow the full JDP process.
    ///
    /// This is the main entry point for the transformation. It performs two major steps:
    /// 1. It first transforms the path of standard normal noise into an Ornstein-Uhlenbeck
    ///    process with jumps (`V_t`) using an Euler-Maruyama discretization scheme.
    /// 2. It then applies the final transformation `X_t = F(t) * exp(V_t)` to get the
    ///    final price path.
    ///
    /// # Arguments
    ///
    /// * `f`: The forward curve `F(t)`.
    /// * `sigma_p`: Volatility of the OU process.
    /// * `kappa`: Mean-reversion speed.
    /// * `lambda_j`: Intensity of the Poisson process for jumps.
    /// * `mu_j`: Mean of the jump size distribution.
    /// * `sigma_j`: Standard deviation of the jump size distribution.
    /// * `path`: A mutable view of the standard normal noise, which is overwritten in-place.
    /// * `rng`: A mutable reference to a random number generator.
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
        
        // This term corrects the drift to ensure the process is a martingale.
        // It accounts for the expected value of the log-normal jump size.
        let half = T::from_f64(0.5).unwrap();
        let drift_term = (mu_j + half * sigma_j.powi(2)).exp() - T::one();
        let jump_drift_correction = lambda_j * dt * drift_term;
        
        // The Poisson distribution determines the number of jumps in a time step `dt`.
        // Its parameter (lambda * dt) must be f64.
        let lambda_f64 = lambda_j.to_f64().unwrap();
        let poisson_dist = Poisson::new(lambda_f64 * dt_val).unwrap();

        // First, transform the noise into the OU process `V_t`.
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

        // Finally, map the OU process `V_t` to the final price process `X_t = F(t) * exp(V_t)`.
        for i in 0..n_points {
            path[i] = f[i] * path[i].exp();
        }
    }
    
    /// Simulates the Ornstein-Uhlenbeck with jumps process `V_t` using Euler-Maruyama.
    ///
    /// This function overwrites the input `path` in-place.
    fn transform_path_to_ou<T: Float + FromPrimitive>(
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
        // The OU process `V_t` starts at 0 at time 0.
        path[0] = T::zero();
        for t in 1..n_points {
            let p = path[t - 1];
            // The input `path` contains the standard normal variable Z_t for the Wiener process.
            let dw = path[t] * dt_sqrt;
            let jump_val = Self::sample_jump(rng, poisson_dist, mu_j, sigma_j);
            
            // Euler-Maruyama step for the SDE of V_t.
            let dx = -kappa * p * dt + sigma_p * dw + jump_val - jump_drift_correction;
            path[t] = p + dx;
        }
    }

    /// Samples a single jump value for a given time step.
    ///
    /// The number of jumps is drawn from a Poisson distribution. If one or more jumps
    /// occur, their total size is drawn from a Normal distribution, scaled by the
    /// number of jumps.
    #[inline(always)]
    fn sample_jump<T: Float + FromPrimitive>(rng: &mut ThreadRng, poisson: &Poisson<f64>, mu: T, sigma: T) -> T {
        let n_jumps = poisson.sample(rng);

        if n_jumps > 0.0 {
            // If jumps occur, their total size is the sum of `n_jumps` IID normal variables.
            // Sum of N normals: N*mu, N*sigma^2 variance.
            let n_jumps_t = T::from_f64(n_jumps).unwrap();
            let z: f64 = rng.sample(StandardNormal);
            let z_t = T::from_f64(z).unwrap();
            
            (mu * n_jumps_t) + (z_t * (sigma * n_jumps_t.sqrt()))
        } else {
            // No jumps in this time step.
            T::zero()
        }
    }
}
