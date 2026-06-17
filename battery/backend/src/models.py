from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class SetupBase(SQLModel):
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

class Setup(SetupBase, table=True):
    __tablename__ = "setups"
    id: Optional[int] = Field(default=None, primary_key=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to Jobs
    jobs: list["Job"] = Relationship(back_populates="setup")

class JobBase(SQLModel):
    setup_id: Optional[int] = Field(default=None, foreign_key="setups.id")
    type: str
    status: str = "PENDING"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    alpha: Optional[float] = None
    grid_fee: Optional[float] = None
    error_message: Optional[str] = None

class Job(JobBase, table=True):
    __tablename__ = "jobs"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    
    # Relationship back to Setup
    setup: Optional[Setup] = Relationship(back_populates="jobs")
