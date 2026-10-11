# contract/

**Owner:** P1 Algorithm lead

**Stack:** Python 3.12 · Pydantic v2 (models ARE the contract: -> OpenAPI -> TypeScript via openapi-typescript) · JSON fixtures

| File | Purpose |
|------|---------|
| `contract/__init__.py` | re-export of the frozen contract models and function signatures |
| `contract/models.py` | Pydantic v2 models = the single contract (DRAFT until contract-v1) |
| `contract/signatures.py` | stub signatures so every lane can import from minute one |
| `contract/fixtures/scenario_micro.json` | hand-checkable micro-scenario: 3 vehicles, 8 deliveries |
| `contract/fixtures/plan_micro.json` | expected plan for the micro-scenario (hand-verified arrivals) |
| `contract/fixtures/proposal_failure.json` | text-derived vehicle-failure proposal with assumptions |
| `contract/fixtures/replan_result_closure.json` | golden replan result for a road closure |
| `contract/fixtures/validation_report_ok.json` | golden all-green validation report |
