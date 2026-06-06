import pyomo.environ as pyo
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List

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
    # Grid usage fee (USD / kWh).
    # Represents network fees or transaction costs for using the grid.
    grid_fee: float

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
    model.P_buy = pyo.Var(model.T, bounds=(0, 20.0)) # Added 20kW grid limit
    model.P_sell = pyo.Var(model.T, bounds=(0, 20.0)) # Added 20kW grid limit
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
            # Main economic term (Energy Purchase/Sale)
            energy_cost = (m.lambda_buy[t] * m.P_buy[t]) - (m.lambda_sell[t] * m.P_sell[t])
            
            # Grid usage fees (Network/Transaction costs)
            grid_usage_cost = hyper_params.grid_fee * (m.P_buy[t] + m.P_sell[t])

            # Battery degradation penalty
            degradation = hyper_params.alpha * (m.P_charge[t]**2 + m.P_discharge[t]**2)
            
            total_cost += (energy_cost + grid_usage_cost) * delta_t + degradation
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

def create_stochastic_microgrid_model(
    time_series: pd.DataFrame, # Contains static solar/prices
    load_scenarios: List[List[float]],
    battery_params: BatteryParams,
    hyper_params: Hyperparameters,
) -> pyo.ConcreteModel:
    """
    STOCHASTIC FACTORY: Multi-scenario optimization.
    Goal: Minimize EXPECTED cost across all load scenarios.
    """
    times = time_series.index
    delta_t = (times[1] - times[0]).total_seconds() / 3600.0
    num_scenarios = len(load_scenarios)
    
    model = pyo.ConcreteModel()

    ### Sets
    model.T = pyo.Set(initialize=times)
    model.S = pyo.Set(initialize=range(num_scenarios))

    ### Variables (Now indexed by both Time and Scenario)
    model.P_buy = pyo.Var(model.S, model.T, bounds=(0, 20.0))
    model.P_sell = pyo.Var(model.S, model.T, bounds=(0, 20.0))
    model.P_charge = pyo.Var(model.S, model.T, bounds=(0, battery_params.max_power_kw))
    model.P_discharge = pyo.Var(model.S, model.T, bounds=(0, battery_params.max_power_kw))
    model.E = pyo.Var(model.S, model.T, bounds=(0, battery_params.max_capacity_kwh))

    ### Parameters
    model.lambda_buy = pyo.Param(model.T, initialize=time_series['price_buy'].to_dict())
    model.lambda_sell = pyo.Param(model.T, initialize=time_series['price_sell'].to_dict())
    model.P_solar = pyo.Param(model.T, initialize=time_series['solar_kw'].to_dict())
    
    # P_load is scenario-dependent
    load_dict = {}
    for s in range(num_scenarios):
        for i, t in enumerate(times):
            load_dict[(s, t)] = load_scenarios[s][i]
    model.P_load = pyo.Param(model.S, model.T, initialize=load_dict)

    ### Objective: Minimize EXPECTED Cost
    def objective_rule(m):
        expected_cost = 0
        prob = 1.0 / num_scenarios # Equal probability for each scenario
        
        for s in m.S:
            scenario_cost = 0
            for t in m.T:
                energy_cost = (m.lambda_buy[t] * m.P_buy[s, t]) - (m.lambda_sell[t] * m.P_sell[s, t])
                grid_usage_cost = hyper_params.grid_fee * (m.P_buy[s, t] + m.P_sell[s, t])
                degradation = hyper_params.alpha * (m.P_charge[s, t]**2 + m.P_discharge[s, t]**2)
                
                scenario_cost += (energy_cost + grid_usage_cost) * delta_t + degradation
            
            expected_cost += prob * scenario_cost
            
        return expected_cost
    model.cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    ### Constraints
    def balance_rule(m, s, t):
        return m.P_solar[t] + m.P_buy[s, t] + m.P_discharge[s, t] == m.P_load[s, t] + m.P_sell[s, t] + m.P_charge[s, t]
    model.balance_constraint = pyo.Constraint(model.S, model.T, rule=balance_rule)

    def energy_dynamics_rule(m, s, t):
        eff_c = battery_params.efficiency_charge
        eff_d = battery_params.efficiency_discharge
        delta_e = ((m.P_charge[s, t] * eff_c) - (m.P_discharge[s, t] / eff_d)) * delta_t
        if t == m.T.first():
            return m.E[s, t] == battery_params.initial_soc_kwh + delta_e
        else:
            prev_t = m.T.prev(t)
            return m.E[s, t] == m.E[s, prev_t] + delta_e
    model.energy_dynamics_constraint = pyo.Constraint(model.S, model.T, rule=energy_dynamics_rule)

    return model