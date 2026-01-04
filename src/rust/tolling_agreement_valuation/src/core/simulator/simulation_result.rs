#[cfg(feature = "python")]
use ndarray::Ix3;
use ndarray::{Array3, ArrayView2, Axis};
#[cfg(feature = "python")]
use numpy::{IntoPyArray, PyArray};
#[cfg(feature = "python")]
use pyo3::{Bound, Python};

// Struct that wraps (and owns) the simulation result but provides lightweight methods
// That return the fields for simulation.
// Internal Layout: (num_paths, asset_idx, n_points)
pub struct SimulationResult {
    data: Array3<f64>,
}

impl SimulationResult {
    pub fn new(data: Array3<f64>) -> Self {
        Self { data }
    }

    pub fn get_asset_data(&self, asset_idx: usize) -> ArrayView2<'_, f64> {
        self.data.index_axis(Axis(1), asset_idx)
    }

    pub fn num_paths(&self) -> usize {
        self.data.len_of(Axis(0))
    }

    pub fn num_points(&self) -> usize {
        self.data.len_of(Axis(2))
    }

    #[cfg(feature = "python")]
    pub fn into_pyarray(self, py: Python) -> Bound<PyArray<f64, Ix3>> {
        self.data.into_pyarray(py)
    }
}
