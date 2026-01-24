use serde::Deserialize;

#[derive(Debug, Deserialize, Clone)]
pub struct UnitParameter<T> {
    // How many MwH can we generate from one BBTU (MwH / BBTU)
    pub heat_rate: T,
    // How many MwH can be generated (MwH)
    pub capacity: T,
    // How expensive is the startup (€)
    pub start_up_costs: T,
}

impl<T> UnitParameter<T> {
    pub fn new(heat_rate: T, capacity: T, start_up_costs: T) -> Self {
        UnitParameter {
            heat_rate,
            capacity,
            start_up_costs,
        }
    }
}
