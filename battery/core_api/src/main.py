from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.data_routes import router as data_router
from api.optimization_routes import router as opt_router

app = FastAPI(title="Battery Platform Core API")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(data_router, prefix="/api/data", tags=["Data"])
app.include_router(opt_router, prefix="/api/optimization", tags=["Optimization"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Battery Optimization Platform API"}
