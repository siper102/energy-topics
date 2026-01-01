use anyhow::{Context, Result};
// Import Context to add nice error messages
use serde::de::DeserializeOwned;
use std::fs::File;

pub struct CsvFileReader;

impl CsvFileReader {
    pub fn read<T>(filename: &str) -> Result<Vec<T>>
    where
        T: DeserializeOwned,
    {
        let file = File::open(filename)
            .with_context(|| format!("Failed to open file: {}", filename))?;

        let mut rdr = csv::Reader::from_reader(file);

        let rows = rdr
            .deserialize()
            .collect::<Result<Vec<T>, csv::Error>>()
            .context("Failed to parse CSV data")?;

        Ok(rows)
    }
}