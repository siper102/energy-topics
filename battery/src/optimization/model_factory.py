import pyomo.environ as pyo
import pandas as pd
from dataclasses import dataclass

### Battery Parameter class
@dataclass
class BatteryParams:
    max_capacity_kwh: float
    max_power_kw: float
    efficiency_charge: float
    efficiency_discharge: float
    initial_soc_kwh: float

### Optimization Hyperparameters 
@dataclass
class Hyperparameters:
    # Degradation penalty (USD / kW^2). 
    # Translates high in / out flows from the battery in cost for degradation
    alpha: float

def create_microgrid_model(
    time_series: pd.DataFrame,
    battery_params: BatteryParams,
    hyper_params: Hyperparameters,
) -> pyo.ConcreteModel:
    """
    FACTORY FUNCTION: Builds and returns a clean, un-solved Pyomo model.
    """
    times = time_series.index
    if len(times) < 2:
        raise ValueError("The 'times' list must contain at least two timestamps to calculate delta_t.")

    # Timedelta in hours    
    delta_t = (times[1] - times[0]).total_seconds() / 3600.0

    model = pyo.ConcreteModel()

    ### Sets
    model.T = pyo.Set(initialize=times)

    ### Variables
    model.P_buy = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.P_sell = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.P_charge = pyo.Var(model.T, bounds=(0, battery_params.max_power_kw))
    model.P_discharge = pyo.Var(model.T, bounds=(0, battery_params.max_power_kw))
    
    model.E = pyo.Var(model.T, bounds=(0, battery_params.max_capacity_kwh))

    ### Parameters (Using dict(zip()) to bind the lists to timestamps)
    model.lambda_buy = pyo.Param(model.T, initialize=time_series['price_buy'].to_dict())
    model.lambda_sell = pyo.Param(model.T, initialize=time_series['price_sell'].to_dict())
    model.P_load = pyo.Param(model.T, initialize=time_series['load_kw'].to_dict())
    model.P_solar = pyo.Param(model.T, initialize=time_series['solar_kw'].to_dict())

    ### Objective
    def objective_rule(m):
        total_cost = 0
        for t in m.T:
            energy_cost = (m.lambda_buy[t] * m.P_buy[t]) - (m.lambda_sell[t] * m.P_sell[t])
            degradation = hyper_params.alpha * (m.P_charge[t]**2 + m.P_discharge[t]**2)
            total_cost += (energy_cost * delta_t) + degradation
        return total_cost
    model.cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    ### Constraints
    def balance_rule(m, t):
        supply = m.P_solar[t] + m.P_buy[t] + m.P_discharge[t]
        demand = m.P_load[t] + m.P_sell[t] + m.P_charge[t]
        return supply == demand
    model.balance_constraint = pyo.Constraint(model.T, rule=balance_rule)

    def energy_dynamics_rule(m, t):
        eff_c = battery_params.efficiency_charge
        eff_d = battery_params.efficiency_discharge
        delta_e = ((m.P_charge[t] * eff_c) - (m.P_discharge[t] / eff_d)) * delta_t
        
        if t == m.T.first():
            return m.E[t] == battery_params.initial_soc_kwh + delta_e
        else:
            prev_t = m.T.prev(t)
            return m.E[t] == m.E[prev_t] + delta_e
    model.energy_dynamics_constraint = pyo.Constraint(model.T, rule=energy_dynamics_rule)

    # Return the fully constructed, ready-to-solve model
    return model