# ReRoute — Phase-Wise Agent Build Prompts

A sequence of copy-paste prompts for a coding agent (Claude Code recommended) that builds **ReRoute**: a delivery-routing system that builds an initial plan, then **replans after disruptions** (road closure, vehicle failure, urgent delivery), explains what was kept / moved / broken, and proves its output with an independent validator.

Each phase has:

1. **Goal**: what exists when the phase is done.
2. **Prompt**: paste this into the agent.
3. **Message for me**: what *you* (the human) must do or verify before and after the phase (API keys, installs, decisions, manual checks).

---

## 0. How to use this document

**Run phases in order.** Each phase depends on the previous one. Start a **fresh agent session per phase** (or per two small phases). The repo is the shared memory: the agent reads `CLAUDE.md` and `docs/` at the start of every session, so it needs no chat history.

**The rule for every phase:** do not move on until `make check` is green and you have done the "Message for me" checklist.

### Phase map

| # | Phase | Output | Hackathon lane it matches |
|---|-------|--------|---------------------------|
| 1 | Foundation and project memory | Repo scaffold, Makefile, CI, `CLAUDE.md`, docs | All |
| 2 | Contract (frozen models + fixtures) | `contract/` | P1 |
| 3 | Test scaffolding | Acceptance tests (xfail), micro-scenario | P2 |
| 4 | Engine I: travel + simulator | `engine/travel.py`, `engine/simulate.py` | P1 |
| 5 | Engine II: solver | prescreen, objective, construct, improve, diagnose | P1 |
| 6 | Independent validator | `verify/` (I1–I12) | P2 |
| 7 | Data: generators, scenarios, importers | `data/` | P3 |
| 8 | Replan core | `replan/` + `insert_deliveries` on frozen state | P2 + P1 |
| 9 | Diff and reason ledger | `diff/` | P2 |
| 10 | Text interpretation | `nlp/` | P3 |
| 11 | API | `api/` (mock mode, gate, store) | P3 |
| 12 | Frontend I: shell + initial-plan views | Gantt, load line, stop table, unplaced, map, KPIs | P4 |
| 13 | Frontend II: disruptions + compare + verify | Console, confirm card, compare, diff, verify, limits | P4 + P3 |
| 14 | Hardening | Fuzzers, edge suite, performance, optimality gap | P1 + P2 |
| 15 | Packaging, demo, docs | `make demo`, README, e2e test, pitch | P3 + P4 |
| 16 | Final QA and submission | Clean-clone test, rehearsal | All |

### If you have more than one person or agent

Phases 4–6 can run in parallel after Phase 3, as can 7 and 10, and 12 can start from fixtures once Phase 2 is done. Respect the **single-writer rule**: each directory has one owner; cross-lane changes go in `docs/CONTRACT_CHANGES.md`.

### Cut-lines (★ = cut these first if time runs out)

- **Never cut:** the validator gate, the confirm gate with unknown-location rejection, a reason on every diff row, the side-by-side view, the Method & Limits page.
- **Cut first (★):** LLM extractor, OR-Tools benchmark, CSV import, animations, customer-message drafts, decision trace, diff export.

---

## 1. Master context (paste once as the first message of any new session, if the agent doesn't load `CLAUDE.md` automatically)

```text
You are a senior engineer building "ReRoute" in this repository. Before doing anything:
1. Read CLAUDE.md, docs/ASSUMPTIONS.md, docs/REQUIREMENTS.md, docs/TECH_STACK.md, docs/CONTRACT_CHANGES.md (if they exist).
2. Run `git log --oneline | head -20` and `make check` to learn the current state.
3. Work test-first: find the failing/xfail tests that belong to your task, make them pass, remove their xfail markers.
4. Keep functions pure and deterministic (seeded RNG, iteration budgets instead of wall-clock, ties broken by ID).
5. Never edit frozen contract files except to add optional fields, and log every such change in docs/CONTRACT_CHANGES.md.
6. When finished, run `make check` and report: what is done, assumptions you made, deviations from the plan, open questions, and anything the human must do.
```

---

## Phase 1 — Foundation and project memory

### Goal
An empty-but-runnable monorepo: Python (uv, FastAPI, pytest, ruff) + frontend placeholder, `make check` working, CI, and a `CLAUDE.md` that carries the whole brief for every future session.

### Prompt

```text
You are starting a new project called ReRoute from an empty repository.

PROJECT BRIEF
ReRoute builds an initial delivery plan for a fleet (one depot, multiple vehicles with capacity, deliveries with hard time windows and service times, a travel-time matrix in minutes). It then REPLANS after three kinds of disruption: road closure, vehicle failure, urgent new delivery. After a replan it shows a side-by-side comparison classifying every delivery as KEPT / MOVED / BROKEN, each with a reason. Disruptions can be entered via a structured form or as free text; free text is interpreted into a proposal that the dispatcher must CONFIRM before it has any effect. An independent validator gates every plan before it is shown. The solver must be explainable and deterministic. No live map tiles; no network calls at runtime except one optional, flagged LLM extractor.

DECISIONS (write these verbatim into docs/ASSUMPTIONS.md and never re-debate them)
D1 Time is integer minutes since midnight; the matrix is in minutes (round fractions up).
D2 A window constrains service START. Early arrival waits: start = max(arrival, open), depart = start + service time. Wait is always shown.
D3 Cargo model: every parcel is either on board or needs a pickup stop. Morning plan: all loaded at the depot. Urgent delivery: picked up at the depot, released at report time. Failed vehicle: its undelivered parcels are picked up at its last known stop (or the depot) after the failure plus a transfer time (config flag, default 10 min). Load is checked at the start and after every pickup ("never overloaded at any point").
D4 Closure raises one edge's time (+N min, new value, or x k; both directions unless stated) for departures in [max(start, now), end). Matrix entries are direct times; no automatic detours.
D5 Freeze: a stop is fixed if its service ended <= now, is in progress, or the vehicle is already driving to it. A failed vehicle keeps only stops finished by its failure time.
D6 Objective, lexicographic: fewest priority-weighted broken, then fewest moved/shifted, then least travel + wait. Urgent priority = 2.
D7 Classes: kept = same vehicle and ETA within +-5 min; moved = other vehicle or larger ETA/sequence change but still in window; broken = cannot be placed in its window. A new urgent delivery is classed moved (placed) or broken (not placed) and is always badged NEW.
D8 Text flow: interpret -> preview -> confirm. An unknown or ambiguous location/vehicle rejects the whole report; no fuzzy matching. Missing optional fields get visible, editable defaults.
D9 Windows are hard. For a broken delivery show the earliest feasible ETA as a negotiation hint; never silently serve it late.
D10 Deterministic: seeded RNG, iteration budgets instead of wall-clock, ties broken by ID.

INVARIANTS (write into docs/ASSUMPTIONS.md as a second table)
I1 Every delivery appears exactly once, placed or unplaced with a reason.
I2 Load <= capacity at the start and after every pickup.
I3 Service start is inside the window, and wait = max(0, open - arrival).
I4 Travel times equal the matrix plus the closure rule.
I5 Nothing on a failed vehicle after its failure time.
I6 Frozen stops are byte-identical.
I7 A pickup precedes its delivery on the same vehicle.
I8 Every moved or broken row has a cause.
I9 An unknown location is rejected and state is unchanged.
I10 Text disruptions cannot apply without confirm.
I11 Same input and seed give the same output.
I12 A no-op replan changes nothing.

STATED LIMITS: heuristic with no optimality guarantee (we measure the gap on small instances); one depot, one capacity dimension, no split parcels; closures modeled by departure time on a direct edge (no mid-edge rerouting, no automatic detours); vehicles in transit are committed to their next stop; windows are hard; target scale up to 200 deliveries and 15 vehicles in about 2-3 s.

TECH STACK
- Backend: Python 3.12, FastAPI, Pydantic v2, uv. Solver is custom pure Python (regret-2 insertion + ruin-and-recreate). Verification: pytest, Hypothesis, ruff. Optional extras group `bench` for OR-Tools (benchmarks only).
- Frontend: Vite, React, TypeScript (strict), Tailwind, shadcn/ui, TanStack Query, Zustand, hand-rolled SVG + d3-scale, openapi-typescript, Playwright. Local fonts only, no CDNs, no tile maps.
- Packaging: `make dev`, `make check`, `make demo`. FastAPI serves the built UI from frontend/dist.

TARGET FILE STRUCTURE (create every directory and an empty __init__.py / README.md stub; every source file will carry a header comment stating its lane and tech stack)
reroute/
  .github/workflows/ci.yml
  api/{routes/{__init__,disruptions,plan,proposals,scenarios,state,validate}.py, __init__,gate,main,mock,settings,store}.py + README.md
  contract/{fixtures/, __init__, models, signatures}.py + README.md
  data/{generators/{__init__,city,stress}.py, importers/{__init__,csv_import,json_import}.py, scenarios/, __init__.py, README.md}
  diff/{__init__,classify,sentences}.py + README.md
  docs/{pitch/{README.md,demo_script.md,limits_slide.md}, ASSUMPTIONS.md, CONTRACT_CHANGES.md, FILE_STRUCTURE.md, REQUIREMENTS.md, TECH_STACK.md}
  engine/{benchmarks/{__init__,bruteforce,ortools_bench}.py, __init__,construct,diagnose,improve,objective,prescreen,simulate,trace,travel}.py + README.md
  frontend/ (create in Phase 12; for now only a README.md placeholder)
  nlp/{__init__,interpreter,llm_extractor,resolver,rules,time_grammar}.py + README.md
  replan/{__init__,apply,freeze,ledger,repair,replan,snapshot}.py + README.md
  scripts/{cli.py, demo.sh, gen_types.sh, README.md}
  tests/{acceptance/, edge/, property/, unit/{api,diff,engine,nlp,replan,verify}/, conftest.py, README.md}
  verify/{__init__,invariants,report,validator}.py + README.md
  .editorconfig .env.example .gitignore CLAUDE.md Makefile README.md pyproject.toml

LANE OWNERSHIP (single writer per directory; include in CLAUDE.md)
P1 engine/ and contract/ | P2 replan/, verify/, diff/, tests/acceptance/ | P3 api/, nlp/, data/, scripts/, frontend/src/features/disruptions/ | P4 rest of frontend/, docs/pitch/.
Hard rule: verify/ must NEVER import engine/ (independent validator).

YOUR TASKS
1. Scaffold everything above. Source stubs must be importable (no syntax errors) and each must start with a header comment: lane, purpose, stack.
2. pyproject.toml: uv-managed, Python 3.12; dependencies fastapi, uvicorn, pydantic>=2, httpx; dev group pytest, hypothesis, ruff, pytest-cov; optional extras `bench` (ortools) and `llm` (anthropic). Configure ruff (line length 100) and pytest (testpaths=tests, strict xfail off, markers: acceptance, edge, property, slow).
3. Makefile targets: `setup` (uv sync, plus pnpm install if frontend/package.json exists), `dev` (API with reload, and the Vite dev server if present), `check` (ruff check, ruff format --check, pytest -q excluding `slow`, and if frontend exists: tsc --noEmit and the build), `test`, `fuzz` (slow property tests), `demo` (placeholder that prints "not built yet"), `types` (runs scripts/gen_types.sh), `clean`. `make check` must pass on the empty scaffold.
4. Add a test tests/unit/verify/test_independence.py that fails if any file in verify/ imports from engine (parse imports with ast).
5. CI: .github/workflows/ci.yml runs `make check` on every PR and on push to main (setup-python 3.12, uv, Node LTS + pnpm cached).
6. Write docs/ASSUMPTIONS.md (D1-D10 + I1-I12 + stated limits), docs/TECH_STACK.md (table: layer, pick, why, where it lives), docs/FILE_STRUCTURE.md (the annotated tree), docs/CONTRACT_CHANGES.md (empty log with a template entry), docs/REQUIREMENTS.md.
7. docs/REQUIREMENTS.md: I will supply the original problem statement at docs/SPEC.md (if the file does not exist, STOP and ask me for it). Split the spec into numbered requirements R1..R15, one table row each with columns: requirement | module(s) | acceptance test file | demo step. Do not invent requirements that are not in the spec.
8. Write CLAUDE.md (the first file every future session reads). It must contain: the brief, R1-R15 (link to REQUIREMENTS.md), D1-D10 summary, invariants I1-I12 summary, architecture diagram (text), lane ownership, commands (make setup/dev/check/test/fuzz/demo), definition of done (make check green + tests for your requirement IDs + no edits outside your lane + header comments), and DON'TS: no map libraries, no network calls except the flagged LLM extractor, no CDNs, no wall-clock-dependent logic, no edits outside your lane, no silent contract changes, never import engine from verify.
9. .env.example with: REROUTE_MOCK_MODE=false, REROUTE_TRANSFER_MINUTES=10, REROUTE_LLM_ENABLED=false, ANTHROPIC_API_KEY= (empty), REROUTE_LLM_MODEL=, REROUTE_LLM_TIMEOUT_S=3.
10. README.md: overview + quick start (will be expanded in Phase 15).

Initialize git if needed and make logical commits. Finish with `make check` green and a report.
```

### Message for me

**Before the phase**
- [ ] Install: **Python 3.12**, **uv**, **Node LTS**, **pnpm**, **git**, **make**. Check with `python3.12 --version`, `uv --version`, `node -v`, `pnpm -v`.
- [ ] Create an **empty private GitHub repo** (or skip GitHub and use local git only), clone it, and `cd` into it before starting the agent.
- [ ] **Save the original problem statement as `docs/SPEC.md`** in the repo. The agent derives R1–R15 from it, and I haven't seen it; the two files you uploaded only describe the plan and structure. Without the spec, requirements will be guessed.
- [ ] If the event rules forbid pre-written code, check that scaffolding before the event is allowed.

**After the phase**
- [ ] Run `make check`; it must pass.
- [ ] Open `docs/REQUIREMENTS.md` and **read R1–R15 against your spec**. Fix any misinterpretation now; every later phase depends on it.
- [ ] If the organizers answered any of these, update `docs/ASSUMPTIONS.md`: dataset/field names, hard vs soft windows, failed-vehicle parcel transfer rules, depot return/shift end.
- [ ] Skim `CLAUDE.md`; it's the agent's only memory, so make sure it's accurate.
- [ ] Commit and push. **No API keys needed yet.**

---

## Phase 2 — Contract (frozen models and fixtures)

### Goal
`contract/` holds the single source of truth: Pydantic v2 models, function signatures with stubs, and hand-verified golden fixtures, so every later module codes against the same shapes.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md, docs/REQUIREMENTS.md, docs/SPEC.md. You are building the contract/ package. This is the ONE shared directory; after the freeze it is additive-only.

TASKS
1. contract/models.py (Pydantic v2, strict types, frozen where sensible, all times are int minutes per D1). If docs/SPEC.md prescribes field names for inputs, USE THEM and note the mapping in the model docstrings. Define at least:
   - Location (id, name, aliases: list[str], optional x, y)
   - Vehicle (id, name, aliases, capacity, optional shift_end, start location = depot)
   - Delivery (id, location_id, demand, window_open, window_close, service_time, priority default 1, optional release_time)
   - Scenario (name, depot_id, locations, vehicles, deliveries, time matrix as list[list[int]] indexed by location order, now/start time, config: transfer_minutes, seed)
   - Stop (kind: depot_start | pickup | delivery | depot_end, delivery_id or parcel ids, location_id, arrival, wait, service_start, depart, load_after, window_open/close where relevant, frozen: bool, badges such as NEW)
   - Route (vehicle_id, stops, total_travel, total_wait, failed_at optional)
   - Plan (version id, scenario ref, routes, unplaced: list[Unplaced], created_from, seed)
   - Unplaced (delivery_id, reasons: list[Reason], earliest_feasible_eta optional)  — Reason has a code (oversize, window_unreachable, no_capacity_at_stop, pushes_stop_late, no_vehicle_available, no_feasible_slot, ...), vehicle_id optional, detail text
   - Disruption: discriminated union RoadClosure (edge a,b; mode add_minutes|set_minutes|multiply; value; both_directions; start; end), VehicleFailure (vehicle_id, at_time, transfer_minutes optional), UrgentDelivery (a Delivery + report_time, priority default 2)
   - Proposal (id, source: form|text, original_text optional, disruption candidate, spans: list[SourceSpan(field, start, end)], assumptions: list[str], warnings: list[str], rejections: list[str], status: pending|confirmed|discarded, impact_preview optional)
   - ReplanResult (new plan, previous plan ref, diff, validation report, ledger entries, trace optional)
   - DiffRow (delivery_id, classification kept|moved|broken, cause_code, sentence, before/after vehicle + eta, badge NEW optional, earliest_feasible_eta optional) and Diff (rows + counts)
   - LedgerEntry (delivery_id, action eject|insert|move|complete, cause_code from: completed, vehicle_failed, closure_delay, displaced_by_urgent, knock_on, no_feasible_slot; detail)
   - ValidationReport (checks: list[InvariantResult(id I1..I12, passed, details)], passed bool)
   - KPI summary model (kept/moved/broken counts, travel, wait)
2. contract/signatures.py: stub function signatures with docstrings and `raise NotImplementedError`, so lanes can import from minute one:
   engine: simulate_route, build_plan, insert_deliveries, improve, diagnose_unplaced
   replan: snapshot, replan
   verify: validate
   diff: classify
   nlp: interpret
   Include exact parameter and return types using the models.
3. contract/__init__.py re-exports everything. Make the real packages (engine/, replan/, verify/, diff/, nlp/) import and re-export these stub signatures so `from engine import simulate_route` works today.
4. Fixtures in contract/fixtures/ (valid JSON that round-trips through the models):
   - scenario_micro.json: HAND-CHECKABLE micro-scenario — 3 vehicles, 8 deliveries, a small matrix (<= 6 distinct locations) — designed so a human can verify arrivals with a pencil. Include one early arrival (a wait), one tight window, one capacity-binding vehicle.
   - plan_micro.json: the expected plan for it with arrivals, waits, load_after computed by hand and explained in a sibling file contract/fixtures/MICRO_WALKTHROUGH.md (step-by-step arithmetic per stop).
   - replan_result_closure.json, proposal_failure.json (text-derived, with spans and an amber assumption), validation_report_ok.json.
5. Add tests/unit/contract/test_models_roundtrip.py: every fixture loads, validates, re-serializes identically; models reject bad input (negative demand, window_close < window_open, unknown disruption type).
6. Write contract/README.md: all models in a table, versioning rule (additive-only optional fields after tag contract-v1), how to regenerate OpenAPI.
7. Ensure `make check` is green. Tag nothing yet — I will review and tag contract-v1.

Do NOT implement algorithms. Report any ambiguity in the spec that affected the models.
```

### Message for me

**Before the phase**
- [ ] If the organizers gave a **sample dataset or file format**, drop it in `docs/samples/` so the agent adopts those field names.

**After the phase** (this is the most important review in the project)
- [ ] **Review `contract/models.py` line by line** against `docs/SPEC.md`. Anything missing here becomes expensive later.
- [ ] **Verify `MICRO_WALKTHROUGH.md` by hand**: recompute 2–3 arrivals with a pencil from the matrix. This is the ground truth for the whole project; if it's wrong, every test is wrong.
- [ ] Check that field names match the organizers' dataset (if any).
- [ ] `git tag contract-v1` once satisfied. From now on, contract changes are additive only and go in `docs/CONTRACT_CHANGES.md`.
- [ ] **No API keys needed.**

---

## Phase 3 — Test scaffolding (the scoreboard)

### Goal
About 40 acceptance tests, all `xfail` on day one, derived from R1–R15. The green count is the project scoreboard. Hand-checkable micro-scenario tests exist and define "correct".

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md, docs/REQUIREMENTS.md, contract/ and its fixtures. You own tests/ for this phase.

TASKS
1. Write about 40 acceptance tests under tests/acceptance/ (one file per theme from the plan): test_initial_plan.py, test_micro_scenario.py, test_road_closure.py, test_vehicle_failure.py, test_urgent_delivery.py, test_text_interpretation.py, test_confirm_gate.py, test_diff_reasons.py. Each test:
   - has a docstring naming the requirement ID(s) (R#) and invariant(s) (I#) it proves,
   - calls ONLY the public signatures from contract/signatures.py or API endpoints via FastAPI TestClient,
   - is marked @pytest.mark.acceptance and @pytest.mark.xfail(reason="not implemented: <phase>", strict=False) for now.
   Cover at least: arrivals+waits shown; load never exceeds capacity at start and after each pickup; unplaceable delivery gets a reason; each of the 3 disruptions end-to-end; nothing scheduled after vehicle failure time; frozen stops identical (I6); every moved/broken row has a cause (I8); urgent delivery gets NEW badge and depot pickup with release time; text -> interpret -> preview -> confirm; confirm gate returns 409 without confirm and 422 on an unknown place (I9, I10); no-op replan = all kept (I12); determinism across two runs (I11).
2. tests/acceptance/test_micro_scenario.py: assert the exact expected arrivals/waits/loads from contract/fixtures/plan_micro.json for the micro-scenario under the specified solver output where the plan is unique, and otherwise assert the hand-computed values via the simulator for a FIXED sequence of stops (simulate_route on a given route must reproduce every number).
3. tests/conftest.py: fixtures for scenario_micro, plan_micro, a TestClient factory, helper `load_fixture(name)`, helper `mutate(plan)` utilities to craft deliberately broken plans (overloaded route, window violation, stop after failure, duplicate delivery, missing delivery, pickup after delivery). These will be used by validator tests in Phase 6.
4. Add tests/README.md: how to run acceptance tests, how to read the scoreboard, and a script scripts/scoreboard.py (or `make score`) that runs pytest -m acceptance and prints "N / total passing, M xfail".
5. Make sure `make check` is green (xfail does not fail the build).

Constraints: do not implement any production logic. Do not weaken a test to make it easier — if a requirement is ambiguous, write the stricter reading and note it in docs/ASSUMPTIONS.md under "Open questions".
```

### Message for me

**After the phase**
- [ ] Run `make score` (or the scoreboard script) and note the starting number (e.g. `0 / 40`).
- [ ] Skim the acceptance test names and check that **each of R1–R15 appears at least once**.
- [ ] Read the micro-scenario test and confirm it matches your hand-computed numbers.
- [ ] If the spec has examples (sample disruptions or sample report texts), tell the agent to add them as extra tests later; paste them into `docs/samples/`.
- [ ] **No API keys needed.**

---

## Phase 4 — Engine I: travel function and simulator

### Goal
`simulate_route` is the single source of truth for arrival, wait, start, depart, load-after and violations, with closures modeled as a time-dependent travel function.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md, contract/, and tests/unit/engine + tests/acceptance/test_micro_scenario.py. You own engine/ (lane P1). Implement engine/travel.py and engine/simulate.py. This is a SMALL, CRITICAL module: everyone depends on it, so correctness and clarity beat cleverness.

STATE YOUR APPROACH FIRST in a short comment block at the top of simulate.py (inputs, outputs, how closures and pickups are handled), then implement.

engine/travel.py
- travel_time(scenario_matrix, closures, a, b, depart_time) -> int minutes, using the direct matrix entry (D1) and applying every active closure on edge (a,b) (or (b,a) if both_directions) whose active interval [max(start, now), end) contains depart_time (D4). Modes: add_minutes, set_minutes, multiply (round up). Overlapping closures: define and document a deterministic composition rule (e.g. apply set_minutes first, then multiply, then add; ties by closure id) and test it.
- Pure, no globals, no I/O.

engine/simulate.py
- simulate_route(scenario, vehicle, ordered_stops, start_location, start_time, start_load, closures, release_times) -> Route result with per-stop: arrival, wait, service_start, depart, load_after, and a list of violations (window miss, over capacity at start or after a pickup, shift_end exceeded, pickup after its delivery, release time not met).
- D2: start = max(arrival, window_open); wait = max(0, open - arrival); depart = start + service_time. A stop whose service_start > window_close is a violation with the lateness.
- D3: load is checked at the start of the route and after EVERY pickup. Deliveries reduce load. Morning plan: the route starts with everything loaded at the depot. Pickup stops add demand at service end.
- Release times: a pickup cannot start before its release time (wait is shown).
- Return-to-depot: configurable per scenario (return_to_depot flag, default per ASSUMPTIONS.md); if enabled, add a depot_end stop and check shift_end.
- Frozen prefix support: simulate_route must accept an already-fixed prefix (list of stops with fixed times) and continue from the vehicle's ready location/time/load. Frozen stops are returned unchanged (byte-identical).
- Return a structured result usable by the validator-independent code paths (but note: verify/ will NOT import this).
- Pure and deterministic.

TESTS (tests/unit/engine/test_engine_simulate.py, tests/unit/engine/test_engine_travel.py)
- Reproduce every number in contract/fixtures/MICRO_WALKTHROUGH.md exactly.
- Early arrival -> wait; exact-boundary arrival (arrival == window_close is OK, +1 is a violation); zero-service stop; overload at start; overload after a pickup but not at start; closure with each mode; closure that begins after departure (no effect); closure with departure exactly at the end (no effect); overlapping closures; frozen-prefix pass-through.
- Property test (Hypothesis, light): simulation is monotone in time (arrival times never decrease along a route) and deterministic.

Remove xfail from tests this unblocks. Run `make check`. Report what you changed and any assumption.
```

### Message for me

**After the phase**
- [ ] Open the `simulate.py` header comment and **check the approach** (2 minutes). Especially the closure-composition rule and the D3 load check.
- [ ] Run the micro-scenario test and confirm it passes against **your** pencil numbers.
- [ ] Confirm the **return-to-depot / shift end** decision matches what the organizers said (or your default).
- [ ] **No API keys needed.**

---

## Phase 5 — Engine II: solver (prescreen, construct, improve, diagnose)

### Goal
`build_plan` produces a good, deterministic initial plan; every unplaced delivery has a reason; `insert_deliveries` is reusable for replanning.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md, contract/, engine/simulate.py, engine/travel.py and tests/unit/engine, tests/acceptance/test_initial_plan.py. You own engine/ (lane P1).

STATE YOUR APPROACH FIRST (as a comment block at the top of construct.py): the algorithm in numbered steps, the data structures for the insertion cache, and how determinism is guaranteed. Then implement.

MODULES
1. engine/prescreen.py — reject impossible deliveries up front with a reason: demand > max vehicle capacity (oversize); window unreachable even as the first stop (depot -> location arrival > window_close); unknown location. Return (feasible, rejected-with-reasons).
2. engine/objective.py — lexicographic objective per D6: (priority-weighted broken count, moved/shifted count, travel + wait). Provide `score(plan, baseline_plan=None, stability_weight=0)` returning a comparable tuple. Stability weight is used by replans (Phase 8) to prefer keeping stops where they were. Ties broken by ID.
3. engine/construct.py —
   - build_plan(scenario, seed) -> Plan: parallel regret-2 insertion. Repeatedly insert the delivery whose best and second-best vehicle options differ most (regret), at its cheapest FEASIBLE position, where feasible = full forward simulate_route passes (load at start and after every pickup, all windows, shift end). Cache the best insertion per (delivery, vehicle) and only re-evaluate the vehicle whose route changed. Deterministic tie-breaking by IDs.
   - insert_deliveries(state, pool, objective) -> (state, unplaced): the SAME insertion routine, but operating on a "state" that includes frozen prefixes, per-vehicle ready location/time/on-board load, pending pickup stops (pickup must precede its delivery on the same vehicle, I7), and release times. Frozen stops are never moved. Design the state type now so Phase 8 can reuse it; put it in contract/ as an optional additive model if needed and log it in docs/CONTRACT_CHANGES.md.
4. engine/improve.py — ruin-and-recreate: remove a related cluster (10-25% of deliveries; relatedness by time/space), reinsert by regret, keep if the objective improves. Fixed iteration budget + seeded RNG (no wall-clock). Never touches frozen stops. Provide improve(state, iterations, seed).
5. engine/diagnose.py — diagnose_unplaced(state, delivery) -> list of Reason, one per vehicle with the binding constraint: oversize, window unreachable, no capacity at stop k, pushes stop X late, no vehicle available. ★ Also compute `earliest_feasible_eta` assuming the window were relaxed (the "what would it take" hint, D9).
6. ★ engine/trace.py — decision trace strings such as "cheapest feasible slot +6 min; runner-up V3 +11". Cut this first if time is short; keep a stub.

TESTS
- tests/unit/engine/test_engine_construct.py: micro-scenario produces the expected plan (or a plan with equal objective if not unique); every placed route passes simulate_route with zero violations; every delivery is placed or unplaced with a reason (I1); two runs with the same seed produce byte-identical JSON (I11); impossible deliveries are rejected with the correct reason code.
- Small-instance checks: tiny scenarios where you can enumerate the optimum by hand.
- Performance sanity: 100 deliveries / 10 vehicles under ~2 s on a laptop (mark @pytest.mark.slow; just record the timing for now).

Remove xfail from tests this unblocks (test_initial_plan, test_micro_scenario). Run `make check`. Report the approach, timing, and anything I should review.
```

### Message for me

**After the phase**
- [ ] **Approve the approach** in the header of `construct.py` (this is the "state the approach first" gate; takes 2 minutes). Check it matches: regret-2 insertion → ruin-and-recreate, deterministic, no OR-Tools in runtime.
- [ ] Look at the timing printed for 100/10 and note it.
- [ ] Sanity-check one plan by hand: pick one route from the micro-scenario and verify arrivals, waits and load against the matrix.
- [ ] Read two "unplaced" reason sentences. Would a dispatcher understand them?
- [ ] **No API keys needed.**

---

## Phase 6 — Independent validator

### Goal
A validator written from the spec, not from the solver, that checks I1–I5, I7 (and later I6, I8, I12) and is a hard gate before any plan is shown or committed.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md, docs/SPEC.md, contract/, tests/conftest.py (the `mutate` helpers). You own verify/ (lane P2). 

CRITICAL RULE: verify/ must NOT import engine/ or reuse its simulator, travel function or objective. Re-implement the arithmetic from the matrix and the rules in ASSUMPTIONS.md. Independence is the point: a bug shared by solver and checker would go unnoticed. tests/unit/verify/test_independence.py enforces this; keep it green.

TASKS
1. verify/invariants.py — one pure function per invariant, each returning an InvariantResult with passed + details (naming the offending delivery/vehicle/stop):
   I1 every delivery exactly once, placed or unplaced with a reason;
   I2 load <= capacity at the start and after every pickup;
   I3 service start inside the window, and wait == max(0, open - arrival);
   I4 travel times equal the matrix plus the closure rule (recompute independently);
   I5 nothing on a failed vehicle after its failure time;
   I6 frozen stops byte-identical vs the previous plan (needs previous plan; N/A for initial plans);
   I7 pickup precedes its delivery on the same vehicle;
   I8 every moved/broken diff row has a cause;
   I9 unknown location rejected, state unchanged (checked at proposal level);
   I10 text disruptions cannot apply without confirm (checked on the proposal/status);
   I11 determinism: same input + seed gives the same output (callable helper that takes two results);
   I12 a no-op replan changes nothing.
   Invariants that need context not available yet should return "not_applicable" cleanly, never crash.
2. verify/validator.py — validate(scenario, plan, previous_plan=None, disruption=None, diff=None, proposal=None) -> ValidationReport. Passing means every applicable check passes.
3. verify/report.py — human-readable summary lines per invariant for the Verify panel (e.g. "I2 Load never exceeds capacity: OK (checked 41 stops)").
4. tests/unit/verify/test_verify_validator.py — for EACH invariant, a deliberately broken plan (use `mutate` helpers) that the validator must flag, naming the right invariant; plus the fixture plan_micro that must pass; plus a randomized "perturb one stop" test that must always be caught.
5. Adversarial self-review: write a short section in verify/README.md listing the 5 sneakiest ways a plan could be wrong that you tried to catch (e.g. load check only at the start, wait computed from departure, time-dependent closure applied at arrival instead of departure).
6. Run the validator against engine.build_plan output on the micro-scenario in a TEST (tests may import both; verify/ itself may not). It should pass.

Remove xfail where unblocked. Run `make check`. Report.
```

### Message for me

**After the phase**
- [ ] Run the independence test and confirm it passes. This is the strongest credibility claim you'll make to judges.
- [ ] Read the "sneakiest bugs" list in `verify/README.md` and add any case you can think of.
- [ ] Ask the agent (new session) to **attack** the solver: "Construct an input that breaks I2 / I5 / I6." This adversarial cross-review is in the plan; do it for at least one invariant now.
- [ ] **No API keys needed.**

---

## Phase 7 — Data: generators, named scenarios, importers

### Goal
A realistic "city" scenario generator (real place names, a shared bridge edge, tight windows, two impossible deliveries), a 7-scenario pack, a stress generator and JSON/CSV importers.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md, docs/SPEC.md, contract/. You own data/ (lane P3).

TASKS
1. data/generators/city.py — generate_city(seed, n_deliveries, n_vehicles) -> Scenario:
   - Uses REAL, recognizable place names (use a single real city of your choice; I will set it below if I specify one), because the text-input demo depends on typing real names. Each location gets 1-3 aliases (e.g. "Central Station", "central stn").
   - Matrix in integer minutes derived from synthetic x/y coordinates (Euclidean * speed factor, rounded UP per D1), symmetric, triangle-inequality respected approximately.
   - ONE bridge edge that many routes naturally cross (so a closure there is dramatic).
   - A few tight windows, mixed service times and demands, two deliberately impossible deliveries (one oversize, one unreachable window).
   - Fully deterministic from the seed.
2. data/generators/stress.py — generate_stress(seed, n_deliveries=100, n_vehicles=10) with the ability to scale to 200 / 15.
3. data/scenarios/*.json — generate (via a script, not by hand) the pack of 7 named scenarios: baseline, closure, failure, urgent, cascade, stress (100/10), impossible. For the disruption scenarios, include a ready-made Disruption object next to each (closure on the bridge; failure of the busiest vehicle mid-route; urgent delivery near the depot that fits only if something else shifts; cascade = two disruptions in sequence). Add scripts/gen_scenarios.py and a `make scenarios` target; document that JSON files are generated, not edited by hand.
4. data/importers/json_import.py — import a scenario JSON with FIELD-ALIAS adapters (adopt the organizers' field names if docs/samples/ has them). Validate through the contract models and return clear errors. 
5. ★ data/importers/csv_import.py — CSV import with alias adapters. Cut first if time is short.
6. tests: generators are deterministic (same seed -> identical JSON); every scenario validates against the models; engine.build_plan works on baseline and produces >= 1 unplaced with a reason on `impossible`; importer round-trip.
7. Update data/README.md with the scenario catalogue (what each scenario demonstrates and which demo step uses it).

Do not change the contract. Run `make check`. Report.
```

### Message for me

**Before the phase**
- [ ] **Pick the city** whose place names should be used (e.g. your own city, or the city in the problem statement). Tell the agent: "Use <city> place names." Use names a judge would recognize and be able to type.

**After the phase**
- [ ] Open `baseline.json` and check that place names and aliases look right and are easy to type live.
- [ ] Confirm each scenario in the pack is something you'd want on stage.
- [ ] If the organizers gave a real dataset, **import it now** with the importer and confirm it plans correctly.
- [ ] **No API keys needed.**

---

## Phase 8 — Replan core (snapshot, freeze, apply, repair, ledger, replan)

### Goal
`replan()` handles all three disruptions starting from the **current state**, changing as little as possible, recording a cause for every change, and passing the validator gate.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md (D3-D7, D9), docs/SPEC.md, contract/, engine/ (construct.insert_deliveries, improve, diagnose, objective), verify/, and the acceptance tests for closure, failure, urgent. You own replan/ (lane P2). You may CALL engine functions but not edit them; if you need a change in engine/, write it in docs/CONTRACT_CHANGES.md and ask me.

STATE YOUR APPROACH FIRST (comment block at the top of replan/replan.py): the pipeline in numbered steps, then implement.

PIPELINE (per the plan)
snapshot(now) -> freeze -> apply disruption -> repair/eject -> reinsert -> improve -> validate gate -> diff.

MODULES
1. replan/snapshot.py — snapshot(plan, now) -> per-vehicle state: frozen prefix, ready location, ready time, on-board load, breakdown site if failed.
2. replan/freeze.py — D5 rule helpers. A stop is frozen if service ended <= now, is in progress, or the vehicle is already driving to it ("in transit is committed to its next stop"). A failed vehicle keeps only stops finished by its failure time. Frozen stops must be byte-identical afterwards (I6).
3. replan/apply.py — apply a disruption to the state:
   - RoadClosure: add the closure to the time-dependent travel function (D4); matrix unchanged.
   - VehicleFailure: mark vehicle unavailable from the failure time; orphan its undelivered parcels; create rescue pickup stops at its last known stop (or the depot) at failure_time + transfer_minutes (config flag, D3); the parcels must be picked up by another vehicle BEFORE delivery (I7), respecting capacity after every pickup (I2).
   - UrgentDelivery: new delivery priority 2, pickup at the depot with release time = report time, badge NEW (D7).
4. replan/repair.py — re-simulate every FREE suffix with windows softened, fix locally (shift within slack, reorder adjacent), then eject any stop that still violates a hard constraint, writing a ledger entry with its cause.
5. replan/ledger.py — reason ledger. Cause codes: completed, vehicle_failed, closure_delay, displaced_by_urgent, knock_on, no_feasible_slot. Every eject, insert, move is recorded with delivery id and detail text.
6. replan/replan.py — replan(scenario, current_plan, disruption, now, seed) -> ReplanResult:
   - Reinsert the ejected/orphaned/new pool via engine.insert_deliveries with the stability-weighted objective (prefer keeping existing stops), then a short ruin-and-recreate on FREE suffixes only.
   - Urgent: insert; displace lower-priority deliveries only if necessary, recording displaced_by_urgent.
   - For any delivery that cannot be placed: unplaced with diagnose_unplaced reasons + earliest feasible ETA (D9). Never serve late.
   - GATE: run verify.validate on the new plan; if it fails, DISCARD the result and raise a typed ReplanValidationError carrying the report. A bad plan must never be returned.
   - Replan-of-replan must work (the result plan can be the input to the next replan).
   - A no-op replan (e.g. closure on an unused edge, or empty disruption) returns all kept, with identical plan (I12).
7. Edge handling: failure at t=0, exactly at a stop's end, on an idle vehicle; closure on an unused edge; overlapping closures; failure of a vehicle with no remaining stops; unplaceable urgent delivery.

TESTS
- tests/unit/replan/test_replan_snapshot.py (freeze rule, in-progress, in-transit).
- Remove xfail from tests/acceptance/test_road_closure.py, test_vehicle_failure.py, test_urgent_delivery.py as they pass.
- Validator must be green after every replan in these tests.

Run `make check`. Report approach, what passes, and any deviation.
```

### Message for me

**Before the phase**
- [ ] Decide / confirm **what happens to cargo on a failed vehicle** (D3). Default: parcels are collected at the vehicle's last known stop (or depot) after failure + 10 min transfer. If the organizers said otherwise, update `docs/ASSUMPTIONS.md` and `.env.example` first.

**After the phase**
- [ ] **Approve the approach** header in `replan.py` (2 minutes).
- [ ] Run `make score`; expect most closure/failure/urgent acceptance tests to pass.
- [ ] Hand-check one failure replan: confirm completed stops are unchanged and nothing is scheduled on the failed vehicle after the failure time.
- [ ] Ask a fresh agent session to **attack replan** ("construct a disruption that breaks I5 or I6"). Fix anything found.
- [ ] **No API keys needed.**

---

## Phase 9 — Diff and reason sentences

### Goal
Classify every delivery as kept / moved / broken with a cause, and produce one plain-English sentence per row.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md (D7, D9), contract/ (DiffRow, Diff, LedgerEntry), replan/ledger.py and tests/acceptance/test_diff_reasons.py. You own diff/ (lane P2).

TASKS
1. diff/classify.py — classify(old_plan, new_plan, ledger, disruption) -> Diff, reading the ledger:
   - kept: same vehicle AND ETA within +-5 min (make 5 a named constant, tested at 5 and 6),
   - moved: other vehicle OR larger ETA/sequence change, still in window,
   - broken: unplaced (cannot be placed in its window); include the earliest feasible ETA as a negotiation hint (D9),
   - a new urgent delivery: moved if placed, broken if not, always with badge NEW (D7),
   - completed deliveries (service ended <= now): kept, cause `completed`.
   Every moved/broken row MUST carry a cause_code from the ledger; if none exists, raise (do not invent one) so I8 failures are visible.
   Also compute counts for the KPI bar and travel/wait deltas.
2. diff/sentences.py — one human sentence per row from its cause code. Examples of tone: "Moved from V2 to V3 (+12 min): vehicle V2 failed at 10:30." / "Broken: the 11:00-12:00 window can't be met after the bridge closure; earliest possible is 12:20." Deterministic templates, no LLM. Every cause code must have a template; test completeness over the enum.
3. Tests: tests/unit/diff/test_diff_classify.py — thresholds (+-5), vehicle change, sequence change, NEW badge, completed, broken with hint; every cause code has a sentence; I8 holds across all three disruption scenarios from data/scenarios.
4. Wire diff into replan() if not already (ReplanResult.diff) and make tests/acceptance/test_diff_reasons.py pass.

Run `make check`. Report.
```

### Message for me

**After the phase**
- [ ] **Read 10 generated sentences** from the three disruption scenarios. Judges will read these on stage, so they should be clear, accurate and not robotic.
- [ ] Confirm the **±5 minute** kept threshold matches your spec (D7).
- [ ] Run `make score`; acceptance tests for diff reasons should be green.
- [ ] **No API keys needed.**

---

## Phase 10 — Text interpretation (rule-based; LLM optional)

### Goal
A deterministic, offline interpreter that turns a free-text report into a **Proposal** with highlighted spans, assumptions, warnings and rejections. Unknown or ambiguous places reject the whole report.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md (D8), docs/SPEC.md, contract/ (Proposal, SourceSpan, disruptions), data/scenarios, tests/acceptance/test_text_interpretation.py. You own nlp/ (lane P3).

PRINCIPLES
- Primary path is OFFLINE and DETERMINISTIC (rules + exact-match resolver). No network.
- No fuzzy matching. Unknown or ambiguous location/vehicle -> reject the WHOLE report, state unchanged (I9).
- Missing optional fields get VISIBLE, EDITABLE defaults, listed as assumptions.

MODULES
1. nlp/time_grammar.py — parse to minutes since midnight: "10:30", "10.30", "3pm", "3:15 pm", "15:00", "until 14:00", "for 2 hours", "for 45 min", "in 30 min" (relative to `now`), "from 9 to 11". Return value + span. Ambiguity (e.g. a bare "3" ) -> warning or rejection, never a silent guess.
2. nlp/resolver.py — exact-match resolver for locations and vehicles: normalize case, spaces and punctuation; support declared aliases; exact match only after normalization; ambiguous (a partial name matching two places) -> reject with the candidates listed; unknown -> reject.
3. nlp/rules.py — rule-based extraction for road_closure, vehicle_failure, urgent_delivery: find the event type from keywords, pull locations/vehicles (resolved via resolver), times, durations, demand, and window for urgent deliveries. Closure effect words: "closed", "blocked", "delay of 20 min", "takes twice as long".
4. nlp/interpreter.py — interpret(text, scenario, now) -> Proposal with spans (character offsets for each extracted field), assumptions (e.g. "No end time given: assumed closure lasts until end of day" / "Assumed 10-minute transfer"), warnings, rejections. Two events in one report -> reject with a clear message asking to submit them separately. Contradictory info -> reject. Missing required info (e.g. no vehicle named) -> reject, with what is missing.
5. ★ nlp/llm_extractor.py — OPTIONAL and OFF by default, enabled by REROUTE_LLM_ENABLED=true plus ANTHROPIC_API_KEY. It calls the Anthropic API to extract mentions as JSON. GUARDRAILS: (a) the model never sees the list of valid locations; (b) every extracted mention must appear VERBATIM in the original text; (c) mentions are resolved by the exact-match resolver, never by the model; (d) hard timeout (REROUTE_LLM_TIMEOUT_S) and any error/timeout/invalid JSON falls back to the rule-based path silently with a warning; (e) the anthropic package is imported lazily, so the code works without it installed. Use the model name from REROUTE_LLM_MODEL (no hardcoded model string without an env override). Cut this first if time is short.
6. TESTS (tests/unit/nlp/): time grammar table; resolver (case, spaces, punctuation, alias, ambiguity, unknown); test_nlp_hostile_phrasings.py with at least 30 phrasings including hostile ones: unknown place, a partial name matching two places, missing time, contradictory info, two events in one report, typos, ALL CAPS, extra punctuation, a place name inside an unrelated sentence, empty string, very long input. For the LLM extractor: unit tests with a mocked client (hallucinated mention not in text -> dropped; timeout -> fallback).

Run `make check`. Report the hostile-phrasing table (input -> outcome).
```

### Message for me

**Before the phase**
- [ ] **Decide whether to use the optional LLM extractor.** It's a ★ item and can be skipped. If yes, get an **Anthropic API key** from the Anthropic Console and put it in your local `.env` (copy `.env.example`):
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  REROUTE_LLM_ENABLED=true
  REROUTE_LLM_MODEL=<model name you want to use>
  ```
  **Never commit `.env`.** Confirm `.gitignore` includes it.

**After the phase**
- [ ] Review the **hostile-phrasing table**. Add 5 phrasings of your own that a judge might type and ask the agent to cover them.
- [ ] Type 5 realistic reports using real place names from your city scenario and check the interpretations.
- [ ] If using the LLM: run once with the key set and confirm that (a) it works, (b) with the key removed it falls back cleanly. Check that a hallucinated place is rejected.
- [ ] Remember: with the LLM flag **off**, the system must work fully offline.

---

## Phase 11 — API (mock mode, confirm gate, version store)

### Goal
FastAPI exposes every endpoint, in **mock mode** (serving fixtures, so the UI never waits) and real mode, with a server-enforced confirm gate and a plan-version store with undo.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md (D8, I9, I10), contract/, nlp/, replan/, verify/, diff/, data/, tests/acceptance/test_confirm_gate.py, tests/acceptance/test_text_interpretation.py. You own api/ and scripts/ (lane P3).

ENDPOINTS
- GET /scenarios, GET /scenarios/{name}
- POST /plan/initial          (scenario name or inline scenario -> Plan + validation report; unplaced with reasons)
- GET /state                  (current plan version, vehicle states at `now`)
- POST /validate              (run the independent validator on a given or current plan)
- POST /disruptions/preview   (structured disruption -> Proposal with impact preview; no state change)
- POST /disruptions/interpret (text -> Proposal via nlp.interpret; no state change)
- POST /proposals/{id}/confirm  (applies via replan(); returns ReplanResult)
- POST /proposals/{id}/discard
- Plus undo/version endpoints: GET /versions, POST /versions/{id}/restore.

RULES
1. api/gate.py — the confirm gate is enforced SERVER-SIDE: applying anything without a confirmed proposal returns 409; a proposal with rejections or an unknown place returns 422 and state is unchanged (I9, I10). Text-originated proposals can never be applied without confirm. Editing fields on the confirm card = re-submitting a modified proposal for a new preview, then confirm.
2. api/store.py — session + plan-version store: every committed plan is a version; undo restores the previous one; replan-of-replan works; thread-safe enough for a single-user demo; no database.
3. api/mock.py + api/settings.py — mock mode (REROUTE_MOCK_MODE=true) serves golden fixtures from contract/fixtures for every endpoint with the real response models. Settings from env: mock mode, LLM flag, transfer minutes, scenario dir.
4. api/main.py — app factory, routers, CORS for the Vite dev server, static mount of frontend/dist (if it exists) with SPA fallback. All responses use contract models so OpenAPI is exact.
5. Gate on output: every plan returned has passed verify.validate; if replan raises ReplanValidationError, return 500-class error JSON with the report and leave state unchanged.
6. scripts/gen_types.sh — dump OpenAPI to frontend/openapi.json and run openapi-typescript to frontend/src/api/schema.d.ts (skip gracefully if frontend isn't there yet). `make types`.
7. scripts/cli.py — `reroute plan|replan|validate` working on JSON files; exit codes meaningful. Register as a console script in pyproject.toml.
8. Tests: tests/unit/api/test_api_endpoints.py (mock mode and real mode on the micro-scenario); remove xfail from test_confirm_gate.py and test_text_interpretation.py; end-to-end: interpret -> preview -> confirm -> diff -> validator green; unknown place -> 422 with state unchanged; confirm without proposal -> 409.

Run `make check` and also start the server (`make dev`) and hit every endpoint once with curl; paste the results in your report.
```

### Message for me

**After the phase**
- [ ] Run `make dev`, open **http://localhost:8000/docs** and try each endpoint in the Swagger UI.
- [ ] Try the gate manually: send a text with an unknown place → expect **422**; try to confirm a non-existent proposal → expect **409**.
- [ ] Run the CLI once: `uv run reroute plan data/scenarios/baseline.json`.
- [ ] Check `REROUTE_MOCK_MODE=true make dev` returns fixtures (this lets frontend work proceed even if the engine breaks).
- [ ] Run `make score`. You should be near the "70% of acceptance tests" gate.
- [ ] **No new keys needed**, but if you enabled the LLM, re-check that `.env` is git-ignored (`git status` must not list it).

---

## Phase 12 — Frontend I: shell and initial-plan views

### Goal
A polished React app that loads a scenario and shows the initial plan: per-vehicle Gantt with hatched waits, load-vs-capacity line, stop table, unplaced panel with reasons, schematic map, KPI bar.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md, contract/ (models and fixtures), docs/SPEC.md, and the generated api/openapi. You own frontend/ except src/features/disruptions/ (lane P4).

DESIGN FIRST: before coding, write docs/pitch/DESIGN.md (one page): palette, typography, spacing, layout sketch in ASCII. Design tokens are in frontend/src/styles/tokens.css and the Tailwind config. RULE: green / amber / red are RESERVED for kept / moved / broken ONLY — never use them decoratively. Local fonts only (frontend/public/fonts); NO CDNs; NO map or tile libraries.

SCAFFOLD
- Vite + React + TypeScript (strict, @/ alias) + Tailwind + shadcn/ui (config in components.json; generated components under src/components/ui) + TanStack Query + Zustand + d3-scale + openapi-typescript + Playwright.
- src/api/client.ts (typed fetch client from schema.d.ts, generated by `make types`; never hand-edit schema.d.ts), src/api/hooks.ts (scenarios, initial plan, state, validate).
- src/store/sessionStore.ts (selected version, 'now' scrubber, filters, hover cross-highlight id).
- src/lib/format.ts (minutes -> HH:MM, D1), src/lib/timeScale.ts (shared time axis helpers), src/lib/cn.ts.
- App shell: header (scenario picker, mock/real indicator), main area, side panels.

FEATURES (hand-rolled SVG + d3-scale)
1. features/gantt/GanttChart.tsx — one row per vehicle: travel segments, HATCHED wait segments, service blocks, window brackets on each delivery, a vertical 'now' line, hover tooltips with arrival / wait / start / depart / load.
2. features/gantt/LoadProfile.tsx — step line of on-board load vs a capacity line under each route; if load ever exceeded capacity it would be visibly wrong (it never should).
3. features/gantt/StopTable.tsx — arrival, wait, start, depart, load per stop; sortable; hover cross-highlights Gantt.
4. features/gantt/UnplacedPanel.tsx — unplaced deliveries with reasons per vehicle, plus the earliest-feasible-ETA hint.
5. features/kpis/KpiBar.tsx — kept / moved / broken counts (empty state for initial plan), total travel, total wait.
6. features/map/mds.ts + SchematicMap.tsx — schematic SVG: x/y if supplied, else classical MDS from the time matrix; routes as colored polylines per vehicle (use neutral vehicle colors, not green/amber/red); depot marked; unknown stays offline.
7. Empty / loading / error states everywhere. Responsive down to a 1280px laptop; keyboard focus visible; sufficient contrast.

Develop against MOCK MODE first (REROUTE_MOCK_MODE=true) and switch to the live API once the layout is solid. Update `make check` to include tsc --noEmit and `pnpm build`. Add `make dev` to run API + Vite together.

Report with screenshots (use Playwright to capture the initial-plan view for baseline and impossible scenarios and save in docs/pitch/screenshots/).
```

### Message for me

**Before the phase**
- [ ] **Download fonts** you want (e.g. Inter or any open-license font) as `.woff2` into `frontend/public/fonts/`, or tell the agent to use a system font stack. Do **not** use Google Fonts links; venue Wi-Fi is unreliable.
- [ ] Decide on a visual direction (clean dashboard / dark mode / light). If you have none, tell the agent "light, calm, high-contrast dashboard".

**After the phase** (visual review is a human job)
- [ ] Run `make dev`, open **http://localhost:5173** and **look at it**: Is the Gantt readable? Are waits visibly hatched? Does the load line stay under capacity?
- [ ] Check there is **no green/amber/red used anywhere except** kept/moved/broken.
- [ ] Switch scenarios (baseline, impossible, stress) and check the stress view isn't unusable at 100 deliveries.
- [ ] Disconnect from the network and reload: it must work fully offline (no CDN requests; check the browser Network tab).
- [ ] **No API keys needed.**

---

## Phase 13 — Frontend II: disruptions, compare, diff, verify, limits

### Goal
The full demo path in the UI: disruption console (form + text), editable confirm card with highlighted spans, impact preview, side-by-side compare with ghost stops, diff table with reasons, verify panel and the Method & Limits page.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md, docs/pitch/DESIGN.md, the generated schema.d.ts (run `make types` first) and the existing frontend. Run in REAL mode against the API. You own frontend/ (P4) and frontend/src/features/disruptions/ (P3 content; you are doing both now).

FEATURES
1. features/disruptions/DisruptionConsole.tsx — two tabs: Form | Text report. DisruptionForm.tsx handles road closure (edge A-B, mode, value, direction, start/end), vehicle failure (vehicle, time, transfer minutes), urgent delivery (location, demand, window, service time, priority). Dropdowns populated from the scenario (so unknown places are impossible via the form).
2. Text flow: textarea -> POST /disruptions/interpret -> ConfirmCard.tsx. useProposal.ts holds TanStack Query mutations for interpret/preview/confirm/discard.
3. ConfirmCard.tsx — EDITABLE parsed fields; SourceSpanHighlight.tsx highlights the extracted spans in the original text; AMBER assumptions list (visible, each editable via its field); RED rejection list (if any rejection, Confirm is DISABLED and the card explains why); ImpactPreview.tsx shows the predicted counts before confirm. Edits re-preview. The Confirm button calls /proposals/{id}/confirm. The UI must never be the only gate — the server enforces it too.
   NOTE: the amber/red colors here denote assumptions/rejections; to respect the reserved-colors rule, use the designated "assumption" and "error" tokens defined in tokens.css, distinct from the moved/broken tokens, and document this in DESIGN.md.
4. features/compare/CompareView.tsx — original | revised on a SHARED time axis (use lib/timeScale.ts). GhostStop.tsx draws a ghost outline where a stop used to be. NowScrubber.tsx scrubs 'now' and shows each vehicle's state at that time. VersionSelector.tsx switches versions and triggers undo.
5. features/diff/DiffTable.tsx — rows with Kept/Moved/Broken filter chips, a reason sentence per row, a NEW badge for urgent deliveries, the earliest-feasible-ETA hint for broken rows, hover cross-highlighting between table, Gantt and map (via the Zustand store). ★ CustomerMessages.tsx (draft message per moved/broken delivery, templates only, no LLM) and ★ exportDiff.ts (CSV/JSON download). Cut the stars first.
6. features/verify/VerifyPanel.tsx — live I1-I12 checklist from the ValidationReport, green ticks (OK) / red crosses with details; shows after every plan; a "Re-validate" button hitting /validate.
7. features/limits/MethodAndLimits.tsx — the Method & Limits page: the algorithm in plain steps (pre-screen, construct, improve, replan, diagnose, gate), the assumptions D1-D10, the stated limits, and the measured numbers (fuzz case count; optimality gap) loaded from a generated JSON file docs/metrics.json (render "pending" if the file is absent; Phase 14 fills it).
8. Error states: validator failure -> clear banner "Plan discarded: validation failed" with the report; network error; empty states.
9. Playwright smoke test frontend/e2e/demo-path.spec.ts: load baseline -> closure via form -> preview -> confirm -> see kept/moved/broken with reasons -> verify panel all green -> text failure report -> confirm card -> confirm -> text with an unknown place -> rejected, nothing changed.

Capture screenshots into docs/pitch/screenshots/. Run `make check` and the Playwright test. Report what remains.
```

### Message for me

**After the phase** (**the most important manual check**: play the demo yourself)
- [ ] Run `make dev` and **walk the entire demo path by hand** (see the 5-minute demo in the plan): morning plan → closure by form → failure by text → hostile text → urgent delivery → verify panel → limits page.
- [ ] Type **5 reports of your own**, including a deliberately wrong place name; confirm that nothing changes and the rejection is clear.
- [ ] Check that every Moved/Broken row has a **reason sentence** and that hover highlights across views.
- [ ] Confirm the Confirm button is **disabled** when rejections exist, and that calling the confirm endpoint directly (Swagger) is still blocked server-side.
- [ ] Note UI annoyances in a list for Phase 15 polish.
- [ ] Run `make score`; target **≥ 70 %** acceptance (Gate G2).
- [ ] **Take a break** (the plan's G2 break matters; fatigue causes the worst bugs later).
- [ ] **No API keys needed** (unless you're using the optional LLM extractor, which is already configured).

---

## Phase 14 — Hardening: fuzzing, edge cases, performance, optimality gap

### Goal
Evidence, not claims: 1,000+ fuzz cases green, an edge suite, a performance budget met, and an optimality-gap number for the Method & Limits page.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md, all of engine/, replan/, verify/, diff/, nlp/, api/, and the tests. This phase is about BREAKING the system, then fixing it. Work in this order and report after each step.

1. tests/property/test_fuzz_invariants.py — Hypothesis fuzzers: random small scenarios (seeded generator from data/generators with randomized size, windows, capacities) x random SEQUENCES of 1-3 disruptions (closure, failure, urgent, at random times) -> after each replan assert I1-I8, I11, I12 via verify.validate plus determinism (run twice). On failure, print the seed and write a replayable JSON (scenario + disruption sequence) to tests/property/failures/. Target 1,000+ cases green (`make fuzz`, marked slow). Fix every bug it finds in the right module, adding a regression test for each (tests/edge/).
2. tests/edge/test_edge_suite.py — failure at t=0; failure exactly at a stop's end; failure on an idle vehicle; failure of the only vehicle; closure on an unused edge; overlapping closures; closure ending before the vehicle arrives; urgent delivery that cannot be placed; urgent delivery at exactly window boundaries; replan-of-replan (3 deep); no-op replan = all kept; zero-demand parcel; a delivery with a window that has already passed at `now`; everything-frozen scenario.
3. Performance: add scripts/profile.py; measure build_plan and replan at 100 deliveries / 10 vehicles and at 200 / 15. Target <= 2 s per replan at 100/10 and about 2-3 s at 200/15. Profile and fix hot spots (the insertion cache, avoiding repeated full simulations, early pruning) WITHOUT changing outputs (determinism tests must still pass). Record results in docs/metrics.json.
4. Optimality gap: complete engine/benchmarks/bruteforce.py (enumerate all assignments/sequences on tiny instances, e.g. 6-8 deliveries / 2 vehicles) and compare the heuristic objective over, say, 50 seeds; report mean and max gap. ★ engine/benchmarks/ortools_bench.py (optional extra `bench`): compare against OR-Tools on mid-size instances; never imported by runtime code. Write both results to docs/metrics.json together with the fuzz case count and date. The Method & Limits page reads this file.
5. ★ Hold-at-origin: if a closure would create a non-FIFO anomaly (leaving later arrives earlier), allow the vehicle to hold at origin; add a test. ★ Decision trace (engine/trace.py) wired into ReplanResult.trace and shown in the UI if time allows.
6. Judge-chaos pass: run a script that feeds 100 random hostile text reports to /disruptions/interpret and asserts: no 500s, no state changes without confirm, every unknown place rejected.
7. Final regression: `make check`, `make fuzz`, `make score` (target 100% acceptance), Playwright demo test.

Report: bugs found by fuzzing (with root causes), final timings, optimality-gap numbers, fuzz case count.
```

### Message for me

**After the phase** (**Gate G3, feature freeze**)
- [ ] `make score` → **100 %** acceptance tests.
- [ ] `make fuzz` → **1,000+** cases green; write the number down for your slides.
- [ ] Check `docs/metrics.json` has the **optimality-gap**, **timing** and **fuzz** numbers, and that the Method & Limits page displays them.
- [ ] Confirm replan time at 100/10 meets **≤ 2 s** on the **demo laptop**, not just your dev machine.
- [ ] If the performance goal is missed, decide the trade-off with the agent (for example fewer ruin-and-recreate iterations for large instances) rather than letting it rewrite the solver.
- [ ] **Stop adding features** after this phase; only bug fixes and polish from here on.
- [ ] If you want the OR-Tools benchmark: `uv sync --extra bench` (internet needed for the install only). It's optional.

---

## Phase 15 — Packaging, demo, README and pitch material

### Goal
One-command offline demo, a pre-seeded state, a README that proves the claims, and the 5-minute script.

### Prompt

```text
Read CLAUDE.md, docs/ASSUMPTIONS.md, docs/pitch/, docs/metrics.json and the current UI. You own packaging, docs and polish.

TASKS
1. `make demo` / scripts/demo.sh — ONE command, fully OFFLINE: builds the frontend if dist is stale, starts FastAPI serving the built UI on localhost:8000 with a PRE-SEEDED state (the city baseline plan already loaded, with the first disruption ready to apply), opens nothing automatically that needs the internet, and prints the URL. Environment: REROUTE_MOCK_MODE=false, LLM off by default. Confirm no external requests are made (document how to verify in the browser's Network tab).
2. Polish the UI from my notes below (visual hierarchy, diff transitions, consistent spacing, tooltips, copy). Keep tokens: green/amber/red reserved. Do not add features.
   MY UI NOTES: <paste your list from Phase 13 here>
3. README.md — overview, screenshots, architecture diagram (text), the algorithm in plain steps, assumptions D1-D10, stated limits, how to run (setup, dev, demo, check, fuzz, scenarios), evidence (acceptance count, fuzz count, optimality gap, timings from docs/metrics.json), repo map (from docs/FILE_STRUCTURE.md), and the one-line answers to the four predictable challenges (is it optimal / how do you know it never overloads / vague reports / failed-vehicle cargo).
4. docs/pitch/demo_script.md — the 5-minute demo: 0:30 morning plan (hatched waits, load line, two unplaced with reasons); 1:00 closure via form -> preview -> apply -> side-by-side with reasons; 1:00 vehicle failure by text (highlighted interpretation, assumptions, confirm; rescue pickup appears; completed stops unchanged); 0:30 hostile report with an unknown place is rejected, nothing changes; 0:45 urgent delivery placed, load line never crosses capacity; 0:45 verify panel all green + fuzz and optimality numbers + Method & Limits; 0:30 hand the keyboard to a judge. For EACH step: exact text to type/click, expected result, and a fallback if it misbehaves. Use the real place names from the generated city.
5. docs/pitch/limits_slide.md — the stated limits slide, plain bullets.
6. docs/pitch/QA.md — 12 likely judge questions with 2-sentence answers (optimality, overload guarantee, vague reports, failed cargo, scale, why not OR-Tools, why heuristic, windows hard, determinism, what's not handled, LLM usage, how the gate works).
7. Make sure `.env` is git-ignored and `.env.example` documents every variable.
8. Run: clean install simulation (`git clone` into a temp dir -> `make setup` -> `make check` -> `make demo`) and report results.

Report anything that failed in the clean-clone test.
```

### Message for me

**Before the phase**
- [ ] Paste your UI-annoyance list from Phase 13 into the prompt where it says `<paste your list>`.

**After the phase**
- [ ] **Run `make demo` with Wi-Fi turned off.** It must work. Check the browser Network tab for any external request.
- [ ] **Read `demo_script.md` out loud** and do one timed dry run on the **demo laptop**. Adjust wording until it fits in 5 minutes.
- [ ] **Record a backup screen recording** of the full demo path (OBS, QuickTime, or any recorder). This is your insurance if the live demo fails.
- [ ] Prepare a **second laptop** with a clean clone (`make setup && make demo`) as backup.
- [ ] Assign who speaks which part. Rehearse once (the plan says from 8:15).
- [ ] If you're submitting slides: build the deck from `docs/pitch/` and the screenshots in `docs/pitch/screenshots/` (I can generate the deck in a separate request).
- [ ] **Keys:** if you plan to demo the LLM extractor, put the key only on the demo laptop's local `.env`. If the venue network is unreliable, keep `REROUTE_LLM_ENABLED=false`; the rule-based path is the default and is demo-safe.

---

## Phase 16 — Final QA and submission

### Goal
A frozen, verified, submitted build with time to spare.

### Prompt

```text
CODE FREEZE. Only critical fixes from now on. Read CLAUDE.md and docs/pitch/. Do the following and report each result as PASS/FAIL with evidence:

1. `git status` clean; `.env` not tracked; no secrets anywhere (grep the repo and git history for "sk-", "ANTHROPIC_API_KEY=" with a value, and tokens).
2. Fresh clone into a temp directory: `make setup && make check && make fuzz && make score && make demo` — all green; demo reachable at localhost:8000 offline.
3. Walk the demo script step by step through the API (curl or a script, scripts/demo_smoke.py) and assert every expected outcome: initial plan with 2 unplaced; closure with kept/moved/broken counts and reasons; failure by text with confirm; hostile text -> 422 and unchanged state; confirm without proposal -> 409; urgent placed with NEW badge; validator all green after each step.
4. Judge-chaos: 50 random hostile texts and 50 random structured disruptions at random times; no 500s, no invariant failures.
5. Verify README claims against docs/metrics.json (numbers must match exactly; no hand-typed numbers).
6. Check licenses of dependencies quickly (pip-licenses / pnpm licenses) and list anything unusual.
7. Produce docs/SUBMISSION_CHECKLIST.md with the results and the exact commands to run the project from a clean machine.
8. Tag the release (e.g. v1.0-submission). Do not make any further changes unless a check fails.

If any check fails, fix the minimal thing, re-run the full list, and report.
```

### Message for me

**After the phase**
- [ ] **Code freeze at the agreed time.** Any change after this needs two-person review.
- [ ] Run the **clean-clone test on a second machine**.
- [ ] Do **two timed dry runs** on the demo laptop. Hand the keyboard to a teammate and have them type a hostile report.
- [ ] Verify the backup video plays, and keep the second laptop ready.
- [ ] **Submit with at least 20 minutes of buffer.** Confirm the submission link, repo access (add judges/organizers if the repo is private), and the demo/slides upload.
- [ ] Final check: **no API key in the repo**; the submission must not contain your `.env`.
- [ ] Rotate/delete the Anthropic API key after the event if you created it only for this.

---

## Appendix A — Human-task summary (everything you must supply or decide)

| When | Task |
|------|------|
| Before Phase 1 | Install Python 3.12, uv, Node LTS, pnpm, git, make; create the private repo; **save the original problem statement as `docs/SPEC.md`**. |
| Before/at Phase 1 | Ask organizers: sample dataset/format? Windows hard? Failed-vehicle parcel transfer? Depot return / shift end? Update `docs/ASSUMPTIONS.md` with answers. |
| Phase 2 | Review `contract/models.py`; hand-verify the micro-scenario; tag `contract-v1`. |
| Phase 7 | Choose the city whose place names are used; import the organizers' dataset if one exists. |
| Phase 10 (optional) | **Anthropic API key** → local `.env` (`ANTHROPIC_API_KEY`, `REROUTE_LLM_ENABLED=true`, `REROUTE_LLM_MODEL`). Never commit it. |
| Phase 12 | Download local `.woff2` fonts (no Google Fonts links); choose a visual direction. |
| Phases 8, 13 | Approve the solver/replanner approach headers; play the demo by hand. |
| Phase 14 | Confirm 100% acceptance, 1,000+ fuzz cases, performance on the demo laptop; **feature freeze**. |
| Phase 15 | Offline `make demo` test, backup video, second laptop, rehearse. |
| Phase 16 | Clean-clone test, submit with buffer, remove secrets, rotate the key. |

## Appendix B — External keys and accounts

| Item | Required? | Used for | Where it goes |
|------|-----------|----------|---------------|
| Anthropic API key | **Optional (★)** | The LLM text extractor (`nlp/llm_extractor.py`) only | Local `.env` as `ANTHROPIC_API_KEY`; never committed |
| GitHub account/repo | Recommended | Shared memory, CI (`make check`) | n/a |
| OR-Tools | Optional (★) | Benchmarks only (`uv sync --extra bench`) | Not a runtime dependency |
| Map/tile providers | **Not used** | The spec forbids live mapping; the map is a schematic SVG | n/a |

Every other part of the system (solver, validator, parser, API, UI) runs **offline with no keys**.

## Appendix C — Prompt hygiene tips

- **Fresh session per phase**, and for large phases (5, 8, 13) split at the sub-numbered tasks if the agent starts to drift or the output gets truncated.
- **Paste failing output** (full `make check` error) instead of describing it.
- For the solver and replanner, the **"state your approach first"** step lets you correct a wrong direction in two minutes instead of two hours.
- **Cross-review adversarially**: after any big module, open a new session and say: *"Construct an input that breaks invariant I2 / I5 / I6 in this module."*
- If the agent wants to change the contract, it must write it in `docs/CONTRACT_CHANGES.md` and ask you. After `contract-v1`, only **additive optional fields** are allowed.
- If something slips past a gate: **G1** (initial plan renders) slipping by >30 min → drop ruin-and-recreate and the map; **G2** (disruptions end to end) slipping → text for closure and failure first, urgent via form only.
