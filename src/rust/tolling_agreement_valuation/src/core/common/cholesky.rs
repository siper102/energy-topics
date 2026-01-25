use ndarray::Array2;
use num_traits::{Float, One, Zero};

/// Calculates the Cholesky decomposition of a 2x2 correlation matrix.
///
/// The correlation matrix is defined as:
///   [[1, rho],
///    [rho, 1]]
///
/// The resulting lower triangular matrix L is:
///   [[1, 0],
///    [rho, sqrt(1 - rho^2)]]
///
/// # Arguments
///
/// * `rho`: The correlation coefficient.
///
/// # Returns
///
/// A 2x2 `ndarray::Array2` representing the lower triangular Cholesky factor.
pub fn cholesky_2d<T>(rho: T) -> Array2<T>
where
    T: Float + One + Zero,
{
    let one = T::one();
    let zero = T::zero();
    let correlation_term = (one - rho * rho).sqrt();
    ndarray::arr2(&[[one, zero], [rho, correlation_term]])
}
