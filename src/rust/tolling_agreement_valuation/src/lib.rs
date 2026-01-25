//! # Tolling Agreement Valuation
//!
//! This crate provides a library for valuing energy tolling agreements using Monte Carlo
//! simulation. It includes models for simulating energy prices (gas and power) and
//! calculating the expected profit and loss (PnL) and risk metrics (Greeks).
//!
//! The core logic is written in pure Rust for performance, and Python bindings are provided
//! via the `pyo3` crate for ease of use in data science and analysis workflows.

// Conditionally compile the Python bindings module when the "python" feature is enabled.
#[cfg(feature = "python")]
use crate::python::parameters::{PyModelParameters, PyUnitParameter};
#[cfg(feature = "python")]
use crate::python::calculate_profit::calculate_daily_profits_py;
#[cfg(feature = "python")]
use crate::python::calculate_greeks::{calculate_greeks_py, PyGreeksResult};
#[cfg(feature = "python")]
use crate::python::sample_paths::sample_prices_py;
#[cfg(feature = "python")]
use pyo3::prelude::*;

/// The core business logic of the simulation and valuation models.
/// This module is private to the crate.
mod core;

/// Public module containing Python bindings for the core logic.
///
/// This module is only compiled when the `python` feature is enabled. It uses `pyo3` to
/// expose the simulation and valuation functions to a Python interpreter.
#[cfg(feature = "python")]
pub mod python;

/// Defines the Python module and exposes the Rust functions and types to Python.
///
/// This function is the entry point for the Python interpreter when it imports the
/// compiled library. It adds the core functions and parameter classes to the Python module.
#[cfg(feature = "python")]
#[pymodule]
fn tolling_agreement_valuation(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_daily_profits_py, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_greeks_py, m)?)?;
    m.add_function(wrap_pyfunction!(sample_prices_py, m)?)?;
    m.add_class::<PyModelParameters>()?;
    m.add_class::<PyUnitParameter>()?;
    m.add_class::<PyGreeksResult>()?;
    Ok(())
}
