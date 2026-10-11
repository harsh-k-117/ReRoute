"""api/main.py - FastAPI app: routers, mock-mode switch, static mount of frontend/dist

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · FastAPI · Pydantic v2 · uvicorn · mock mode serves fixtures · serves the built UI (frontend/dist)
Spec : mock mode
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.routes import disruptions, plan, proposals, scenarios, state, validate

app = FastAPI(title="ReRoute", version="0.1.0")

for module in (scenarios, plan, state, validate, disruptions, proposals):
    app.include_router(module.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# FastAPI serves the built UI: one offline command (make demo). No CDNs.
_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="ui")
