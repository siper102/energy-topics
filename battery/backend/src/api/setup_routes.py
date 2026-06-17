import os
import logging
import psycopg
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import DB_DSN

router = APIRouter()
logger = logging.getLogger(__name__)

class SetupBase(BaseModel):
    name: str
    max_capacity_kwh: float
    max_power_kw: float
    efficiency_charge: float
    efficiency_discharge: float
    initial_soc_kwh: float = 0.0
    lat: float
    lon: float
    peak_power_kw: float
    tilt: float = 35
    azimuth: float = 0

class SetupCreate(SetupBase):
    pass

class Setup(SetupBase):
    id: int

@router.get("/", response_model=List[Setup])
async def list_setups():
    try:
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, max_capacity_kwh, max_power_kw, efficiency_charge, 
                           efficiency_discharge, initial_soc_kwh, lat, lon, peak_power_kw, tilt, azimuth 
                    FROM setups ORDER BY id ASC
                """)
                rows = cur.fetchall()
                return [
                    Setup(
                        id=row[0], name=row[1], max_capacity_kwh=float(row[2]), 
                        max_power_kw=float(row[3]), efficiency_charge=float(row[4]),
                        efficiency_discharge=float(row[5]), initial_soc_kwh=float(row[6]),
                        lat=float(row[7]), lon=float(row[8]), peak_power_kw=float(row[9]),
                        tilt=float(row[10]), azimuth=float(row[11])
                    ) for row in rows
                ]
    except Exception as e:
        logger.error(f"Failed to list setups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Setup)
async def create_setup(setup: SetupCreate):
    try:
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO setups (name, max_capacity_kwh, max_power_kw, efficiency_charge, 
                                      efficiency_discharge, initial_soc_kwh, lat, lon, peak_power_kw, tilt, azimuth)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (setup.name, setup.max_capacity_kwh, setup.max_power_kw, setup.efficiency_charge,
                      setup.efficiency_discharge, setup.initial_soc_kwh, setup.lat, setup.lon, 
                      setup.peak_power_kw, setup.tilt, setup.azimuth))
                new_id = cur.fetchone()[0]
                conn.commit()
                return Setup(id=new_id, **setup.model_dump())
    except Exception as e:
        logger.error(f"Failed to create setup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{setup_id}", response_model=Setup)
async def get_setup(setup_id: int):
    try:
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, max_capacity_kwh, max_power_kw, efficiency_charge, 
                           efficiency_discharge, initial_soc_kwh, lat, lon, peak_power_kw, tilt, azimuth 
                    FROM setups WHERE id = %s
                """, (setup_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Setup not found")
                return Setup(
                    id=row[0], name=row[1], max_capacity_kwh=float(row[2]), 
                    max_power_kw=float(row[3]), efficiency_charge=float(row[4]),
                    efficiency_discharge=float(row[5]), initial_soc_kwh=float(row[6]),
                    lat=float(row[7]), lon=float(row[8]), peak_power_kw=float(row[9]),
                    tilt=float(row[10]), azimuth=float(row[11])
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get setup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
