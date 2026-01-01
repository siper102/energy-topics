use crate::data_reader::json_reader::JsonFileReader;
use anyhow::Result;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct UnitParameter {
    // How many MwH can we generate from one BBTU (MwH / BBTU)
    pub heat_rate: f64,
    // How many MwH can be generated (MwH)
    pub capacity: f64,
    // How expensive is the startup (€)
    pub start_up_costs: f64,
}

impl UnitParameter {
    // Read a list of unit parameters for one facility
    pub fn from_json_file(path: &str) -> Result<Vec<Self>> {
        JsonFileReader::read(path)
    }
}