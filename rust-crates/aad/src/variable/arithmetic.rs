
//! # Arithmetic Operator Overloading for `AADVar`
//! 
//! This module implements the standard arithmetic traits from `std::ops` (e.g., `Add`,
//! Mul`, `Sub`, `Div`) for the `AADVar` type. This is what allows `AADVar`s to be
//! used in mathematical expressions with natural syntax (e.g., `a + b * c`).
//! 
//! Each implementation calculates the resulting value and pushes the corresponding
//! operation and its derivatives (weights) onto the AAD tape.

use super::AADVar;
use crate::tape::push_to_tape;
use std::ops::{
    Add, AddAssign, Div, DivAssign, Mul, MulAssign, Rem, RemAssign, Sub, SubAssign,
};

impl Add for AADVar {
    type Output = AADVar;
    /// Implements the `+` operator for `AADVar`.
    ///
    /// If `z = x + y`, then `dz/dx = 1` and `dz/dy = 1`.
    fn add(self, rhs: AADVar) -> AADVar {
        let res_val = self.value + rhs.value;
        let new_index = push_to_tape(vec![1.0, 1.0], vec![self.index, rhs.index]);
        AADVar {
            value: res_val,
            index: new_index,
        }
    }
}

impl Sub for AADVar {
    type Output = AADVar;
    /// Implements the `-` operator for `AADVar`.
    ///
    /// If `z = x - y`, then `dz/dx = 1` and `dz/dy = -1`.
    fn sub(self, rhs: AADVar) -> AADVar {
        let res_val = self.value - rhs.value;
        let new_index = push_to_tape(vec![1.0, -1.0], vec![self.index, rhs.index]);
        AADVar {
            value: res_val,
            index: new_index,
        }
    }
}

impl Mul for AADVar {
    type Output = AADVar;
    /// Implements the `*` operator for `AADVar`.
    ///
    /// If `z = x * y`, then by the product rule, `dz/dx = y` and `dz/dy = x`.
    fn mul(self, rhs: AADVar) -> AADVar {
        let res_val = self.value * rhs.value;
        let new_index = push_to_tape(vec![rhs.value, self.value], vec![self.index, rhs.index]);
        AADVar {
            value: res_val,
            index: new_index,
        }
    }
}

impl Div for AADVar {
    type Output = AADVar;
    /// Implements the `/` operator for `AADVar`.
    ///
    /// If `z = x / y`, then by the quotient rule:
    /// - `dz/dx = 1 / y`
    /// - `dz/dy = -x / y^2`
    fn div(self, rhs: AADVar) -> AADVar {
        let res_val = self.value / rhs.value;
        let new_index = push_to_tape(
            vec![1.0 / rhs.value, -self.value / (rhs.value * rhs.value)],
            vec![self.index, rhs.index],
        );
        AADVar {
            value: res_val,
            index: new_index,
        }
    }
}

impl Rem for AADVar {
    type Output = AADVar;
    /// Implements the `%` (remainder) operator for `AADVar`.
    ///
    /// The derivative of the remainder operation is complex. This implementation uses a
    /// common simplification by treating `trunc(x/y)` as a local constant.
    /// From `x % y = x - y * trunc(x/y)`, the partial derivatives are:
    /// - `d/dx = 1`
    /// - `d/dy = -trunc(x/y)`
    fn rem(self, rhs: AADVar) -> AADVar {
        let res_val = self.value % rhs.value;
        let trunc = (self.value / rhs.value).trunc();
        let new_index = push_to_tape(vec![1.0, -trunc], vec![self.index, rhs.index]);
        AADVar {
            value: res_val,
            index: new_index,
        }
    }
}

// These assignment operators (e.g., `+=`, `*=`) are required by some numeric traits
// and are useful for writing idiomatic loops. They are implemented by calling the
// corresponding binary operator.

impl AddAssign for AADVar {
    fn add_assign(&mut self, rhs: AADVar) {
        *self = *self + rhs;
    }
}

impl SubAssign for AADVar {
    fn sub_assign(&mut self, rhs: AADVar) {
        *self = *self - rhs;
    }
}

impl MulAssign for AADVar {
    fn mul_assign(&mut self, rhs: AADVar) {
        *self = *self * rhs;
    }
}

impl DivAssign for AADVar {
    fn div_assign(&mut self, rhs: AADVar) {
        *self = *self / rhs;
    }
}

impl RemAssign for AADVar {
    fn rem_assign(&mut self, rhs: AADVar) {
        *self = *self % rhs;
    }
}
