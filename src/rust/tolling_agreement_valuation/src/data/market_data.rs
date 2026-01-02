use crate::data_reader::csv_reader::CsvFileReader;
use crate::data::model_parameters::ModelParameters;
use anyhow::Result;
use chrono::NaiveDateTime;
use ndarray::Array1;
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

pub struct MarketData {
    pub gas_curve: Array1<f64>,
    pub power_curve: Array1<f64>,
    pub model_params: ModelParameters,
}

impl MarketData {
    pub fn load(gas_path: &str, power_path: &str, model_params_path: &str) -> Result<Self> {
        let gas_points = ForwardCurvePoint::from_csv_file(gas_path)?;
        let gas_curve = Array1::from_iter(gas_points.into_iter().map(|p| p.price));

        let power_points = ForwardCurvePoint::from_csv_file(power_path)?;
        let power_curve = Array1::from_iter(power_points.into_iter().map(|p| p.price));

        let model_params = ModelParameters::from_json_file(model_params_path)?;

        Ok(Self {
            gas_curve,
            power_curve,
            model_params,
        })
    }
}
