use crate::data_reader::csv_reader::CsvFileReader;
use anyhow::Result;
use chrono::NaiveDateTime;
use serde::{self, Deserialize, Deserializer};

fn deserialize_datetime<'de, D>(deserializer: D) -> Result<NaiveDateTime, D::Error>
where
    D: Deserializer<'de>,
{
    let s = String::deserialize(deserializer)?;
    NaiveDateTime::parse_from_str(&s, "%Y-%m-%d %H:%M:%S").map_err(serde::de::Error::custom)
}

#[derive(Debug, Deserialize)]
pub struct ForwardCurvePoint {
    #[serde(deserialize_with = "deserialize_datetime")]
    #[allow(dead_code)]
    pub date: NaiveDateTime,
    pub price: f64,
}

impl ForwardCurvePoint {
    pub fn from_csv_file(path: &str) -> Result<Vec<Self>> {
        CsvFileReader::read(path)
    }
}
