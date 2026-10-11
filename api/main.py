import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.disruptions import router as disruptions_router
from .routes.plan import router as plan_router
from .routes.proposals import router as proposals_router
from .routes.scenarios import router as scenarios_router
from .routes.state import router as state_router
from .routes.upload import router as upload_router
from .routes.validate import router as validate_router

app = FastAPI(title="ReRoute API", version="0.1.0")
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "REROUTE_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(scenarios_router)
app.include_router(plan_router)
app.include_router(state_router)
app.include_router(validate_router)
app.include_router(disruptions_router)
app.include_router(proposals_router)
app.include_router(upload_router)
