pub mod arithmetic;
pub mod math;
pub mod ops; // Keeping ops if it contains Neg, or move Neg to arithmetic.

use std::cmp::Ordering;
use crate::tape::push_to_tape;

#[derive(Clone, Copy, Debug)]
pub struct AADVar {
    pub value: f64,
    // index on tape
    pub index: usize,
}

// Utilities for AADVar
impl AADVar {
    // Generic constructor for any constant (like 5.0, -1.0, etc.)
    pub fn constant(value: f64) -> Self {
        let new_index = push_to_tape(vec![], vec![]);
        AADVar { value, index: new_index }
    }
}

impl PartialEq for AADVar {
    fn eq(&self, other: &Self) -> bool {
        self.value == other.value
    }
}

impl PartialOrd for AADVar {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        self.value.partial_cmp(&other.value)
    }
}

use num_traits::{FromPrimitive, ToPrimitive};

impl FromPrimitive for AADVar {
    fn from_i64(n: i64) -> Option<Self> {
        Some(AADVar::constant(n as f64))
    }
    fn from_u64(n: u64) -> Option<Self> {
        Some(AADVar::constant(n as f64))
    }
    fn from_f64(n: f64) -> Option<Self> {
        Some(AADVar::constant(n))
    }
}

impl ToPrimitive for AADVar {
    fn to_i64(&self) -> Option<i64> {
        self.value.to_i64()
    }
    fn to_u64(&self) -> Option<u64> {
        self.value.to_u64()
    }
    fn to_f64(&self) -> Option<f64> {
        Some(self.value)
    }
}
