-- Use timescaledb extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ==========================================
-- 1. SETUPS TABLE (Standard Postgres)
-- ==========================================
-- Holds the physical constraints of the hardware and location.
CREATE TABLE setups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    -- Battery Parameters
    max_capacity_kwh NUMERIC NOT NULL,
    max_power_kw NUMERIC NOT NULL,
    efficiency_charge NUMERIC NOT NULL,
    efficiency_discharge NUMERIC NOT NULL,
    initial_soc_kwh NUMERIC NOT NULL DEFAULT 0.0,
    -- Solar Parameters
    lat NUMERIC NOT NULL,
    lon NUMERIC NOT NULL,
    peak_power_kw NUMERIC NOT NULL,
    tilt NUMERIC NOT NULL DEFAULT 35,
    azimuth NUMERIC NOT NULL DEFAULT 0, -- 0 = South
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed initial setups
INSERT INTO setups (name, max_capacity_kwh, max_power_kw, efficiency_charge, efficiency_discharge, initial_soc_kwh, lat, lon, peak_power_kw, tilt, azimuth)
VALUES 
    ('Default Setup', 13.5, 5.0, 0.95, 0.95, 0.0, 51.26, 6.84, 5.0, 35, 0),
    ('Large Battery (Tesla Megapack)', 100.0, 25.0, 0.98, 0.98, 0.0, 51.26, 6.84, 15.0, 35, 0);

-- ==========================================
-- 2. INPUTS (Time-series Hypertable)
-- ==========================================
CREATE TABLE sensor_telemetry (
    time TIMESTAMPTZ NOT NULL,
    setup_id INTEGER NOT NULL REFERENCES setups(id),
    load_kw NUMERIC NOT NULL,
    solar_kw NUMERIC NOT NULL,
    price_buy_usd_per_kwh NUMERIC NOT NULL,
    price_sell_usd_per_kwh NUMERIC NOT NULL,
    PRIMARY KEY (time, setup_id)
);

-- ==========================================
-- 3. OUTPUTS (Time-series Hypertable)
-- ==========================================
CREATE TABLE dispatch_plans (
    target_time TIMESTAMPTZ NOT NULL,
    setup_id INTEGER NOT NULL REFERENCES setups(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cmd_charge_kw NUMERIC NOT NULL,
    cmd_discharge_kw NUMERIC NOT NULL,
    expected_soc_kwh NUMERIC NOT NULL,
    expected_grid_buy_kw NUMERIC NOT NULL,
    expected_grid_sell_kw NUMERIC NOT NULL,
    PRIMARY KEY (target_time, setup_id)
);

-- Convert the time-series tables to hypertables
-- Note: In TimescaleDB, the partitioning column (time) must be part of the PK.
SELECT create_hypertable('sensor_telemetry', 'time');
SELECT create_hypertable('dispatch_plans', 'target_time');

-- ==========================================
-- 4. JOBS TRACKING (Standard Postgres)
-- ==========================================
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    setup_id INTEGER REFERENCES setups(id),
    type VARCHAR(50) NOT NULL, -- e.g., 'FULL_RUN', 'INGEST', 'OPTIMIZE'
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'RUNNING', 'SUCCESS', 'FAILURE'
    start_date DATE,
    end_date DATE,
    alpha NUMERIC,
    grid_fee NUMERIC,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);
