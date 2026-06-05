from datetime import datetime, timedelta
import pandas as pd
from dataclasses import dataclass
from optimization.model_factory import BatteryParams
import os
import psycopg

DB_DSN = os.getenv(
    "DB_DSN", 
    "postgresql://postgres:postgres@localhost:5432/battery"
)


def load_data(setup_id: int = None) -> tuple[pd.DataFrame, BatteryParams]:
    """
    Fetches the latest telemetry and physical parameters for a specific setup
    from TimescaleDB.
    """
    
    # We use a standard connection for the parameters and pd.read_sql for the series
    with psycopg.connect(DB_DSN) as conn:
        
        # 1. Fetch Time-Series Data (Telemetry)
        # We query the last 24 hours of data for the specific setup
        where_clause = "WHERE setup_id = %s" if setup_id else ""
        params_telemetry = (setup_id,) if setup_id else ()
        
        query = f"""
        SELECT 
            time, 
            load_kw, 
            solar_kw, 
            price_buy_usd_per_kwh as price_buy, 
            price_sell_usd_per_kwh as price_sell
        FROM sensor_telemetry
        {where_clause}
        ORDER BY time ASC;
        """
        
        # pd.read_sql returns a DataFrame perfectly indexed by 'time'
        df_telemetry = pd.read_sql(query, conn, params=params_telemetry, index_col='time')
        
        if df_telemetry.empty:
            raise ValueError(f"No time-series data found for setup_id {setup_id}. Please run data ingestion first.")
        
        if len(df_telemetry) < 2:
            raise ValueError(f"Not enough data points found ({len(df_telemetry)}) for setup_id {setup_id}. At least 2 points are required for optimization.")
        
        # 2. Fetch Static Setup Parameters
        with conn.cursor() as cur:
            if setup_id:
                cur.execute("""
                    SELECT 
                        max_capacity_kwh, 
                        max_power_kw, 
                        efficiency_charge, 
                        efficiency_discharge, 
                        initial_soc_kwh 
                    FROM setups 
                    WHERE id = %s;
                """, (setup_id,))
            else:
                cur.execute("""
                    SELECT 
                        max_capacity_kwh, 
                        max_power_kw, 
                        efficiency_charge, 
                        efficiency_discharge, 
                        initial_soc_kwh 
                    FROM setups 
                    LIMIT 1;
                """)
                
            row = cur.fetchone()
            if not row:
                raise ValueError(f"No setup found in database (ID: {setup_id}).")
                
            params = BatteryParams(
                max_capacity_kwh=float(row[0]),
                max_power_kw=float(row[1]),
                efficiency_charge=float(row[2]),
                efficiency_discharge=float(row[3]),
                initial_soc_kwh=float(row[4])
            )

    return df_telemetry, params

def clear_dispatch_plans(setup_id: int = None):
    """Deletes dispatch plans from the database, optionally filtered by setup_id."""
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            if setup_id:
                cur.execute("DELETE FROM dispatch_plans WHERE setup_id = %s;", (setup_id,))
            else:
                cur.execute("DELETE FROM dispatch_plans;")
            conn.commit()
            print(f"🧹 Cleared existing dispatch plans (setup_id: {setup_id}) from DB.")

def get_available_setups() -> pd.DataFrame:
    """Fetches all available setups from the database."""
    with psycopg.connect(DB_DSN) as conn:
        query = "SELECT id, name, max_capacity_kwh, max_power_kw FROM setups ORDER BY id ASC;"
        return pd.read_sql(query, conn)

def save_data(result: pd.DataFrame, setup_id: int, table_name: str = "dispatch_plans"):
    """Saves the optimized dispatch plan to TimescaleDB."""    
    # 1. Reset index. Since the index is already named "time", 
    # Pandas creates a column named "time" automatically!
    df_reset = result.reset_index()
    df_reset['setup_id'] = setup_id
        
    # 2. Defensively order AND rename columns to match the Database schema
    df_db_ready = df_reset[['time', 'setup_id', 'p_charge_kw', 'p_discharge_kw', 'soc_kwh', 'p_buy_kw', 'p_sell_kw']].rename(
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
                # 4. ATOMIC UPSERT STRATEGY
                # We use a temporary table to stage the data, then perform an atomic 
                # "INSERT ... ON CONFLICT" to avoid race conditions and unique constraint violations.
                temp_table = f"temp_{table_name}"
                cur.execute(f"CREATE TEMP TABLE {temp_table} (LIKE {table_name} INCLUDING ALL) ON COMMIT DROP;")

                columns_str = ", ".join(df_db_ready.columns)
                copy_query = f"COPY {temp_table} ({columns_str}) FROM STDIN"
                    
                with cur.copy(copy_query) as copy:
                    for row in records:
                        copy.write_row(row)
                
                # Perform the atomic UPSERT
                # We update all columns except the primary key (target_time, setup_id)
                update_cols = [col for col in df_db_ready.columns if col not in ['target_time', 'setup_id']]
                set_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_cols])

                upsert_query = f"""
                    INSERT INTO {table_name} ({columns_str})
                    SELECT {columns_str} FROM {temp_table}
                    ON CONFLICT (target_time, setup_id) DO UPDATE
                    SET {set_clause};
                """
                cur.execute(upsert_query)
                    
                conn.commit()
                print(f"✅ Successfully saved {len(records)} optimal dispatch commands to DB (Atomic UPSERT).")
            
    except psycopg.Error as e:
        print(f"❌ Database error during save: {e}")
        raise
