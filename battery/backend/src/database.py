from datetime import datetime, timedelta
import pandas as pd
from dataclasses import dataclass
from optimization.model_factory import BatteryParams
import os
import psycopg
import logging

logger = logging.getLogger(__name__)

DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:postgres@localhost:5432/battery")


def load_battery_params(setup_id: int) -> BatteryParams:
    """Fetches static battery parameters for a specific setup."""
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    max_capacity_kwh, 
                    max_power_kw, 
                    efficiency_charge, 
                    efficiency_discharge, 
                    initial_soc_kwh 
                FROM setups 
                WHERE id = %s;
                """,
                (setup_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"No setup found in database (ID: {setup_id}).")

            return BatteryParams(
                max_capacity_kwh=float(row[0]),
                max_power_kw=float(row[1]),
                efficiency_charge=float(row[2]),
                efficiency_discharge=float(row[3]),
                initial_soc_kwh=float(row[4]),
            )


def load_data(setup_id: int = None) -> tuple[pd.DataFrame, BatteryParams]:
    """
    Fetches the latest telemetry and physical parameters for a specific setup
    from TimescaleDB.
    """
    with psycopg.connect(DB_DSN) as conn:
        where_clause = "WHERE setup_id = %s" if setup_id else ""
        params_telemetry = (setup_id,) if setup_id else ()

        query = f"""
        SELECT 
            time, 
            load_kw, 
            solar_kw, 
            temp_c,
            price_buy_usd_per_kwh as price_buy, 
            price_sell_usd_per_kwh as price_sell
        FROM sensor_telemetry
        {where_clause}
        ORDER BY time ASC;
        """

        df_telemetry = pd.read_sql(
            query, conn, params=params_telemetry, index_col="time"
        )

        if df_telemetry.empty:
            raise ValueError(
                f"No time-series data found for setup_id {setup_id}. Please run data ingestion first."
            )

        params = load_battery_params(setup_id) if setup_id else load_battery_params(1)

    return df_telemetry, params


def save_telemetry_data(df: pd.DataFrame, setup_id: int):
    """Saves input telemetry data to TimescaleDB."""
    if df.empty:
        return

    # Reset index to get 'time' column
    df_reset = df.reset_index()
    if 'time' not in df_reset.columns and 'index' in df_reset.columns:
        df_reset.rename(columns={'index': 'time'}, inplace=True)
    
    df_reset['setup_id'] = setup_id

    # Expected schema: time, setup_id, load_kw, solar_kw, price_buy_usd_per_kwh, price_sell_usd_per_kwh, temp_c
    # In the DF from extract_data, we usually have 'price_buy' and 'price_sell'
    rename_map = {
        'price_buy': 'price_buy_usd_per_kwh',
        'price_sell': 'price_sell_usd_per_kwh'
    }
    cols_to_keep = ['time', 'setup_id', 'load_kw', 'solar_kw', 'price_buy_usd_per_kwh', 'price_sell_usd_per_kwh', 'temp_c']
    
    # Ensure columns exist before renaming/selecting
    for old, new in rename_map.items():
        if old in df_reset.columns:
            df_reset.rename(columns={old: new}, inplace=True)
            
    df_db_ready = df_reset[[c for c in cols_to_keep if c in df_reset.columns]]
    
    _atomic_upsert(df_db_ready, "sensor_telemetry", ["time", "setup_id"])


def save_dispatch_plan(df: pd.DataFrame, setup_id: int):
    """Saves optimized dispatch plan to TimescaleDB."""
    if df.empty:
        return

    df_reset = df.reset_index()
    if 'time' not in df_reset.columns and 'index' in df_reset.columns:
        df_reset.rename(columns={'index': 'time'}, inplace=True)
    
    df_reset['setup_id'] = setup_id

    df_db_ready = df_reset[
        [
            "time",
            "setup_id",
            "p_charge_kw",
            "p_discharge_kw",
            "soc_kwh",
            "p_buy_kw",
            "p_sell_kw",
        ]
    ].rename(
        columns={
            "time": "target_time",
            "p_charge_kw": "cmd_charge_kw",
            "p_discharge_kw": "cmd_discharge_kw",
            "soc_kwh": "expected_soc_kwh",
            "p_buy_kw": "expected_grid_buy_kw",
            "p_sell_kw": "expected_grid_sell_kw",
        }
    )

    _atomic_upsert(df_db_ready, "dispatch_plans", ["target_time", "setup_id"])


def _atomic_upsert(df: pd.DataFrame, table_name: str, pk_cols: list[str]):
    """Generic atomic UPSERT helper."""
    columns_str = ", ".join(df.columns)
    records = df.values.tolist()

    try:
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                temp_table = f"temp_{table_name}"
                cur.execute(f"CREATE TEMP TABLE {temp_table} (LIKE {table_name} INCLUDING ALL) ON COMMIT DROP;")

                copy_query = f"COPY {temp_table} ({columns_str}) FROM STDIN"
                with cur.copy(copy_query) as copy:
                    for row in records:
                        copy.write_row(row)

                update_cols = [col for col in df.columns if col not in pk_cols]
                set_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_cols])
                pk_str = ", ".join(pk_cols)

                upsert_query = f"""
                    INSERT INTO {table_name} ({columns_str})
                    SELECT {columns_str} FROM {temp_table}
                    ON CONFLICT ({pk_str}) DO UPDATE
                    SET {set_clause};
                """
                cur.execute(upsert_query)
                conn.commit()
                logger.info(f"✅ Successfully upserted {len(records)} rows into {table_name}.")

    except psycopg.Error as e:
        logger.error(f"❌ Database error during upsert into {table_name}: {e}")
        raise


def save_data(result: pd.DataFrame, setup_id: int):
    """Legacy wrapper for save_dispatch_plan."""
    save_dispatch_plan(result, setup_id)
