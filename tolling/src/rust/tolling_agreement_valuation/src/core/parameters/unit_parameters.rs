use serde::Deserialize;

/// Represents the operational and cost parameters of a single power generation unit.
///
/// This struct is generic over the number type `T`, allowing it to be used
/// with both standard floats (`f64`) for simulation and `AADVar` for greeks calculation.
#[derive(Debug, Deserialize, Clone)]
pub struct UnitParameter<T> {
    /// The efficiency of the unit in converting fuel (gas) to electricity.
    /// Units: MWh / MMBtu
    pub heat_rate: T,
    /// The maximum power output of the unit.
    /// Units: MWh
    pub capacity: T,
    /// The fixed cost incurred each time the unit is started.
    /// Units: €
    pub start_up_costs: T,
}

impl<T> UnitParameter<T> {
    /// Constructs a new `UnitParameter` instance.
    pub fn new(heat_rate: T, capacity: T, start_up_costs: T) -> Self {
        UnitParameter {
            heat_rate,
            capacity,
            start_up_costs,
        }
    }
}
