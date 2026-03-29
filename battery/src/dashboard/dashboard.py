import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
from datetime import datetime

# Add src/optimization to sys.path to import our local modules
# This is a bit of a hack, but it works for a simple layout
current_dir = os.path.dirname(os.path.abspath(__file__))
opt_dir = os.path.abspath(os.path.join(current_dir, "..", "optimization"))
if opt_dir not in sys.path:
    sys.path.append(opt_dir)

try:
    from database_connector import load_data, save_data, DB_DSN
    from model_factory import create_microgrid_model, Hyperparameters
    from solver import run_optimization_and_get_results
except ImportError as e:
    st.error(f"Failed to import local optimization modules: {e}")
    st.stop()

import psycopg

st.set_page_config(page_title="Battery Optimization Dashboard", layout="wide")

st.title("🔋 Battery Optimization Dashboard")
st.markdown("Visualize microgrid data and optimized battery dispatch strategies.")

def get_dispatch_plans():
    """Fetches the latest dispatch plan from the database."""
    with psycopg.connect(DB_DSN) as conn:
        query = """
        SELECT 
            target_time as time, 
            cmd_charge_kw, 
            cmd_discharge_kw, 
            expected_soc_kwh, 
            expected_grid_buy_kw, 
            expected_grid_sell_kw
        FROM dispatch_plans
        ORDER BY target_time ASC;
        """
        return pd.read_sql(query, conn, index_col='time')

# --- Sidebar ---
st.sidebar.header("Optimization Settings")
alpha = st.sidebar.slider("Degradation Penalty (α)", 0.0, 5.0, 1.5, 0.1)

if st.sidebar.button("🚀 Run Optimization"):
    with st.status("Running optimization pipeline..."):
        st.write("Loading data from database...")
        time_series, battery_params = load_data()
        
        st.write("Building Pyomo model...")
        hyper_params = Hyperparameters(alpha=alpha)
        model = create_microgrid_model(
            time_series=time_series,
            battery_params=battery_params,
            hyper_params=hyper_params
        )
        
        st.write("Solving with IPOPT...")
        solution = run_optimization_and_get_results(model=model)
        
        st.write("Saving results to database...")
        save_data(solution)
        
    st.sidebar.success("Optimization complete! ✅")
    st.rerun()

# --- Main Dashboard ---
try:
    # 1. Load Data
    telemetry, battery_params = load_data()
    
    # 2. Try to Load Dispatch Plan
    try:
        dispatch = get_dispatch_plans()
    except Exception:
        dispatch = pd.DataFrame()

    if telemetry.empty:
        st.warning("No telemetry data found in the database. Please run `pixi run data` first.")
    else:
        # Create tabs for different views
        tab1, tab2 = st.tabs(["Overview", "Raw Data"])

        with tab1:
            # 1. Price Plot
            st.subheader("💰 Energy Prices")
            fig_prices = go.Figure()
            fig_prices.add_trace(go.Scatter(x=telemetry.index, y=telemetry['price_buy'], name="Price Buy ($/kWh)", line=dict(color='red', width=2)))
            fig_prices.add_trace(go.Scatter(x=telemetry.index, y=telemetry['price_sell'], name="Price Sell ($/kWh)", line=dict(color='green', width=2)))
            fig_prices.update_layout(
                height=300, 
                margin=dict(l=20, r=20, t=20, b=20),
                yaxis_title="Price ($/kWh)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_prices, use_container_width=True)

            # 2. Power Consumption/Generation Plot
            st.subheader("🔌 Load & Solar Generation")
            fig_power = go.Figure()
            fig_power.add_trace(go.Scatter(x=telemetry.index, y=telemetry['load_kw'], name="Load (kW)", fill='tozeroy', line=dict(color='blue')))
            fig_power.add_trace(go.Scatter(x=telemetry.index, y=telemetry['solar_kw'], name="Solar (kW)", fill='tozeroy', line=dict(color='orange')))
            fig_power.update_layout(
                height=300, 
                margin=dict(l=20, r=20, t=20, b=20),
                yaxis_title="Power (kW)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_power, use_container_width=True)

            # 3. Optimization Results (if available)
            if not dispatch.empty:
                st.divider()
                st.subheader("🔋 Battery Strategy")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("**State of Charge**")
                    fig_soc = go.Figure()
                    fig_soc.add_trace(go.Scatter(x=dispatch.index, y=dispatch['expected_soc_kwh'], name="SOC (kWh)", fill='tozeroy', line=dict(color='cyan')))
                    fig_soc.add_hline(y=battery_params.max_capacity_kwh, line_dash="dot", line_color="gray", annotation_text="Max Cap")
                    fig_soc.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), yaxis_title="Energy (kWh)")
                    st.plotly_chart(fig_soc, use_container_width=True)

                with col2:
                    st.markdown("**Dispatch Commands**")
                    fig_cmds = go.Figure()
                    fig_cmds.add_trace(go.Bar(x=dispatch.index, y=dispatch['cmd_charge_kw'], name="Charge (kW)", marker_color='blue'))
                    fig_cmds.add_trace(go.Bar(x=dispatch.index, y=-dispatch['cmd_discharge_kw'], name="Discharge (kW)", marker_color='orange'))
                    fig_cmds.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), yaxis_title="Power (kW)", barmode='relative')
                    st.plotly_chart(fig_cmds, use_container_width=True)

                st.subheader("🌐 Grid Interaction")
                fig_grid = go.Figure()
                fig_grid.add_trace(go.Scatter(x=dispatch.index, y=dispatch['expected_grid_buy_kw'], name="Grid Buy (kW)", line=dict(color='red')))
                fig_grid.add_trace(go.Scatter(x=dispatch.index, y=-dispatch['expected_grid_sell_kw'], name="Grid Sell (kW)", line=dict(color='green')))
                fig_grid.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), yaxis_title="Power (kW)")
                st.plotly_chart(fig_grid, use_container_width=True)
            else:
                st.info("No dispatch plan found. Click 'Run Optimization' in the sidebar to generate one.")

        with tab2:
            st.subheader("Telemetry Data")
            st.dataframe(telemetry, use_container_width=True)
            if not dispatch.empty:
                st.subheader("Dispatch Plan")
                st.dataframe(dispatch, use_container_width=True)

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.exception(e)
