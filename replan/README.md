# replan/

**Owner:** P2 Replan & quality lead

**Stack:** Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · snapshot(now) -> freeze -> apply -> repair/eject -> reinsert -> improve

| File | Purpose |
|------|---------|
| `replan/__init__.py` | replanning package |
| `replan/snapshot.py` | snapshot(plan, now): frozen prefix, ready location/time, on-board load, breakdown site |
| `replan/freeze.py` | freeze rule helpers (D5); frozen stops must be byte-identical (I6) |
| `replan/apply.py` | apply a disruption: time-dependent travel, vehicle availability, orphaned parcels + rescue pickups |
| `replan/repair.py` | re-simulate free suffixes with windows softened, fix locally, eject remaining violators |
| `replan/ledger.py` | reason ledger: completed | vehicle_failed | closure_delay | displaced_by_urgent | knock_on | no_feasible_slot |
| `replan/replan.py` | replan(): one entry point for closure, vehicle failure, urgent delivery |
