# verify/

**Owner:** P2 Replan & quality lead

**Stack:** Python 3.12 · stdlib + contract models ONLY. MUST NOT import the engine's simulator (independent validator) · pytest · Hypothesis

> **Independence rule:** nothing in `verify/` may import `engine/`. The validator is written from the spec.

| File | Purpose |
|------|---------|
| `verify/__init__.py` | independent validator package (does NOT import engine) |
| `verify/invariants.py` | I1-I12 checks written from the spec, not from the engine |
| `verify/validator.py` | validate(): hard gate before any plan is shown or committed |
| `verify/report.py` | ValidationReport assembly + human-readable summary for the Verify panel |
