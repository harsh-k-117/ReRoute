# tests/

**Owner:** P2 Replan & quality lead

**Stack:** pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff

> Acceptance tests start as `xfail`; the green count is the team scoreboard. Per-lane unit tests live in `tests/unit/<lane>/` and are owned by that lane.

| File | Purpose |
|------|---------|
| `tests/conftest.py` | shared pytest fixtures |
| `tests/acceptance/test_initial_plan.py` | initial plan: arrivals, waits, load line, unplaced reasons |
| `tests/acceptance/test_road_closure.py` | closure disruption end to end |
| `tests/acceptance/test_vehicle_failure.py` | failure disruption: orphaned parcels, rescue pickup, nothing after failure |
| `tests/acceptance/test_urgent_delivery.py` | urgent delivery: depot pickup, release time, NEW badge |
| `tests/acceptance/test_text_interpretation.py` | text -> interpret -> preview -> confirm |
| `tests/acceptance/test_confirm_gate.py` | server-enforced confirm gate |
| `tests/acceptance/test_diff_reasons.py` | side-by-side diff: every moved/broken row has a cause |
| `tests/acceptance/test_micro_scenario.py` | hand-checkable micro-scenario (3 vehicles, 8 deliveries) |
| `tests/property/test_fuzz_invariants.py` | Hypothesis: random scenarios x random disruption sequences -> I1-I12 (print seed + replayable JSON) |
| `tests/edge/test_edge_suite.py` | edge suite: failure at t=0 / exactly at stop end / idle vehicle; overlapping closures; replan-of-replan |
| `tests/unit/engine/test_engine_simulate.py` | unit: simulate_route |
| `tests/unit/engine/test_engine_construct.py` | unit: regret-2 insertion |
| `tests/unit/replan/test_replan_snapshot.py` | unit: snapshot / freeze rule |
| `tests/unit/verify/test_verify_validator.py` | unit: validator catches deliberately broken plans |
| `tests/unit/diff/test_diff_classify.py` | unit: kept/moved/broken thresholds |
| `tests/unit/nlp/test_nlp_resolver.py` | unit: exact-match resolver |
| `tests/unit/nlp/test_nlp_time_grammar.py` | unit: time grammar |
| `tests/unit/nlp/test_nlp_hostile_phrasings.py` | 30+ phrasings incl. hostile ones |
| `tests/unit/api/test_api_endpoints.py` | unit: API endpoints in mock mode |
