//! # Unary Operations for `AADVar`
//!
//! This module implements unary operations, such as negation.

use crate::tape::push_to_tape;
use super::AADVar;
use std::ops::Neg;

impl Neg for AADVar {
    type Output = AADVar;

    /// Implements the unary negation (`-`) operator for `AADVar`.
    ///
    /// When `-v` is computed, this function is called. It performs two actions:
    /// 1.  Computes the negated value: `-v.value`.
    /// 2.  Pushes a new node onto the tape representing this operation. The new node has
    ///     one parent (the variable `v`) and the weight of the edge is `-1.0`, which is
    ///     the derivative of `-v` with respect to `v`.
    fn neg(self) -> Self::Output {
        let res_val = -self.value;
        // The derivative of `-x` with respect to `x` is `-1`.
        let new_index = push_to_tape(vec![-1.0], vec![self.index]);
        AADVar {
            value: res_val,
            index: new_index,
        }
    }
}
