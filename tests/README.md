# Tests and acceptance scoreboard

Run all fast checks with `make check`. Run the acceptance suite by itself with
`uv run pytest -q -m acceptance`, or run `uv run python scripts/scoreboard.py` for the
passing/xfail summary.

Phase 3 acceptance cases are marked `xfail` while the corresponding production phases are
unfinished. An xfail is an expected failure and does not fail `make check`; once an
implementation makes the case pass, pytest reports it as XPASS. Remove that test's xfail
marker after reviewing the implementation so it counts as a normal pass on the scoreboard.

Test docstrings cite the requirement IDs (R1–R15) and invariant IDs (I1–I12) they cover.
`tests/conftest.py` provides the hand-checked micro-scenario, plan, JSON fixture loader,
FastAPI client factory, and malformed-plan mutations for validator work in Phase 6.

The micro-scenario sequence is fixed so the simulator can be compared against exact arrivals,
waits, service starts, departures, and loads in `contract/fixtures/plan_micro.json`. Its
arithmetic is written out in `contract/fixtures/MICRO_WALKTHROUGH.md`.
