import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from database import get_session
from models import Setup, SetupBase

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Setup])
async def list_setups(session: Session = Depends(get_session)):
    try:
        statement = select(Setup).order_by(Setup.id)
        results = session.exec(statement).all()
        return results
    except Exception as e:
        logger.error(f"Failed to list setups: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

@router.post("/", response_model=Setup)
async def create_setup(setup_data: SetupBase, session: Session = Depends(get_session)):
    try:
        new_setup = Setup.model_validate(setup_data)
        session.add(new_setup)
        session.commit()
        session.refresh(new_setup)
        return new_setup
    except Exception as e:
        logger.error(f"Failed to create setup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{setup_id}", response_model=Setup)
async def get_setup(setup_id: int, session: Session = Depends(get_session)):
    setup = session.get(Setup, setup_id)
    if not setup:
        raise HTTPException(status_code=404, detail="Setup not found")
    return setup
