import pyomo.environ as pyo
import pandas as pd
import numpy as np
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
    # Grid usage fee (USD / kWh).
    # Represents network fees or transaction costs for using the grid.
    grid_fee: float


def generate_garch_scenarios(n_steps: int, n_scenarios: int = 10, scale_factor: float = 100.0) -> np.ndarray:
    """
    Generates AR(1)-GARCH(1,1) intraday price spread scenarios.
    Uses the parameters fitted in price_spread_analysis.ipynb.
    """
    mu = 5.0801e-03
    phi = 0.8622
    omega = 0.0338
    alpha = 0.5178
    beta = 0.3994
    
    uncond_var = omega / (1 - alpha - beta)
    
    y = np.zeros((n_steps, n_scenarios))
    h = np.zeros((n_steps, n_scenarios))
    eps = np.zeros((n_steps, n_scenarios))
    
    for s in range(n_scenarios):
        h[0, s] = uncond_var
        eps[0, s] = np.random.normal(0, np.sqrt(h[0, s]))
        y[0, s] = mu + eps[0, s]
        
        for t in range(1, n_steps):
            h[t, s] = omega + alpha * (eps[t-1, s]**2) + beta * h[t-1, s]
            eps[t, s] = np.random.normal(0, np.sqrt(h[t, s]))
            y[t, s] = mu + phi * y[t-1, s] + eps[t, s]
            
    return y / scale_factor


def create_microgrid_model(
    time_series: pd.DataFrame,
    battery_params: BatteryParams,
    hyper_params: Hyperparameters,
    n_scenarios: int = 10,
) -> pyo.ConcreteModel:
    """
    FACTORY FUNCTION: Builds and returns a clean, un-solved Pyomo model.
    Supports Stochastic Optimization with GARCH intraday price scenarios.
    """
    times = time_series.index
    if len(times) < 2:
        raise ValueError(
            "The 'times' list must contain at least two timestamps to calculate delta_t."
        )

    # Timedelta in hours
    delta_t = (times[1] - times[0]).total_seconds() / 3600.0

    model = pyo.ConcreteModel()

    ### Sets
    model.T = pyo.Set(initialize=times)
    model.S = pyo.RangeSet(0, n_scenarios - 1)

    ### Variables
    model.P_buy = pyo.Var(model.T, bounds=(0, 20.0))  # Added 20kW grid limit
    model.P_sell = pyo.Var(model.T, bounds=(0, 20.0))  # Added 20kW grid limit
    model.P_charge = pyo.Var(model.T, bounds=(0, battery_params.max_power_kw))
    model.P_discharge = pyo.Var(model.T, bounds=(0, battery_params.max_power_kw))

    model.E = pyo.Var(
        model.T, bounds=(0, battery_params.max_capacity_kwh)
    )  # Battery State

    ### Generate scenarios
    n_steps = len(times)
    np.random.seed(42)  # For reproducible price scenario path generation
    spreads = generate_garch_scenarios(n_steps, n_scenarios)

    # Map (time, scenario) to values
    lambda_buy_dict = {}
    lambda_sell_dict = {}
    for i, t in enumerate(times):
        price_buy_base = time_series.loc[t, "price_buy"]
        price_sell_base = time_series.loc[t, "price_sell"]
        for s in range(n_scenarios):
            lambda_buy_dict[(t, s)] = price_buy_base + spreads[i, s]
            lambda_sell_dict[(t, s)] = price_sell_base + spreads[i, s]

    ### Parameters (Using dict(zip()) to bind the lists to timestamps)
    model.lambda_buy = pyo.Param(model.T, model.S, initialize=lambda_buy_dict)
    model.lambda_sell = pyo.Param(model.T, model.S, initialize=lambda_sell_dict)
    model.P_load = pyo.Param(model.T, initialize=time_series["load_kw"].to_dict())
    model.P_solar = pyo.Param(model.T, initialize=time_series["solar_kw"].to_dict())

    # Keep original Day-Ahead price series for DB reporting
    model.price_buy_da = pyo.Param(model.T, initialize=time_series["price_buy"].to_dict())
    model.price_sell_da = pyo.Param(model.T, initialize=time_series["price_sell"].to_dict())

    ### Objective
    def objective_rule(m):
        total_cost = 0
        num_scenarios = len(m.S)
        for t in m.T:
            # Expected energy purchase/sale cost over all scenarios
            expected_energy_cost = sum(
                m.lambda_buy[t, s] * m.P_buy[t] - m.lambda_sell[t, s] * m.P_sell[t]
                for s in m.S
            ) / num_scenarios
            
            # Grid usage fees (Network/Transaction costs)
            grid_usage_cost = hyper_params.grid_fee * (m.P_buy[t] + m.P_sell[t])

            # Battery degradation penalty
            degradation = hyper_params.alpha * (m.P_charge[t] ** 2 + m.P_discharge[t] ** 2)

            total_cost += (expected_energy_cost + grid_usage_cost) * delta_t + degradation
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

    model.energy_dynamics_constraint = pyo.Constraint(
        model.T, rule=energy_dynamics_rule
    )

    # Return the fully constructed, ready-to-solve model
    return model
