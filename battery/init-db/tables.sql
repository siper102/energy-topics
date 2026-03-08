-- Use tamescaledb extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- The Inputs (Time-series for input)
CREATE TABLE sensor_telemetry (
    time TIMESTAMPTZ NOT NULL,
    load_kw NUMERIC NOT NULL,
    solar_kw NUMERIC NOT NULL,
    price_usd_per_kwh NUMERIC NOT NULL
);

-- The Outputs (Decisions made by your IPOPT solver)
CREATE TABLE dispatch_plans (
    target_time TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cmd_charge_kw NUMERIC NOT NULL,
    cmd_discharge_kw NUMERIC NOT NULL,
    expected_soc_kwh NUMERIC NOT NULL
);

-- Convert to hypertables
SELECT create_hypertable('sensor_telemetry', 'time');
SELECT create_hypertable('dispatch_plans', 'target_time');
