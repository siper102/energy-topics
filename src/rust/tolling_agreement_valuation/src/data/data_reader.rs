use crate::data::market_data::ForwardCurvePoint;
use crate::data::model_parameters::ModelParameters;
use crate::data::unit_parameters::UnitParameter;
use anyhow::{anyhow, Result};
use ndarray::Array1;

pub struct DataReader {
    gas_forward_curve_path: String,
    power_forward_curve_path: String,
    model_parameter_path: String,
    unit_parameter_path: Option<String>,
}

impl DataReader {
    pub fn new(gas_path: &str, power_path: &str, model_path: &str, unit_path: &str) -> Self {
        Self {
            gas_forward_curve_path: gas_path.to_string(),
            power_forward_curve_path: power_path.to_string(),
            model_parameter_path: model_path.to_string(),
            unit_parameter_path: Some(unit_path.to_string()),
        }
    }

    pub fn new_without_unit(gas_path: &str, power_path: &str, model_path: &str) -> Self {
        Self {
            gas_forward_curve_path: gas_path.to_string(),
            power_forward_curve_path: power_path.to_string(),
            model_parameter_path: model_path.to_string(),
            unit_parameter_path: None,
        }
    }

    pub fn read_gas_forward_curve(&self) -> Result<Array1<f64>> {
        self.read_forward_curve_as_array(self.gas_forward_curve_path.as_str())
    }

    pub fn read_power_forward_curve(&self) -> Result<Array1<f64>> {
        self.read_forward_curve_as_array(self.power_forward_curve_path.as_str())
    }

    pub fn read_model_parameters(&self) -> Result<ModelParameters> {
        ModelParameters::from_json_file(self.model_parameter_path.as_str())
    }

    pub fn read_unit_parameters(&self) -> Result<Vec<UnitParameter>> {
        if self.unit_parameter_path.is_some() {
            return UnitParameter::from_json_file(self.unit_parameter_path.as_ref().unwrap().as_str())
        }
        Err(anyhow!("No unit_parameter path specified"))
    }

    fn read_forward_curve_as_array(
        &self,
        file_path: &str,
    ) -> Result<Array1<f64>> {
        let forward_curve_points = ForwardCurvePoint::from_csv_file(file_path)?;
        let prices: Vec<f64> = forward_curve_points.iter().map(|x| x.price).collect();

        Ok(Array1::from_iter(prices))
    }
}
