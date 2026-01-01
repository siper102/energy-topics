use anyhow::{anyhow, Result};
use ndarray::{Array1, ArrayViewMut2, Axis, Zip};

// Struct that provides a function to transform pure gaussian noise eps
// to a geometric brownian motion at time points 1 / eps.len()
// It calculates the solution of the following sde:
// dX_{t} = \mu(t) X_{t} dt + \sigma X_{t} dW_{t}
// which has the closed-form solution
// X_{t} = F(t) * \exp(-\frac{1}{2} \sigma^{2} t + \sigma W_{t})
pub struct GeometricBrownianMotionTransformer;

impl GeometricBrownianMotionTransformer {
    // do the transformation inplace to avoid copy, allocation, ...
    pub fn transform_to_gbm(
        f: &Array1<f64>,
        sigma: f64,
        n_points: usize,
        mut eps: ArrayViewMut2<f64>,
    ) -> Result<()> {
        if f.len() != n_points {
            return Err(anyhow!("Length mismatch"));
        }

        let dt = 1.0 / ((n_points - 1) as f64);
        let dt_sqrt = dt.sqrt();

        // Step 1: Noise -> Path
        Self::cumulative_sum(eps.view_mut(), Axis(1));

        // Step 2: Path -> Price
        let t = Array1::linspace(0.0, 1.0, n_points);
        let drift_term = -0.5 * sigma.powi(2);

        for mut row in eps.outer_iter_mut() {
            Zip::from(&mut row).and(&t).and(f).for_each(|e, &t_i, &f| {
                let w_t = *e * dt_sqrt;

                *e = f * (drift_term * t_i + sigma * w_t).exp();
            });
        }
        Ok(())
    }

    // Transform the gaussian noise to wiener process by calculating the cumsum
    fn cumulative_sum(mut eps: ArrayViewMut2<f64>, axis: Axis) {
        let t_max = eps.len_of(axis);
        for t in 1..t_max {
            let (prev, mut curr) = eps.view_mut().split_at(axis, t);
            let prev = prev.index_axis(axis, t - 1);
            let mut curr = curr.index_axis_mut(axis, 0);
            Zip::from(&mut curr).and(&prev).for_each(|c, &p| *c += p);
        }
    }
}
