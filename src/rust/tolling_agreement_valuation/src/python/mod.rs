//! # Python Bindings Module
//!
//! This module and its submodules contain all the code for exposing the Rust functionalities
//! of this crate to Python. It uses the `pyo3` crate to create Python-callable functions
//! (`#[pyfunction]`) and Python-usable types (`#[pyclass]`).
//!
//! The submodules are organized to mirror the `core` services, providing wrappers for:
//! - Parameter structs (`parameters.rs`)
//! - Greeks calculation (`calculate_greeks.rs`)
//! - Profit calculation (`calculate_profit.rs`)
//! - Path sampling (`sample_paths.rs`)

pub mod calculate_profit;
pub mod parameters;
pub mod sample_paths;
pub mod calculate_greeks;
