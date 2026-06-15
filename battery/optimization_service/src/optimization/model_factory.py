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
    time_series: pd.DataFrame, # Contains static solar
    load_forecast: List[float], # Point estimate (Deterministic)
    price_scenarios: List[List[float]], # Stochastic Price Scenarios
    battery_params: BatteryParams,
    hyper_params: Hyperparameters,
) -> pyo.ConcreteModel:
    """
    STOCHASTIC FACTORY: Multi-scenario optimization.
    Goal: Minimize EXPECTED cost across all PRICE scenarios, with deterministic LOAD.
    """
    times = time_series.index
    delta_t = (times[1] - times[0]).total_seconds() / 3600.0
    num_scenarios = len(price_scenarios)
    
    model = pyo.ConcreteModel()

    ### Sets
    model.T = pyo.Set(initialize=times)
    model.S = pyo.Set(initialize=range(num_scenarios))

    ### Variables (Indexed by both Time and Price Scenario)
    model.P_buy = pyo.Var(model.S, model.T, bounds=(0, 20.0))
    model.P_sell = pyo.Var(model.S, model.T, bounds=(0, 20.0))
    model.P_charge = pyo.Var(model.S, model.T, bounds=(0, battery_params.max_power_kw))
    model.P_discharge = pyo.Var(model.S, model.T, bounds=(0, battery_params.max_power_kw))
    model.E = pyo.Var(model.S, model.T, bounds=(0, battery_params.max_capacity_kwh))

    ### Parameters
    model.P_solar = pyo.Param(model.T, initialize=time_series['solar_kw'].to_dict())
    model.P_load = pyo.Param(model.T, initialize=dict(zip(times, load_forecast)))
    
    # Prices are now scenario-dependent
    price_buy_dict = {}
    price_sell_dict = {}
    for s in range(num_scenarios):
        for i, t in enumerate(times):
            price_buy_dict[(s, t)] = price_scenarios[s][i]
            # Assuming sell price is a fraction of buy price or fixed spread for now if not provided
            price_sell_dict[(s, t)] = price_scenarios[s][i] * 0.9 
            
    model.lambda_buy = pyo.Param(model.S, model.T, initialize=price_buy_dict)
    model.lambda_sell = pyo.Param(model.S, model.T, initialize=price_sell_dict)

    ### Objective: Minimize EXPECTED Cost
    def objective_rule(m):
        expected_cost = 0
        prob = 1.0 / num_scenarios # Equal probability for each scenario
        
        for s in m.S:
            scenario_cost = 0
            for t in m.T:
                energy_cost = (m.lambda_buy[s, t] * m.P_buy[s, t]) - (m.lambda_sell[s, t] * m.P_sell[s, t])
                grid_usage_cost = hyper_params.grid_fee * (m.P_buy[s, t] + m.P_sell[s, t])
                degradation = hyper_params.alpha * (m.P_charge[s, t]**2 + m.P_discharge[s, t]**2)
                
                scenario_cost += (energy_cost + grid_usage_cost) * delta_t + degradation
            
            expected_cost += prob * scenario_cost
            
        return expected_cost
    model.cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    ### Constraints
    def balance_rule(m, s, t):
        return m.P_solar[t] + m.P_buy[s, t] + m.P_discharge[s, t] == m.P_load[t] + m.P_sell[s, t] + m.P_charge[s, t]
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