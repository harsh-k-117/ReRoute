# CONTEXT.md — ReRoute (S-01: Dynamic Fleet & Delivery Replanning)

> Shared source of truth for all four team members (and their Claude sessions). Read this first. The timeline, lanes and gates live in `ROADMAP.md`; both files are consistent with each other.

## Contents

1. [Project Overview](#1-project-overview)
2. [Objectives](#2-objectives)
3. [Mandatory Requirements](#3-mandatory-requirements)
4. [Locked Decisions (D1–D10)](#4-locked-decisions-d1d10)
5. [Constraints and Stated Limits](#5-constraints-and-stated-limits)
6. [Tech Stack](#6-tech-stack)
7. [System Architecture](#7-system-architecture)
8. [Shared Data Models and Contracts](#8-shared-data-models-and-contracts)
9. [Invariants Enforced by the Validator](#9-invariants-enforced-by-the-validator)
10. [Module Ownership](#10-module-ownership)
11. [Development Principles](#11-development-principles)
12. [Open Questions for Organizers](#12-open-questions-for-organizers)

---

## 1. Project Overview

**ReRoute** is a dynamic fleet and delivery replanning system (problem statement **S-01**). It builds a morning delivery plan for a fleet, then replans from the *current state* when a disruption occurs: a **road closure**, a **vehicle failure**, or a **new urgent delivery**. Disruptions can be entered as a structured form or as free text.

The dispatcher stays in control: **propose → preview → confirm**. Nothing is applied until confirmed.

No plan can promise a win, so the project is built so that every line of the spec has visible proof, which is how a team beats others with a prettier map and a weaker engine.

---

## 2. Objectives

Optimize for three things judges can see in five minutes:

1. **The engine never emits an invalid plan, and shows the proof.**
2. **Every kept / moved / broken verdict has a real cause.**
3. **The dispatcher stays in control** (propose → preview → confirm).

---

## 3. Mandatory Requirements

Every spec line must have something that can be pointed at on stage. The 15 numbered requirements (R1–R15) are written out in `docs/REQUIREMENTS.md` at the start of the hackathon (requirement → module → test → demo step). They cover the following areas.

| Spec line | Mechanism | Proof on stage |
|-----------|-----------|----------------|
| Matrix-only inputs, explainable algorithm, limits, arrivals + waits | One simulator; regret insertion + ruin-and-recreate; schematic map only | Gantt with hatched waits; Method & Limits page |
| Never overload at any point; unplaceable → reason | Load checked at the start and after every pickup; per-vehicle diagnostics | Load-vs-capacity line under each route; unplaced list with reasons; fuzz result |
| Three disruptions, structured or text | Disruption union + one `replan()` | Live demo of each, in both input modes |
| Confirm before effect; unknown location rejected | Propose → preview → confirm; exact-match resolver | Server returns 409 without confirm and 422 on an unknown place; a judge types a hostile report |
| Replan from current state; nothing after failure | `snapshot(now)` + freeze rule | I5/I6 invariants; Verify panel |
| Side-by-side, kept/moved/broken with reason | Reason ledger → diff | Compare view; every row carries a cause code and a sentence |

**Never cut** (non-negotiable): the validator gate, the confirm gate with unknown-location rejection, reasons on every diff row, the side-by-side view, and the Method & Limits page.

---

## 4. Locked Decisions (D1–D10)

Locked in the first 20 minutes and recorded in `docs/ASSUMPTIONS.md`. **Do not re-debate them.**

| # | Decision |
|---|----------|
| D1 | Time is integer minutes since midnight; the matrix is in minutes (round fractions up). |
| D2 | A window constrains service start. Early arrival waits: `start = max(arrival, open)`, `depart = start + service time`. Wait is always shown. |
| D3 | Cargo model: every parcel is either on board or needs a pickup stop. Morning plan: all loaded at the depot. Urgent delivery: picked up at the depot, released at report time. Failed vehicle: its undelivered parcels are picked up at its last known stop (or depot) after the failure plus a transfer time (config flag). Load is checked at the start and after every pickup, which is what "never overloaded at any point" requires. |
| D4 | Closure: raises that edge's time (+N min, new value, or ×k; both directions unless stated) for departures in `[max(start, now), end)`. Matrix entries are direct times; no automatic detours. |
| D5 | Freeze: a stop is fixed if its service ended ≤ now, is in progress, or the vehicle is already driving to it. A failed vehicle keeps only stops finished by its failure time. |
| D6 | Objective, in order: fewest priority-weighted broken → fewest moved/shifted → least travel + wait. Urgent priority = 2. |
| D7 | Classes: **kept** = same vehicle, ETA within ±5 min; **moved** = other vehicle or larger ETA/sequence change, still in window; **broken** = cannot be placed in its window. A new urgent delivery is classed moved (placed) or broken (not placed) and always badged NEW. |
| D8 | Text: interpret → preview → confirm. An unknown or ambiguous location/vehicle rejects the whole report; no fuzzy matching. Missing optional fields get visible, editable defaults. |
| D9 | Windows are hard. For a broken delivery we show the earliest feasible ETA as a negotiation hint, never silently serve it late. |
| D10 | Deterministic: seeded RNG, iteration budgets instead of wall-clock, ties broken by ID. |

If organizers provide a dataset, the contract adopts their field names while D1–D10 stay. If an answer contradicts D2, D3 or D9, change that one assumption; the architecture does not move.

---

## 5. Constraints and Stated Limits

### Constraints

- **No live mapping and no tile map** (the spec forbids it). Use a schematic SVG from x/y if supplied, else a layout computed from the time matrix (classical MDS).
- **Offline operation:** local fonts, no CDNs, no network dependency; venue Wi-Fi is unreliable. No map libraries.
- **No network calls** except the optional, flagged LLM extractor (with timeout and fallback).
- **Inputs are matrix-based** (travel-time matrix in minutes).
- **Deterministic** output: same input and seed give the same output.
- **One writer per directory**; no edits outside your lane.
- **Rules on pre-written code:** check them and don't pre-build the project if it's forbidden.

### Stated limits (shown on the Method & Limits page / slide)

- It is a heuristic with no optimality guarantee; the measured gap on small instances is quoted.
- It handles one depot, one capacity dimension and no split parcels.
- Closures are modeled by departure time on a direct edge, with no mid-edge rerouting and no automatic detours.
- Vehicles in transit are committed to their next stop.
- Windows are hard.
- Target scale: up to **200 deliveries and 15 vehicles in about 2–3 s** (performance budget: ≤ 2 s per replan at 100 deliveries / 10 vehicles).

---

## 6. Tech Stack

| Layer | Pick | Why |
|-------|------|-----|
| Engine + API | Python 3.12, FastAPI, Pydantic v2, uv | Fastest to write and test algorithms with Claude. The Pydantic models are the contract: they generate OpenAPI, which generates TypeScript types, so UI and API can't drift. |
| Solver | Custom pure Python: regret-2 insertion + ruin-and-recreate | Explainable in a minute. Handles time-dependent closures, frozen prefixes and pickups natively, with no solver dependency to break on the day. OR-Tools is a black box and awkward for time-dependent closures. |
| Oracles | Brute-force enumeration on tiny instances; OR-Tools only in benchmarks (★) | Lets us quote an optimality gap when asked about limits. |
| Verification | pytest, Hypothesis, ruff | Property-based fuzzing of the invariants is the strongest credibility signal. |
| Text input | Rule-based parser + exact-match location resolver (primary). ★ Optional LLM extractor (Anthropic API, JSON output) behind a flag, with timeout and fallback | The primary path is offline and deterministic. The LLM only extracts mentions as written and never sees the location list; our resolver decides, so it can't "guess" a place. |
| Frontend | Vite, React, TypeScript, Tailwind, shadcn/ui, TanStack Query, Zustand, custom SVG + d3-scale, openapi-typescript | Quickest route to a polished, interactive UI. Hand-rolled SVG gives full control of the Gantt, load profile and diff ghosts. |
| Map | Schematic SVG (see Constraints) | No network dependency, and it looks intentional. |
| Packaging | `make dev` / `check` / `demo`; FastAPI serves the built UI | One offline command. |
| Collaboration | Private GitHub repo, trunk-based, `CLAUDE.md`, `make check` as the merge gate | The repo is the only shared memory across four separate Claude accounts. |

★ = differentiator; cut these first if a gate slips.

---

## 7. System Architecture

```
Scenario (JSON/CSV)
  └─ engine ── simulate_route: ONE source of truth for times, waits, load
        └─ build_plan: regret insertion → ruin-and-recreate

Disruption (form, or text → interpret → CONFIRM)
  └─ replan: snapshot(now) → freeze → apply → repair/eject → reinsert → improve
        ├─ verify: independent validator, a hard gate before anything is shown
        └─ diff: reason ledger → kept / moved / broken, each with a cause

FastAPI ──► React UI: Gantt · schematic map · side-by-side · confirm card · verify panel
```

### Algorithm (in the order it is explained)

1. **Pre-screen.** Reject impossible deliveries up front with a reason: oversize, window unreachable even as the first stop, unknown location.
2. **Construct.** Parallel regret-2 insertion: repeatedly place the delivery whose best and second-best vehicle options differ most, at its cheapest feasible position. Feasible means a full forward simulation passes (load ≤ capacity at the start and after every pickup, all windows met, shift end respected). Best insertions are cached per (delivery, vehicle) so only the changed route is re-evaluated.
3. **Improve.** Ruin-and-recreate: remove a related cluster (10–25% of deliveries), reinsert by regret, keep the result if the objective improves. Fixed iterations and seed make it reproducible.
4. **Replan.** `snapshot(now)` freezes what's done or committed and computes each vehicle's ready location, ready time and on-board load. Apply the disruption (time-dependent travel function, vehicle availability, new or orphaned parcels with pickup stops). Re-simulate every free suffix with windows softened, fix locally, eject whatever still violates (logging the cause), reinsert the pool with a stability-weighted objective, then run a short ruin-and-recreate on free suffixes only. Starting from the old plan and changing the minimum keeps the number of customers touched low.
5. **Diagnose.** For every unplaced delivery, report each vehicle's binding constraint, plus ★ the "what would it take" hint (earliest feasible ETA if the window were relaxed).
6. **Gate.** The independent validator must pass before a plan is shown or committed. If it fails, the replan is discarded and the dispatcher sees an error, never a bad plan.

### Disruption handling

| Disruption | Behavior |
|------------|----------|
| **Closure** | Re-simulate suffixes with windows softened, fix locally, eject remaining violators, reinsert. |
| **Failure** | Cut at the failure time, orphan parcels, add rescue pickups, reinsert. |
| **Urgent** | Pickup at the depot with a release time, insert, displace lower priority only if necessary. |

### Reason ledger

Every eject, insert or move records a cause: `completed`, `vehicle_failed`, `closure_delay`, `displaced_by_urgent`, `knock_on`, `no_feasible_slot`. `classify()` reads the ledger to produce kept / moved / broken.

### Unplaced-delivery reason codes

`oversize`, `window unreachable`, `no capacity at stop k`, `pushes stop X late`, `no vehicle available`.

### Text-input pipeline

- Rules for the three disruption types plus a small time grammar (`10:30`, `3pm`, `until 14:00`, `for 2 hours`, `in 30 min`), with assumptions and warnings.
- Location/vehicle resolver: normalize case, space and punctuation, support aliases, **exact match only**, ambiguous → reject.
- Confirm card: parsed fields, highlighted source spans, amber assumptions, red rejections, impact preview. A failed parse falls back to the pre-filled form.
- ★ Optional LLM guardrails: the mention must appear verbatim in the text and resolve exactly, with a timeout and fallback.

### API surface

| Endpoint | Purpose |
|----------|---------|
| `/scenarios` | List / load scenarios |
| `/plan/initial` | Build the morning plan |
| `/state` | Current state and plan versions |
| `/validate` | Run the independent validator |
| `/disruptions/preview` | Preview a structured disruption |
| `/disruptions/interpret` | Interpret a text report into a proposal |
| `/proposals/{id}/confirm` | Confirm a proposal (server-enforced gate; 409 without confirm) |
| `/proposals/{id}/discard` | Discard a proposal |

Additional behavior: mock mode serves fixtures from every endpoint; a session + plan-version store supports undo; unknown location returns 422 and leaves state unchanged. CLI: `reroute plan|replan|validate`.

### Frontend views

Gantt per vehicle (travel, hatched wait, service blocks, window brackets, load-vs-capacity step line, "now" line); stop table; unplaced panel with reasons; schematic map; compare view (original | revised on a shared time axis with ghost outlines); diff table with Kept/Moved/Broken filters and hover cross-highlighting; version selector and "now" scrubber; disruption console with editable confirm card; Verify panel (live I1–I12 checklist); Method & Limits page; empty/error/loading states.

**Design tokens:** green / amber / red are reserved for kept / moved / broken only.

---

## 8. Shared Data Models and Contracts

All models live in `contract/` (Pydantic v2 models, JSON fixtures, function signatures). It is the **one shared directory**, frozen at **1:00** and tagged `contract-v1`. After the freeze, changes are **additive only** (new optional fields), announced in chat, and signed off by P1 and P3. If organizers supply a dataset, their field names are adopted in the contract.

### Models

| Model | Contents |
|-------|----------|
| `Scenario` | Depot, vehicles (capacity, availability, shift end), deliveries (location, demand, time window, service time, priority), travel-time matrix (minutes), optional x/y for schematic layout, location names/aliases. |
| `Plan` / `Route` / `Stop` | A plan has one route per vehicle; a route is an ordered list of stops (delivery or pickup) carrying arrival, wait, service start, depart, load-after, and violations (all produced by `simulate_route`); plus the unplaced list with reasons. |
| `Disruption` (union) | `Closure` (edge, effect: +N min / new value / ×k, direction, start/end), `VehicleFailure` (vehicle, failure time), `UrgentDelivery` (new delivery, report time, priority = 2). |
| `Proposal` | A parsed/previewed disruption awaiting confirmation: fields, source spans, assumptions, warnings, rejections, impact preview. Cannot be applied without confirm (I10). |
| `ReplanResult` | New plan, reason ledger, diff, validation report. |
| `Diff` | Per-delivery row: class (kept / moved / broken), NEW badge where applicable, cause code, human sentence, old/new vehicle and ETA. |
| `ValidationReport` | Per-invariant (I1–I12) pass/fail with offending items. |

### Function signatures (stubbed from minute one)

| Module | Signatures |
|--------|-----------|
| `engine/` | `simulate_route`, `build_plan`, `insert_deliveries(state, pool, objective)`, `improve`, `diagnose_unplaced` |
| `replan/` | `snapshot(plan, now)`, `replan()`, reason ledger, `classify()` |
| `verify/` | Independent validator (does **not** import the engine's simulator) |
| `nlp/` | Interpreter, time grammar, location/vehicle resolver |

`snapshot(plan, now)` returns per-vehicle frozen prefix, ready location, ready time, on-board load, and breakdown site.

### Scenario pack (7 named scenarios)

baseline, closure, failure, urgent, cascade, stress (100 deliveries / 10 vehicles), impossible. The "city" generator uses real place names (the text demo depends on them), one bridge edge many routes cross, a few tight windows, and two deliberately impossible deliveries.

---

## 9. Invariants Enforced by the Validator

| ID | Invariant |
|----|-----------|
| I1 | Every delivery appears exactly once, placed or unplaced with a reason. |
| I2 | Load ≤ capacity at the start and after every pickup. |
| I3 | Service start is inside the window, and `wait = max(0, open − arrival)`. |
| I4 | Travel times equal the matrix plus the closure rule. |
| I5 | Nothing on a failed vehicle after its failure time. |
| I6 | Frozen stops are byte-identical. |
| I7 | A pickup precedes its delivery on the same vehicle. |
| I8 | Every moved or broken row has a cause. |
| I9 | An unknown location is rejected and state is unchanged. |
| I10 | Text disruptions can't apply without confirm. |
| I11 | Same input and seed give the same output. |
| I12 | A no-op replan changes nothing. |

---

## 10. Module Ownership

| | Role | Owns (single writer) | Ships |
|---|------|----------------------|-------|
| **P1** | Algorithm lead | `engine/` | `simulate_route`, `build_plan`, `insert_deliveries`, `improve`, `diagnose_unplaced` |
| **P2** | Replan & quality lead | `replan/`, `verify/`, `diff/`, `tests/acceptance/` | Acceptance tests, independent validator, snapshot, replan, reason ledger, classify, fuzzers |
| **P3** | Integration & language lead | `api/`, `nlp/`, `data/`, `scripts/`, `frontend/src/features/disruptions/` | API, mock mode, version store, confirm gate, interpreter, scenario generator and importers, CLI, make targets |
| **P4** | UX & story lead | Rest of `frontend/`, `docs/pitch/` | Gantt, schematic map, compare view, KPIs, verify panel, Method & Limits page, demo script and deck |

Suggested assignment: P1 = strongest algorithm person, P2 = most test-minded, P3 = best generalist, P4 = best frontend person and presenter.

---

## 11. Development Principles

- **The repo is the shared brain.** `CLAUDE.md` is the first thing every session reads: brief, R1–R15, D1–D10, architecture, lane ownership, commands, definition of done, and don'ts (no map libraries, no network calls except the flagged LLM extractor, no edits outside your lane).
- **One writer per directory.** Cross-lane needs go in `docs/CONTRACT_CHANGES.md` or a PR comment, never a silent edit.
- **Fixtures first.** UI and API never wait for the engine (mock mode plus golden fixtures); the engine never waits for the UI.
- **Tests first.** Every session starts from failing acceptance tests for its requirement IDs.
- **Pure and deterministic.** Keep functions pure; seeded RNG, iteration budgets instead of wall-clock, ties broken by ID.
- **One source of truth for simulation.** The engine's `simulate_route` is the only simulator in the engine; the validator is written independently from the spec.
- **Validator gate.** No plan is shown or committed unless the validator passes.
- **Adversarial cross-review.** Before merging a major module, a different lane's Claude is asked to "construct an input that breaks invariant I2 / I5 / I6." The validator author (P2) attacks the solver (P1).
- **Small PRs, trunk-based.** Merge at least hourly. `make check` (ruff, pytest, tsc, build) must be green and main must always run. Use one clone or worktree per session.
- **Fresh session per task (≤ 60 min).** Paste failing output instead of describing it. For the solver and replanner, make Claude state its approach first and have the lane owner approve it in two minutes.
- **Pace usage.** Account limits are real: keep prompts focused and stagger heavy generation. If one account runs dry, the lane's tests and docs let a teammate take over.
- **Sync.** 5-minute stand-up each hour (done / next / blocked), with hard gates at 3:00, 5:30, 7:30 and 9:00.
- **Scope discipline.** Do not add features beyond the spec. ★ items are cut first.

---

## 12. Open Questions for Organizers

Ask in the first 15 minutes:

- Is there a sample dataset or file format?
- Are windows hard?
- Can a failed vehicle's parcels be transferred (where and when)?
- Must vehicles return to the depot, or is there a shift end?

Answers update only the affected assumption (D2, D3, D9, or contract field names); the architecture does not change.