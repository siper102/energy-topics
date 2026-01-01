use anyhow::Result;
use serde::de::DeserializeOwned;
use std::fs::File;

pub struct JsonFileReader;

impl JsonFileReader {
    pub fn read<T>(filename: &str) -> Result<T>
    where
        T: DeserializeOwned,
    {
        let file = File::open(filename)?;
        let model_parameters: T = serde_json::from_reader(file)?;
        Ok(model_parameters)
    }
}
