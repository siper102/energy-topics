pub mod arithmetic;
pub mod math;
pub mod ops;

use std::cmp::Ordering;
use crate::core::aad::tape::{push_to_tape, TAPE};

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

    pub fn backward(&self) -> Vec<f64> {
        TAPE.with(|t| {
            let tape = t.borrow();
            let len = tape.nodes.len();

            let mut adjoints = vec![0.0; len];
            if self.index < len {
                adjoints[self.index] = 1.0;
            }
            for i in (0..len).rev() {
                let node_grad = adjoints[i];
                if node_grad == 0.0 {
                    continue;
                }
                let node = &tape.nodes[i];

                // Propagate to parents using the Chain Rule:
                // parent_grad += node_grad * weight
                for (parent_idx, weight) in node.parents.iter().zip(&node.weights) {
                    adjoints[*parent_idx] += node_grad * weight;
                }
            }

            adjoints
        })
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
