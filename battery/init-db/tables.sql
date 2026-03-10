-- Use timescaledb extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ==========================================
-- 1. CONFIGURATION TABLE (Standard Postgres)
-- ==========================================
-- Holds the physical constraints of the hardware. 
-- This is NOT a hypertable because it doesn't grow over time.
CREATE TABLE battery_parameters (
    id SERIAL PRIMARY KEY,
    max_capacity_kwh NUMERIC NOT NULL,
    max_power_kw NUMERIC NOT NULL,
    efficiency_charge NUMERIC NOT NULL,
    efficiency_discharge NUMERIC NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- 2. INPUTS (Time-series Hypertable)
-- ==========================================
-- Split the price into buy and sell to match the optimization model
CREATE TABLE sensor_telemetry (
    time TIMESTAMPTZ NOT NULL,
    load_kw NUMERIC NOT NULL,
    solar_kw NUMERIC NOT NULL,
    price_buy_usd_per_kwh NUMERIC NOT NULL,
    price_sell_usd_per_kwh NUMERIC NOT NULL
);

-- ==========================================
-- 3. OUTPUTS (Time-series Hypertable)
-- ==========================================
-- I added the grid expected values here. While the battery only cares about 
-- charge/discharge commands, storing the expected grid behavior is crucial 
-- for auditing if the solver actually saved you money later!
CREATE TABLE dispatch_plans (
    target_time TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cmd_charge_kw NUMERIC NOT NULL,
    cmd_discharge_kw NUMERIC NOT NULL,
    expected_soc_kwh NUMERIC NOT NULL,
    expected_grid_buy_kw NUMERIC NOT NULL,
    expected_grid_sell_kw NUMERIC NOT NULL
);

-- Convert the time-series tables to hypertables
SELECT create_hypertable('sensor_telemetry', 'time');
SELECT create_hypertable('dispatch_plans', 'target_time');