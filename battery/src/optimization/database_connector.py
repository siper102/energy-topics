from datetime import datetime, timedelta
import pandas as pd
from dataclasses import dataclass
from model_factory import BatteryParams
import os
import psycopg

# ==========================================
# 1. HARDWARE CONSTRAINTS (Mocking Table 1)
# ==========================================
# Normally queried from: microgrid_components
battery_params = {
    "max_capacity_kwh": 13.5,  # e.g., Tesla Powerwall
    "max_power_kw": 5.0,       # Max charge/discharge rate
    "efficiency_charge": 0.95,   # Charging efficiency
    "efficiency_discharge": 0.95,   # Discharging efficiency
    "initial_soc_kwh": 6.75    # Assume battery starts half full
}

DB_DSN = os.getenv(
    "DB_DSN", 
    "postgresql://postgres:postgres@localhost:5432/battery"
)


def load_data() -> tuple[pd.DataFrame, BatteryParams]:
    """
    Fetches the latest telemetry and physical battery parameters 
    from TimescaleDB.
    """
    
    # We use a standard connection for the parameters and pd.read_sql for the series
    with psycopg.connect(DB_DSN) as conn:
        
        # 1. Fetch Time-Series Data (Telemetry)
        # We query the last 24 hours of data
        query = """
        SELECT 
            time, 
            load_kw, 
            solar_kw, 
            price_buy_usd_per_kwh as price_buy, 
            price_sell_usd_per_kwh as price_sell
        FROM sensor_telemetry
        ORDER BY time ASC;
        """
        
        # pd.read_sql returns a DataFrame perfectly indexed by 'time'
        df_telemetry = pd.read_sql(query, conn, index_col='time')
        
        # 2. Fetch Static Battery Parameters
        # We just grab the most recent entry from our parameters table
        params = BatteryParams(**battery_params)

    return df_telemetry, params

def save_data(result: pd.DataFrame, table_name: str = "dispatch_plans"):
    """Saves the optimized dispatch plan to TimescaleDB."""    
    # 1. Reset index. Since the index is already named "time", 
    # Pandas creates a column named "time" automatically!
    df_reset = result.reset_index()
        
    # 2. Defensively order AND rename columns to match the Database schema
    df_db_ready = df_reset[['time', 'p_charge_kw', 'p_discharge_kw', 'soc_kwh', 'p_buy_kw', 'p_sell_kw']].rename(
        columns={
            'time': 'target_time',
            'p_charge_kw': 'cmd_charge_kw',
            'p_discharge_kw': 'cmd_discharge_kw',
            'soc_kwh': 'expected_soc_kwh',
            'p_buy_kw': 'expected_grid_buy_kw',
            'p_sell_kw': 'expected_grid_sell_kw'
        }
    )
        
    # 3. Convert DataFrame to a list of lists for psycopg
    records = df_db_ready.values.tolist()

    try:
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                # 4. DYNAMIC SQL MAGIC
                columns_str = ", ".join(df_db_ready.columns)
                copy_query = f"COPY {table_name} ({columns_str}) FROM STDIN"
                    
                with cur.copy(copy_query) as copy:
                    for row in records:
                        copy.write_row(row)
                    
                conn.commit()
                print(f"✅ Successfully saved {len(records)} optimal dispatch commands to DB.")
            
    except psycopg.Error as e:
        print(f"❌ Database error during save: {e}")
        raise
