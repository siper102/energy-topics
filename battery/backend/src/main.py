from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import routers
from api.setup_routes import router as setup_router
from api.data_routes import router as data_router
from api.job_routes import router as job_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Battery Optimization Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(setup_router, prefix="/api/setups", tags=["Setups"])
app.include_router(data_router, prefix="/api/data", tags=["Data"])
app.include_router(job_router, prefix="/api/jobs", tags=["Jobs"])


@app.get("/")
def read_root():
    return {"message": "Battery Optimization Unified Backend"}
