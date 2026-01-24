use std::ops::{Add, AddAssign, Div, DivAssign, Mul, MulAssign, Rem, RemAssign, Sub, SubAssign};
use crate::core::aad::tape::push_to_tape;
use super::AADVar;

impl Add for AADVar {
    type Output = AADVar;
    fn add(self, rhs: AADVar) -> AADVar {
        let res_val = self.value + rhs.value;
        let new_index = push_to_tape(vec![1.0, 1.0], vec![self.index, rhs.index]);
        AADVar { value: res_val, index: new_index }
    }
}

impl Sub for AADVar {
    type Output = AADVar;
    fn sub(self, rhs: AADVar) -> AADVar {
        let res_val = self.value - rhs.value;
        let new_index = push_to_tape(vec![1.0, -1.0], vec![self.index, rhs.index]);
        AADVar { value: res_val, index: new_index }
    }
}

impl Mul for AADVar {
    type Output = AADVar;
    fn mul(self, rhs: AADVar) -> AADVar {
        let res_val = self.value * rhs.value;
        let new_index = push_to_tape(vec![rhs.value, self.value], vec![self.index, rhs.index]);
        AADVar { value: res_val, index: new_index }
    }
}

impl Div for AADVar {
    type Output = AADVar;
    fn div(self, rhs: AADVar) -> AADVar {
        let res_val = self.value / rhs.value;
        let new_index = push_to_tape(vec![1.0 / rhs.value, -self.value / (rhs.value * rhs.value)], vec![self.index, rhs.index]);
        AADVar { value: res_val, index: new_index }
    }
}

impl Rem for AADVar {
    type Output = AADVar;
    fn rem(self, rhs: AADVar) -> AADVar {
        // Remainder derivative is 1.0 for lhs and floor(-lhs/rhs) for rhs,
        // but often treated as constant or simplified.
        // For standard float remainder x % y:
        // x % y = x - y * trunc(x/y)
        // If we treat trunc(x/y) as constant (locally), then:
        // d/dx = 1
        // d/dy = -trunc(x/y)
        let res_val = self.value % rhs.value;
        let trunc = (self.value / rhs.value).trunc();
        let new_index = push_to_tape(vec![1.0, -trunc], vec![self.index, rhs.index]);
        AADVar { value: res_val, index: new_index }
    }
}

// Assignment operators are needed for loops like `w_t += ...`
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
