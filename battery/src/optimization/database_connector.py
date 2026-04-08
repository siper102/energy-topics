from datetime import datetime, timedelta
import pandas as pd
from dataclasses import dataclass
from model_factory import BatteryParams
import os
import psycopg

DB_DSN = os.getenv(
    "DB_DSN", 
    "postgresql://postgres:postgres@localhost:5432/battery"
)


def load_data(battery_id: int = None) -> tuple[pd.DataFrame, BatteryParams]:
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
        with conn.cursor() as cur:
            if battery_id:
                cur.execute("""
                    SELECT 
                        max_capacity_kwh, 
                        max_power_kw, 
                        efficiency_charge, 
                        efficiency_discharge, 
                        initial_soc_kwh 
                    FROM battery_parameters 
                    WHERE id = %s;
                """, (battery_id,))
            else:
                cur.execute("""
                    SELECT 
                        max_capacity_kwh, 
                        max_power_kw, 
                        efficiency_charge, 
                        efficiency_discharge, 
                        initial_soc_kwh 
                    FROM battery_parameters 
                    LIMIT 1;
                """)
                
            row = cur.fetchone()
            if not row:
                raise ValueError(f"No battery parameters found in database (ID: {battery_id}).")
                
            params = BatteryParams(
                max_capacity_kwh=float(row[0]),
                max_power_kw=float(row[1]),
                efficiency_charge=float(row[2]),
                efficiency_discharge=float(row[3]),
                initial_soc_kwh=float(row[4])
            )

    return df_telemetry, params

def clear_dispatch_plans():
    """Deletes all existing dispatch plans from the database."""
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM dispatch_plans;")
            conn.commit()
            print("🧹 Cleared existing dispatch plans from DB.")

def get_available_batteries() -> pd.DataFrame:
    """Fetches all available batteries from the database."""
    with psycopg.connect(DB_DSN) as conn:
        query = "SELECT id, max_capacity_kwh, max_power_kw FROM battery_parameters ORDER BY id ASC;"
        return pd.read_sql(query, conn)

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
