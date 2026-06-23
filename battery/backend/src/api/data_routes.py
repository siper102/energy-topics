import logging
import psycopg
import pandas as pd
from typing import Optional
from fastapi import APIRouter, HTTPException
from database import DB_DSN

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard-data")
async def get_dashboard_data(
    setup_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None
):
    """
    Fetches the latest telemetry and dispatch plans for the dashboard.
    """
    try:
        with psycopg.connect(DB_DSN) as conn:
            where_telemetry = "WHERE setup_id = %s"
            where_plans = "WHERE setup_id = %s"
            params_telemetry = [setup_id]
            params_plans = [setup_id]

            if start_date and end_date:
                real_end = f"{end_date} 23:59:59"
                where_telemetry += " AND time >= %s AND time <= %s"
                where_plans += " AND target_time >= %s AND target_time <= %s"
                params_telemetry.extend([start_date, real_end])
                params_plans.extend([start_date, real_end])

            query_telemetry = f"""
            SELECT
                time,
                load_kw,
                solar_kw,
                price_buy_usd_per_kwh,
                price_sell_usd_per_kwh,
                COALESCE(realized_price_buy_usd_per_kwh, price_buy_usd_per_kwh) as realized_price_buy_usd_per_kwh,
                COALESCE(realized_price_sell_usd_per_kwh, price_sell_usd_per_kwh) as realized_price_sell_usd_per_kwh
            FROM sensor_telemetry
            {where_telemetry}
            ORDER BY time ASC;
            """

            query_plans = f"""
            SELECT target_time, cmd_charge_kw, cmd_discharge_kw, expected_soc_kwh, expected_grid_buy_kw, expected_grid_sell_kw
            FROM dispatch_plans
            {where_plans}
            ORDER BY target_time ASC;
            """

            df_telemetry = pd.read_sql(query_telemetry, conn, params=params_telemetry)
            df_plans = pd.read_sql(query_plans, conn, params=params_plans)

            df_telemetry["time"] = pd.to_datetime(df_telemetry["time"])
            df_plans["target_time"] = pd.to_datetime(df_plans["target_time"])

            if not df_telemetry.empty:
                min_time = df_telemetry["time"].min()
                max_time = df_telemetry["time"].max()
                span_days = (max_time - min_time).days

                # Determine resampling rule
                if span_days > 180:
                    rule = "ME"  # Monthly (End of Month)
                elif span_days > 30:
                    rule = "W"  # Weekly
                elif span_days > 7:
                    rule = "D"  # Daily
                else:
                    rule = None

                if rule:
                    # Resample telemetry
                    df_telemetry = df_telemetry.set_index("time")
                    df_telemetry = df_telemetry.resample(rule).mean()
                    df_telemetry = df_telemetry.reset_index()

                    # Resample plans
                    if not df_plans.empty:
                        df_plans = df_plans.set_index("target_time")
                        df_plans = df_plans.resample(rule).mean()
                        df_plans = df_plans.reset_index()

            return {
                "telemetry": df_telemetry.to_dict(orient="records"),
                "plans": df_plans.to_dict(orient="records"),
            }

    except Exception as e:
        logger.error(f"Failed to fetch dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
