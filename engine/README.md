# engine/

**Owner:** P1 Algorithm lead

**Stack:** Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · custom solver: regret-2 insertion + ruin-and-recreate (no solver dependency; OR-Tools only in benchmarks)

| File | Purpose |
|------|---------|
| `engine/__init__.py` | engine package: simulator + solver |
| `engine/travel.py` | time-dependent travel function over the matrix + closure rule (D4) |
| `engine/simulate.py` | simulate_route: ONE source of truth for arrival, wait, start, depart, load-after, violations |
| `engine/prescreen.py` | reject impossible deliveries up front with a reason |
| `engine/objective.py` | lexicographic objective: weighted broken -> moved/shifted -> travel + wait (D6) + stability weight |
| `engine/construct.py` | build_plan + insert_deliveries: parallel regret-2 insertion with cached best insertions |
| `engine/improve.py` | ruin-and-recreate: remove a related cluster (10-25%), reinsert by regret, keep if better |
| `engine/diagnose.py` | diagnose_unplaced: per-vehicle binding constraint + 'what would it take' hint (star) |
| `engine/trace.py` | decision trace, e.g. 'cheapest feasible slot +6 min; runner-up V3 +11' (star) |
| `engine/benchmarks/__init__.py` | benchmarks package (not imported by runtime code) |
| `engine/benchmarks/bruteforce.py` | brute-force enumeration oracle on tiny instances -> optimality-gap number |
| `engine/benchmarks/ortools_bench.py` | OR-Tools comparison, benchmarks ONLY (star; optional extra `bench`) |
