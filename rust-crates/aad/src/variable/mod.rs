//! # The `AADVar` Type
//!
//! This module defines the core `AADVar` struct, which is the central type for
//! performing automatic differentiation. It also implements several standard traits
//! to make `AADVar` behave like a regular numeric type.

pub mod arithmetic;
pub mod math;
pub mod ops;

use crate::tape::push_to_tape;
use std::cmp::Ordering;
use num_traits::{FromPrimitive, ToPrimitive};

/// Represents a variable on the computation graph (the "tape").
///
/// An `AADVar` holds both its concrete `value` and an `index` that points to the
/// `Node` on the tape representing the operation that produced it. This structure
/// allows the backward pass to traverse the graph and accumulate derivatives.
#[derive(Clone, Copy, Debug)]
pub struct AADVar {
    /// The concrete floating-point value of the variable.
    pub value: f64,
    /// The index of the corresponding `Node` on the AAD tape.
    pub index: usize,
}

impl AADVar {
    /// Creates a new "leaf" variable on the tape, representing a constant.
    ///
    /// A constant has no parents and its operation node on the tape is empty.
    /// This is the entry point for introducing external values into the computation graph.
    pub fn constant(value: f64) -> Self {
        let new_index = push_to_tape(vec![], vec![]);
        AADVar {
            value,
            index: new_index,
        }
    }
}

/// Implements equality comparison based on the concrete `value` of the `AADVar`.
impl PartialEq for AADVar {
    fn eq(&self, other: &Self) -> bool {
        self.value == other.value
    }
}

/// Implements partial ordering based on the concrete `value` of the `AADVar`.
impl PartialOrd for AADVar {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        self.value.partial_cmp(&other.value)
    }
}

/// Allows converting primitive numeric types into an `AADVar`.
/// This is required to conform to the `num_traits::Float` trait.
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

/// Allows converting an `AADVar` back into primitive numeric types.
/// This is required to conform to the `num_traits::Float` trait.
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
