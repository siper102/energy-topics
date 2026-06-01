import pyomo.environ as pyo
import pandas as pd

def run_optimization_and_get_results(model: pyo.ConcreteModel) -> pd.DataFrame:
    """
    Runs the IPOPT solver on the provided Pyomo model,
    and returns the optimal dispatch schedule as a Pandas DataFrame.
    """
    # 1. Initialize the solver
    solver = pyo.SolverFactory('ipopt')
    
    print("Starting the IPOPT Solver...")
    
    # 2. Solve the model (tee=True streams the solver output)
    results = solver.solve(model, tee=True)
    
    # 3. Verify the solver actually found a mathematically optimal solution
    if (results.solver.status == pyo.SolverStatus.ok) and \
       (results.solver.termination_condition == pyo.TerminationCondition.optimal):
        
        print("\n✅ Optimal Solution Found! Extracting to DataFrame...")
        
        # 4. Extract the results
        data = []
        for t in model.T:
            data.append({
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
            })
            
        # 5. Format the DataFrame
        df = pd.DataFrame(data)
        df.set_index("time", inplace=True)
        df = df.round(3)
        
        print(f"Total Minimized Cost: ${pyo.value(model.cost):.2f}\n")
        return df
        
    else:
        # 6. Fail loudly if the optimization breaks
        print("\n❌ Solver failed to find an optimal solution.")
        print(f"Status: {results.solver.status}")
        print(f"Termination Condition: {results.solver.termination_condition}")
        raise RuntimeError("Optimization failed. Check model inputs and constraints.")