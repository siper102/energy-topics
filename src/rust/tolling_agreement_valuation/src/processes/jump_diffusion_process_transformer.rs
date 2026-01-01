use anyhow::{anyhow, Result};
use ndarray::{Array1, ArrayViewMut2, Axis, Zip};
use ndarray_rand::rand::prelude::ThreadRng;
use ndarray_rand::rand::{thread_rng, Rng};
use ndarray_rand::rand_distr::{Distribution, Poisson, StandardNormal};

// Struct that provides a function to transform pure gaussian noise eps
// to a martingale transformed ornstein-uhlenbeck-jump-process at time points 1 / eps.len()
// It samples from the process:
// $X_{t} = f(t) * \exp{V_{t}}$
// Where $V_{t}$ is the solution for:
// $dV_t = {} & -\kappa V_t dt + \sigma dW_t + J dN_t - \lambda\left(\mathbb E[e^{J}] - 1\right)dt$
// Where J is normal and $N_{t}$ is a poisson process with intensity $\lambda$.
// The sample is created using Euler-Maruyama
pub struct JumpDiffusionProcessTransformer;

impl JumpDiffusionProcessTransformer {
    pub fn transform_to_jdp(
        f: &Array1<f64>,
        sigma_p: f64,
        kappa: f64,
        lambda_j: f64,
        mu_j: f64,
        sigma_j: f64,
        mut eps: ArrayViewMut2<f64>,
    ) -> Result<()> {
        eps.index_axis_mut(Axis(1), 0).fill(0.0);
        Self::transform_to_ou_sample(sigma_p, kappa, lambda_j, mu_j, sigma_j, eps.view_mut())?;
        Self::transform_to_process(&f, eps.view_mut())?;
        Ok(())
    }

    #[inline(always)]
    fn transform_to_ou_sample(
        sigma_p: f64,
        kappa: f64,
        lambda_j: f64,
        mu_j: f64,
        sigma_j: f64,
        mut eps: ArrayViewMut2<f64>,
    ) -> Result<()> {
        let n_points = eps.len_of(Axis(1));
        let dt = 1.0 / n_points as f64;
        let dt_sqrt = dt.sqrt();

        let jump_drift_correction = lambda_j * dt * ((mu_j + 0.5 * sigma_j.powi(2)).exp() - 1.0);
        let poisson_dist = Poisson::new(lambda_j * dt)?;

        let mut rng = thread_rng();

        for t in 1..n_points {
            let (prev_slice, mut curr_slice) = eps.view_mut().split_at(Axis(1), t);
            let prev_col = prev_slice.index_axis(Axis(1), t - 1);
            let mut curr_col = curr_slice.index_axis_mut(Axis(1), 0);

            Zip::from(&mut curr_col).and(&prev_col).for_each(|c, &p| {
                // Extract complex jump logic to inline helper
                let jump_val = Self::sample_jump(&mut rng, &poisson_dist, mu_j, sigma_j);

                let dw = *c * dt_sqrt;
                let dx = -kappa * p * dt + sigma_p * dw + jump_val - jump_drift_correction;

                *c = p + dx;
            });
        }
        Ok(())
    }

    #[inline(always)]
    fn sample_jump(rng: &mut ThreadRng, poisson: &Poisson<f64>, mu: f64, sigma: f64) -> f64 {
        // Sample Poisson (integer number of jumps)
        let n_jumps = poisson.sample(rng);

        if n_jumps > 0.0 {
            let z: f64 = rng.sample(StandardNormal);
            // transform to Normal distribution
            (mu * n_jumps) + (z * (sigma * n_jumps.sqrt()))
        } else {
            0.0
        }
    }

    #[inline(always)]
    fn transform_to_process(
        forward_curve: &Array1<f64>,
        mut paths: ArrayViewMut2<f64>,
    ) -> Result<()> {
        if forward_curve.len() != paths.len_of(Axis(1)) {
            return Err(anyhow!("Forward curve length mismatch"));
        }
        // X_t = F(t) * exp(V_t)
        paths.mapv_inplace(f64::exp);
        paths *= forward_curve;
        Ok(())
    }
}
