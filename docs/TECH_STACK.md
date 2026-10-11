# Technology stack

| Layer | Pick | Why | Where |
|---|---|---|---|
| Runtime | Python 3.12 | Stable typed backend runtime | `pyproject.toml` |
| API | FastAPI, Uvicorn, Pydantic v2 | Typed HTTP contracts and local serving | `api/`, `contract/` |
| Solver | Pure Python heuristic | Explainable, deterministic, no runtime service dependency | `engine/`, `replan/` |
| Verification | pytest, Hypothesis, Ruff | Regression, invariant, property, and style checks | `tests/`, `verify/` |
| Frontend | Vite, React, TypeScript, Tailwind | Local interactive planning UI | `frontend/` |
| State | In-process store | Offline demo and deterministic local behavior | `api/store.py` |
| Optional integrations | OR-Tools and Anthropic | Benchmarks and explicitly flagged text extraction only | `engine/benchmarks/`, `nlp/` |