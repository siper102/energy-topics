//! # A Simple Algorithmic Automatic Differentiation (AAD) Library
//!
//! `aad` provides a basic implementation of reverse-mode Algorithmic Automatic
//! Differentiation. It is designed for educational purposes and for use cases where
//! a lightweight, dependency-free AAD system is needed.
//!
//! ## Core Concepts
//!
//! 1.  **The Tape**: A global, thread-local singleton that records every mathematical
//!     operation performed on the variables. This sequence of operations forms the
//!     computation graph.
//!
//! 2.  **`AADVar`**: The central type of the library. It wraps a standard `f64` value
//!     but also contains an index that points to its location on the tape. When
//!     operations are performed on `AADVar`s, they create new `AADVar`s and push the
//!     operation and its dependencies onto the tape.
//!
//! 3.  **The Backward Pass**: After building the computation graph, the `backward`
//!     function is called. It traverses the tape in reverse order, applying the
//!     chain rule at each step to compute the partial derivatives (adjoints) of the
//!     final result with respect to every intermediate variable.
//!
//! ## Basic Usage
//!
//! ```rust
//! use aad::{AADVar, backward, clear_tape};
//!
//! // Start with a clean slate.
//! clear_tape();
//!
//! // Create independent variables. This registers them on the tape.
//! let x = AADVar::constant(2.0); // value = 2.0
//! let y = AADVar::constant(5.0); // value = 5.0
//!
//! // Perform an operation. This adds an operation to the tape.
//! // z = x * y = 2.0 * 5.0 = 10.0
//! let z = x * y;
//!
//! // The value can be accessed directly.
//! assert_eq!(z.value, 10.0);
//!
//! // Run the backward pass to compute derivatives.
//! // We want to find dz/dx and dz/dy.
//! // We start by setting dz/dz = 1.0.
//! let mut adjoints = vec![0.0; z.index + 1];
//! adjoints[z.index] = 1.0;
//! backward(&mut adjoints);
//!
//! // The adjoints vector now contains the derivatives.
//! // dz/dx = y = 5.0
//! // dz/dy = x = 2.0
//! assert_eq!(adjoints[x.index], 5.0);
//! assert_eq!(adjoints[y.index], 2.0);
//! ```

pub mod tape;
pub mod variable;

pub use tape::{backward, clear_tape, get_tape_len};
pub use variable::AADVar;

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_abs_diff_eq;
    use num_traits::Float;

    #[test]
    fn test_add() {
        clear_tape();
        let x = AADVar::constant(2.0);
        let y = AADVar::constant(5.0);
        let z = x + y;

        assert_eq!(z.value, 7.0);

        let mut adjoints = vec![0.0; get_tape_len()];
        adjoints[z.index] = 1.0;
        backward(&mut adjoints);

        // dz/dx = 1.0
        assert_eq!(adjoints[x.index], 1.0);
        // dz/dy = 1.0
        assert_eq!(adjoints[y.index], 1.0);
    }

    #[test]
    fn test_mul() {
        clear_tape();
        let x = AADVar::constant(3.0);
        let y = AADVar::constant(4.0);
        let z = x * y;

        assert_eq!(z.value, 12.0);

        let mut adjoints = vec![0.0; get_tape_len()];
        adjoints[z.index] = 1.0;
        backward(&mut adjoints);

        // dz/dx = y = 4.0
        assert_eq!(adjoints[x.index], 4.0);
        // dz/dy = x = 3.0
        assert_eq!(adjoints[y.index], 3.0);
    }

    #[test]
    fn test_chain_rule_complex() {
        // Test z = (x * y) + sin(x)
        clear_tape();
        let x = AADVar::constant(2.0);
        let y = AADVar::constant(3.0);

        let prod = x * y;
        let sin_x = x.sin();
        let z = prod + sin_x;

        assert_abs_diff_eq!(z.value, 2.0 * 3.0 + 2.0_f64.sin(), epsilon = 1e-9);

        let mut adjoints = vec![0.0; get_tape_len()];
        adjoints[z.index] = 1.0;
        backward(&mut adjoints);

        // dz/dx = d(prod)/dx + d(sin_x)/dx = y + cos(x)
        let expected_dz_dx = 3.0 + 2.0_f64.cos();
        assert_abs_diff_eq!(adjoints[x.index], expected_dz_dx, epsilon = 1e-9);

        // dz/dy = d(prod)/dy + d(sin_x)/dy = x + 0
        let expected_dz_dy = 2.0;
        assert_abs_diff_eq!(adjoints[y.index], expected_dz_dy, epsilon = 1e-9);
    }

    #[test]
    fn test_exp() {
        clear_tape();
        let x = AADVar::constant(2.0);
        let y = x.exp();

        assert_eq!(y.value, 2.0_f64.exp());

        let mut adjoints = vec![0.0; get_tape_len()];
        adjoints[y.index] = 1.0;
        backward(&mut adjoints);

        // dy/dx = exp(x)
        assert_eq!(adjoints[x.index], 2.0_f64.exp());
    }

    #[test]
    fn test_sin_and_cos() {
        clear_tape();
        let x = AADVar::constant(1.5);
        let y = x.sin();
        let z = x.cos();

        assert_eq!(y.value, 1.5_f64.sin());
        assert_eq!(z.value, 1.5_f64.cos());

        // Test sin derivative
        let mut adjoints_y = vec![0.0; get_tape_len()];
        adjoints_y[y.index] = 1.0;
        backward(&mut adjoints_y);

        // dy/dx = cos(x)
        assert_abs_diff_eq!(adjoints_y[x.index], 1.5_f64.cos(), epsilon = 1e-9);

        // Test cos derivative
        let mut adjoints_z = vec![0.0; get_tape_len()];
        adjoints_z[z.index] = 1.0;
        backward(&mut adjoints_z);
        
        // dz/dx = -sin(x)
        assert_abs_diff_eq!(adjoints_z[x.index], -1.5_f64.sin(), epsilon = 1e-9);
    }
    
    #[test]
    fn test_tape_clears() {
        clear_tape();
        let x = AADVar::constant(1.0);
        let _ = x * x;
        let len_before = get_tape_len();
        assert!(len_before > 0);
        
        clear_tape();
        let len_after = get_tape_len();
        assert_eq!(len_after, 0);
        
        // Ensure new variables can be created
        let y = AADVar::constant(2.0);
        assert_eq!(y.index, 0);
    }
}
