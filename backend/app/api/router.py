from fastapi import APIRouter
from app.api import auth, assets, telemetry, dispatch, carbon, health

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(assets.sites_router, prefix="/sites", tags=["Sites"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
api_router.include_router(dispatch.router, prefix="/dispatch", tags=["Dispatch"])
api_router.include_router(dispatch.curtailment_router, prefix="/curtailment", tags=["Curtailment"])
api_router.include_router(carbon.router, prefix="/carbon", tags=["Carbon Credits"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(health.maintenance_router, prefix="/maintenance", tags=["Maintenance"])
