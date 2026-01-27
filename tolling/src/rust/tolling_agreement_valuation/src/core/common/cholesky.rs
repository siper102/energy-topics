use ndarray::Array2;
use num_traits::{Float, One, Zero};

/// Calculates the Cholesky decomposition of a 2x2 correlation matrix.
///
/// The correlation matrix is defined as:
/// ```text
/// [[1,   rho],
///  [rho, 1  ]]
/// ```
///
/// The resulting lower triangular matrix `L` is:
/// ```text
/// [[1,   0              ],
///  [rho, sqrt(1 - rho^2)]]
/// ```
///
/// This is used to correlate two series of standard normal random variables.
///
/// # Arguments
///
/// * `rho`: The correlation coefficient, a value of type `T`.
///
/// # Returns
///
/// A 2x2 `ndarray::Array2<T>` representing the lower triangular Cholesky factor `L`.
///
/// # Panics
///
/// This function will panic if `rho` is outside the mathematical domain of `[-1.0, 1.0]`,
/// as `(1 - rho^2)` would be negative, causing `sqrt()` to return `NaN` or panic for real numbers.
pub fn cholesky_2d<T>(rho: T) -> Array2<T>
where
    T: Float + One + Zero,
{
    let one = T::one();
    let zero = T::zero();
    let correlation_term = (one - rho * rho).sqrt();
    ndarray::arr2(&[[one, zero], [rho, correlation_term]])
}
