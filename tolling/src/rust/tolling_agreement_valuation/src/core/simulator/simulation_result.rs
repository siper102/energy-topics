#[cfg(feature = "python")]
use ndarray::Ix3;
use ndarray::{Array3, ArrayView2, Axis};
#[cfg(feature = "python")]
use numpy::{IntoPyArray, PyArray};
#[cfg(feature = "python")]
use pyo3::{Bound, Python};

/// A wrapper struct for the results of a Monte Carlo simulation.
///
/// This struct owns the simulation data, which is stored in a 3D array. It provides
/// convenient methods to access dimensions and slices of the data.
///
/// The internal data is laid out as `(num_paths, num_assets, num_points)`.
pub struct SimulationResult<T> {
    data: Array3<T>,
}

impl<T> SimulationResult<T> {
    /// Constructs a new `SimulationResult` from a 3D array of data.
    pub fn new(data: Array3<T>) -> Self {
        Self { data }
    }

    /// Returns a 2D view of the data for a single asset.
    ///
    /// The returned array view has the shape `(num_paths, num_points)`.
    ///
    /// # Arguments
    ///
    /// * `asset_idx`: The index of the asset to retrieve (e.g., from `TollingAssetIndex`).
    pub fn get_asset_data(&self, asset_idx: usize) -> ArrayView2<'_, T> {
        self.data.index_axis(Axis(1), asset_idx)
    }

    /// Returns the number of simulation paths.
    pub fn num_paths(&self) -> usize {
        self.data.len_of(Axis(0))
    }

    /// Returns the number of time steps (points) in each path.
    pub fn num_points(&self) -> usize {
        self.data.len_of(Axis(2))
    }
}

#[cfg(feature = "python")]
impl SimulationResult<f64> {
    /// Consumes the `SimulationResult` and converts its data into a Python-owned NumPy array.
    ///
    /// This method is only available when the `python` feature is enabled and for `f64` data.
    /// It provides a zero-copy (if memory layout allows) way to share the results with Python.
    pub fn into_pyarray(self, py: Python) -> Bound<PyArray<f64, Ix3>> {
        self.data.into_pyarray(py)
    }
}
