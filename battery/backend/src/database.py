import pandas as pd
from optimization.model_factory import BatteryParams
import os
import psycopg
import logging
from sqlalchemy import text
from sqlmodel import Session, create_engine

logger = logging.getLogger(__name__)

# Raw DSN for psycopg (v3)
DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:postgres@timescaledb:5432/battery")

# SQLAlchemy Engine (Explicitly use psycopg v3 dialect)
# SQLAlchemy needs 'postgresql+psycopg://' to use psycopg v3
engine_url = DB_DSN.replace("postgresql://", "postgresql+psycopg://")
engine = create_engine(engine_url)


def get_session():
    with Session(engine) as session:
        yield session


def load_battery_params(setup_id: int) -> BatteryParams:
    """Fetches static battery parameters for a specific setup."""
    from models import Setup

    with Session(engine) as session:
        setup = session.get(Setup, setup_id)
        if not setup:
            raise ValueError(f"No setup found in database (ID: {setup_id}).")

        return BatteryParams(
            max_capacity_kwh=float(setup.max_capacity_kwh),
            max_power_kw=float(setup.max_power_kw),
            efficiency_charge=float(setup.efficiency_charge),
            efficiency_discharge=float(setup.efficiency_discharge),
            initial_soc_kwh=float(setup.initial_soc_kwh),
        )


def load_data(setup_id: int = None) -> tuple[pd.DataFrame, BatteryParams]:
    """
    Fetches the latest telemetry and physical parameters for a specific setup.
    Uses the SQLAlchemy engine for connection pooling.
    """
    query_str = """
    SELECT
        time,
        load_kw,
        solar_kw,
        temp_c,
        price_buy_usd_per_kwh as price_buy,
        price_sell_usd_per_kwh as price_sell
    FROM sensor_telemetry
    """

    if setup_id:
        query_str += " WHERE setup_id = :setup_id"

    query_str += " ORDER BY time ASC;"

    # Using the SQLAlchemy engine directly with Pandas
    with engine.connect() as conn:
        df_telemetry = pd.read_sql(
            text(query_str),
            conn,
            params={"setup_id": setup_id} if setup_id else {},
            index_col="time",
        )

    if df_telemetry.empty:
        raise ValueError(
            f"No time-series data found for setup_id {setup_id}. Please run a job first."
        )

    params = load_battery_params(setup_id) if setup_id else load_battery_params(1)

    return df_telemetry, params


def save_telemetry_data(df: pd.DataFrame, setup_id: int):
    """Saves input telemetry data to TimescaleDB (Uses raw psycopg COPY for speed)."""
    if df.empty:
        return

    df_reset = df.reset_index()
    if "time" not in df_reset.columns and "index" in df_reset.columns:
        df_reset.rename(columns={"index": "time"}, inplace=True)

    df_reset["setup_id"] = setup_id

    rename_map = {
        "price_buy": "price_buy_usd_per_kwh",
        "price_sell": "price_sell_usd_per_kwh",
        "realized_price_buy": "realized_price_buy_usd_per_kwh",
        "realized_price_sell": "realized_price_sell_usd_per_kwh",
    }
    cols_to_keep = [
        "time",
        "setup_id",
        "load_kw",
        "solar_kw",
        "price_buy_usd_per_kwh",
        "price_sell_usd_per_kwh",
        "realized_price_buy_usd_per_kwh",
        "realized_price_sell_usd_per_kwh",
        "temp_c",
    ]

    for old, new in rename_map.items():
        if old in df_reset.columns:
            df_reset.rename(columns={old: new}, inplace=True)

    df_db_ready = df_reset[[c for c in cols_to_keep if c in df_reset.columns]]

    _atomic_upsert(df_db_ready, "sensor_telemetry", ["time", "setup_id"])


def save_dispatch_plan(df: pd.DataFrame, setup_id: int):
    """Saves optimized dispatch plan to TimescaleDB (Uses raw psycopg COPY for speed)."""
    if df.empty:
        return

    df_reset = df.reset_index()
    if "time" not in df_reset.columns and "index" in df_reset.columns:
        df_reset.rename(columns={"index": "time"}, inplace=True)

    df_reset["setup_id"] = setup_id

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
    """Generic atomic UPSERT helper using raw psycopg."""
    columns_str = ", ".join(df.columns)
    records = df.values.tolist()

    try:
        # Raw psycopg (v3) connection
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                temp_table = f"temp_{table_name}"
                cur.execute(
                    f"CREATE TEMP TABLE {temp_table} (LIKE {table_name} INCLUDING ALL) ON COMMIT DROP;"
                )

                copy_query = f"COPY {temp_table} ({columns_str}) FROM STDIN"
                with cur.copy(copy_query) as copy:
                    for row in records:
                        copy.write_row(row)

                update_cols = [col for col in df.columns if col not in pk_cols]
                set_clause = ", ".join(
                    [f"{col} = EXCLUDED.{col}" for col in update_cols]
                )
                pk_str = ", ".join(pk_cols)

                upsert_query = f"""
                    INSERT INTO {table_name} ({columns_str})
                    SELECT {columns_str} FROM {temp_table}
                    ON CONFLICT ({pk_str}) DO UPDATE
                    SET {set_clause};
                """
                cur.execute(upsert_query)
                conn.commit()
                logger.info(
                    f"✅ Successfully upserted {len(records)} rows into {table_name}."
                )

    except psycopg.Error as e:
        logger.error(f"❌ Database error during upsert into {table_name}: {e}")
        raise
