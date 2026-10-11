# api/

**Owner:** P3 Integration & language lead

**Stack:** Python 3.12 · FastAPI · Pydantic v2 · uvicorn · mock mode serves fixtures · serves the built UI (frontend/dist)

| File | Purpose |
|------|---------|
| `api/__init__.py` | FastAPI app package |
| `api/main.py` | FastAPI app: routers, mock-mode switch, static mount of frontend/dist |
| `api/settings.py` | env-driven settings (mock mode, LLM flag, transfer minutes) |
| `api/mock.py` | mock mode: serve golden fixtures from every endpoint so UI never waits for the engine |
| `api/store.py` | session + plan-version store with undo |
| `api/gate.py` | server-enforced confirm gate: 409 without confirm, 422 on unknown place |
| `api/routes/__init__.py` | route modules |
| `api/routes/scenarios.py` | GET /scenarios, GET /scenarios/{name} |
| `api/routes/plan.py` | POST /plan/initial |
| `api/routes/state.py` | GET /state (current plan version, vehicle states at `now`) |
| `api/routes/validate.py` | POST /validate (independent validator) |
| `api/routes/disruptions.py` | POST /disruptions/preview, POST /disruptions/interpret |
| `api/routes/proposals.py` | POST /proposals/{id}/confirm, POST /proposals/{id}/discard (gate enforced server-side) |
