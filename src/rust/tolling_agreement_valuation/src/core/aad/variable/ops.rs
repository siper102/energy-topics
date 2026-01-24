use std::ops::Neg;
use crate::core::aad::tape::push_to_tape;
use super::AADVar;

impl Neg for AADVar {
    type Output = AADVar;

    fn neg(self) -> Self::Output {
        let res_val = -self.value;
        let new_index = push_to_tape(vec![-1.0], vec![self.index]);
        AADVar { value: res_val, index: new_index }
    }
}
