# diff/

**Owner:** P2 Replan & quality lead

**Stack:** Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · reason ledger -> kept / moved / broken

| File | Purpose |
|------|---------|
| `diff/__init__.py` | diff package |
| `diff/classify.py` | classify(): kept (same vehicle, ETA within +-5) / moved / broken, reading the reason ledger |
| `diff/sentences.py` | one human sentence per diff row from its cause code |
