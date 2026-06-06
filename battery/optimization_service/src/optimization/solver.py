import pyomo.environ as pyo
import pandas as pd
import numpy as np

def run_optimization_and_get_results(model: pyo.ConcreteModel) -> pd.DataFrame:
    """
    Runs the IPOPT solver on the provided Pyomo model,
    and returns the optimal dispatch schedule as a Pandas DataFrame.
    Supports both Deterministic and Stochastic models.
    """
    # 1. Initialize the solver
    solver = pyo.SolverFactory('ipopt')
    
    print("Starting the IPOPT Solver...")
    
    # 2. Solve the model
    results = solver.solve(model, tee=False)
    
    # 3. Verify success
    if (results.solver.status == pyo.SolverStatus.ok) and \
       (results.solver.termination_condition == pyo.TerminationCondition.optimal):
        
        print("\n✅ Optimal Solution Found! Extracting results...")
        
        is_stochastic = hasattr(model, 'S')
        data = []

        for t in model.T:
            if not is_stochastic:
                # Deterministic Case
                row = {
                    "time": t,
                    "load_kw": pyo.value(model.P_load[t]),
                    "solar_kw": pyo.value(model.P_solar[t]),
                    "price_buy_usd": pyo.value(model.lambda_buy[t]),
                    "price_sell_usd": pyo.value(model.lambda_sell[t]),
                    "p_buy_kw": pyo.value(model.P_buy[t]),
                    "p_sell_kw": pyo.value(model.P_sell[t]),
                    "p_charge_kw": pyo.value(model.P_charge[t]),
                    "p_discharge_kw": pyo.value(model.P_discharge[t]),
                    "soc_kwh": pyo.value(model.E[t])
                }
            else:
                # Stochastic Case: Take Mean across scenarios S
                num_s = len(model.S)
                
                # We calculate the expected value for dispatch variables
                avg_load = sum(pyo.value(model.P_load[s, t]) for s in model.S) / num_s
                avg_p_buy = sum(pyo.value(model.P_buy[s, t]) for s in model.S) / num_s
                avg_p_sell = sum(pyo.value(model.P_sell[s, t]) for s in model.S) / num_s
                avg_p_charge = sum(pyo.value(model.P_charge[s, t]) for s in model.S) / num_s
                avg_p_discharge = sum(pyo.value(model.P_discharge[s, t]) for s in model.S) / num_s
                avg_soc = sum(pyo.value(model.E[s, t]) for s in model.S) / num_s

                row = {
                    "time": t,
                    "load_kw": avg_load,
                    "solar_kw": pyo.value(model.P_solar[t]),
                    "price_buy_usd": pyo.value(model.lambda_buy[t]),
                    "price_sell_usd": pyo.value(model.lambda_sell[t]),
                    "p_buy_kw": avg_p_buy,
                    "p_sell_kw": avg_p_sell,
                    "p_charge_kw": avg_p_charge,
                    "p_discharge_kw": avg_p_discharge,
                    "soc_kwh": avg_soc
                }
            data.append(row)
            
        # 5. Format the DataFrame
        df = pd.DataFrame(data)
        df.set_index("time", inplace=True)
        df = df.round(3)
        
        print(f"Total Minimized Expected Cost: ${pyo.value(model.cost):.2f}\n")
        return df
        
    else:
        # 6. Fail loudly if the optimization breaks
        print("\n❌ Solver failed to find an optimal solution.")
        print(f"Status: {results.solver.status}")
        print(f"Termination Condition: {results.solver.termination_condition}")
        raise RuntimeError("Optimization failed. Check model inputs and constraints.")