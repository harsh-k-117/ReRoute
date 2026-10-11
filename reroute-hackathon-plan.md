# ReRoute:

1. [Lock these decisions in the first 20 minutes](#1-lock-these-decisions-in-the-first-20-minutes)
2. [Tech stack](#2-tech-stack)
3. [How it works](#3-how-it-works)
4. [Lanes](#4-lanes)
5. [Timeline](#5-timeline)
6. [Four Claude sessions without collisions](#6-four-claude-sessions-without-collisions)
7. [Proof and demo](#7-proof-and-demo)
8. [Risks and cut-lines](#8-risks-and-cut-lines)

---

## 1. Lock these decisions in the first 20 minutes

Most hackathon rework comes from ambiguous semantics. Put these in `docs/ASSUMPTIONS.md` and don't re-debate them.

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

**In the first 15 minutes, ask the organizers:**

- Is there a sample dataset or file format?
- Are windows hard?
- Can a failed vehicle's parcels be transferred (where and when)?
- Must vehicles return to the depot, or is there a shift end?

If they give a dataset, the contract adopts their field names while D1–D10 stay. If an answer contradicts D2, D3 or D9, change that one assumption; the architecture doesn't move.

---

## 2. Tech stack

| Layer | Pick | Why |
|-------|------|-----|
| Engine + API | Python 3.12, FastAPI, Pydantic v2, uv | Fastest to write and test algorithms with Claude. The Pydantic models are the contract: they generate OpenAPI, which generates TypeScript types, so UI and API can't drift. |
| Solver | Custom pure Python: regret-2 insertion + ruin-and-recreate | Explainable in a minute. Handles time-dependent closures, frozen prefixes and pickups natively, with no solver dependency to break on the day. OR-Tools is a black box and awkward for time-dependent closures. |
| Oracles | Brute-force enumeration on tiny instances; OR-Tools only in benchmarks (★) | Lets us quote an optimality gap when asked about limits. |
| Verification | pytest, Hypothesis, ruff | Property-based fuzzing of the invariants is the strongest credibility signal we can show. |
| Text input | Rule-based parser + exact-match location resolver (primary). ★ Optional LLM extractor (Anthropic API, JSON output) behind a flag, with timeout and fallback | The primary path is offline and deterministic. The LLM only extracts mentions as written and never sees the location list; our resolver decides, so it can't "guess" a place. |
| Frontend | Vite, React, TypeScript, Tailwind, shadcn/ui, TanStack Query, Zustand, custom SVG + d3-scale, openapi-typescript | Quickest route to a polished, interactive UI. Hand-rolled SVG gives full control of the Gantt, load profile and diff ghosts. |
| Map | No tile map (the spec forbids live mapping). Schematic SVG from x/y if supplied, else a layout computed from the time matrix (classical MDS) | No network dependency, and it looks intentional. |
| Packaging | `make dev` / `check` / `demo`; FastAPI serves the built UI | One offline command. Local fonts, no CDNs; venue Wi-Fi is unreliable. |
| Collaboration | Private GitHub repo, trunk-based, `CLAUDE.md`, `make check` as the merge gate | The repo is the only shared memory across four separate Claude accounts. |

---

## 3. How it works

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

### The algorithm, in the order you'll explain it

1. **Pre-screen.** Reject impossible deliveries up front with a reason: oversize, window unreachable even as the first stop, unknown location.
2. **Construct.** Parallel regret-2 insertion: repeatedly place the delivery whose best and second-best vehicle options differ most, at its cheapest feasible position. Feasible means a full forward simulation passes (load ≤ capacity at the start and after every pickup, all windows met, shift end respected). Cache best insertions per (delivery, vehicle) so only the changed route is re-evaluated.
3. **Improve.** Ruin-and-recreate: remove a related cluster (10–25% of deliveries), reinsert by regret, keep the result if the objective improves. Fixed iterations and seed make it reproducible.
4. **Replan.** `snapshot(now)` freezes what's done or committed and computes each vehicle's ready location, ready time and on-board load. Apply the disruption (time-dependent travel function, vehicle availability, new or orphaned parcels with pickup stops). Re-simulate every free suffix with windows softened, fix locally, eject whatever still violates (logging the cause), reinsert the pool with a stability-weighted objective, then run a short ruin-and-recreate on free suffixes only. Starting from the old plan and changing the minimum keeps the number of customers touched low.
5. **Diagnose.** For every unplaced delivery, report each vehicle's binding constraint, plus ★ the "what would it take" hint (earliest feasible ETA if the window were relaxed).
6. **Gate.** The independent validator must pass before a plan is shown or committed. If it fails, the replan is discarded and the dispatcher sees an error, never a bad plan.

### Invariants the validator enforces

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

### Stated limits (put these on a slide)

- It is a heuristic with no optimality guarantee; we quote the measured gap on small instances.
- It handles one depot, one capacity dimension and no split parcels.
- Closures are modeled by departure time on a direct edge, with no mid-edge rerouting and no automatic detours.
- Vehicles in transit are committed to their next stop.
- Windows are hard.
- Target scale is up to 200 deliveries and 15 vehicles in about 2–3 s.

---

## 4. Lanes

| | Role | Owns (single writer) | Ships |
|---|------|----------------------|-------|
| **P1** | Algorithm lead | `engine/` | `simulate_route`, `build_plan`, `insert_deliveries`, `improve`, `diagnose_unplaced` |
| **P2** | Replan & quality lead | `replan/`, `verify/`, `diff/`, `tests/acceptance/` | Acceptance tests, independent validator, snapshot, replan, reason ledger, classify, fuzzers |
| **P3** | Integration & language lead | `api/`, `nlp/`, `data/`, `scripts/`, `frontend/src/features/disruptions/` | API, mock mode, version store, confirm gate, interpreter, scenario generator and importers, CLI, make targets |
| **P4** | UX & story lead | Rest of `frontend/`, `docs/pitch/` | Gantt, schematic map, compare view, KPIs, verify panel, Method & Limits page, demo script and deck |

Give P1 your strongest algorithm person, P2 your most test-minded one, P3 your best generalist, and P4 your best frontend person and presenter. `contract/` (Pydantic models, JSON fixtures, function signatures) is the one shared directory, frozen at 1:00.

---

## 5. Timeline

★ marks differentiators; cut these first if a gate slips.

**Before 0:00**, if the rules allow prep: install Python 3.12, uv, Node LTS, pnpm and git on all four machines, create an empty private repo, and test everyone's Claude access. Check the rules on pre-written code and don't pre-build the project if it's forbidden.

### Phase 0: Align and freeze the contract (0:00–1:00)

**All, 0:00–0:20:** lock D1–D10, assign lanes, send the organizer questions, and split the spec into numbered requirements R1–R15 in `docs/REQUIREMENTS.md` (requirement → module → test → demo step).

**P1:** `contract/` Pydantic models (Scenario, Plan/Route/Stop, Disruption union, Proposal, ReplanResult, Diff, ValidationReport) and stub signatures in `engine/`, `replan/`, `verify/`, `nlp/` so every lane can import from minute one.

**P2:** about 40 acceptance tests derived from R1–R15, all xfail on day one (the green count is the team scoreboard), plus a hand-checkable micro-scenario (3 vehicles, 8 deliveries, expected arrivals).

**P3:**
- Repo scaffold (`CLAUDE.md`, Makefile, lint/test config).
- FastAPI skeleton with mock mode serving fixtures from every endpoint.
- OpenAPI → TypeScript type script.
- A "city" scenario generator with real place names (the text demo depends on them), one bridge edge many routes cross, a few tight windows, and two deliberately impossible deliveries.
- A pack of 7 named scenarios: baseline, closure, failure, urgent, cascade, stress (100/10), impossible.

**P4:** Vite/React/Tailwind/shadcn scaffold, design tokens (green/amber/red reserved for kept/moved/broken only), and an app shell talking to mock mode.

**0:50–1:00:** 10-minute contract review by all, then tag `contract-v1`.

### Phase 1: Walking skeleton (1:00–3:00)

**P1:**
- PR #1 by 1:45: `simulate_route` (arrival, wait, start, depart, load-after, violations; closures as a time-dependent travel function) so others can use it.
- Then `build_plan`, and `diagnose_unplaced` v1 with reason codes: oversize, window unreachable, no capacity at stop k, pushes stop X late, no vehicle available.

**P2:**
- Independent validator v1, written from the spec and not importing the engine's simulator (I1–I5, I7).
- `snapshot(plan, now)` → per-vehicle frozen prefix, ready location and time, on-board load, breakdown site. Use a first-fit stub until P1's solver lands.

**P3:**
- API v1 (`/scenarios`, `/plan/initial`, `/state`, `/validate`) and a session + plan-version store with undo.
- CLI (`reroute plan|replan|validate`).
- Location/vehicle resolver: normalize case, space and punctuation, support aliases, exact match only, ambiguous → reject. Include tests.

**P4:** Gantt per vehicle (travel, hatched wait, service blocks, window brackets, load-vs-capacity step line, "now" line), stop table, and unplaced panel with reasons. Build on fixtures, then switch to the live API around 2:45.

> **Gate G1, 3:00:** the real initial plan on the city scenario renders in the UI with arrivals, waits and unplaced reasons; validator green; main green.

### Phase 2: Disruptions and replanning (3:00–5:30)

**P1:**
- `insert_deliveries(state, pool, objective)` working on frozen prefixes, ready states and pickup stops. P2 depends on it, so use a first-fit stub until about 3:45.
- Stability-weighted objective and the ruin-and-recreate improve.
- ★ "What would it take" hint.

**P2:** `replan()` for all three disruptions.
- **Closure:** re-simulate suffixes with windows softened, fix locally, eject remaining violators, reinsert.
- **Failure:** cut at the failure time, orphan parcels, add rescue pickups, reinsert.
- **Urgent:** pickup at the depot with a release time, insert, displace lower priority only if necessary.
- **The reason ledger:** every eject, insert or move records a cause (`completed`, `vehicle_failed`, `closure_delay`, `displaced_by_urgent`, `knock_on`, `no_feasible_slot`), and `classify()` reads it.
- Validator I6, I8, I12.

**P3:**
- `/disruptions/preview`, `/disruptions/interpret`, `/proposals/{id}/confirm|discard`, with a server-enforced gate.
- Rules for the three types plus a small time grammar ("10:30", "3pm", "until 14:00", "for 2 hours", "in 30 min"), with assumptions and warnings.
- The disruption console with an editable confirm card: parsed fields, highlighted source spans, amber assumptions, red rejections, impact preview.

**P4:**
- Compare view: original | revised on a shared time axis, with a ghost outline where a stop used to be.
- Diff table with Kept/Moved/Broken filters and hover cross-highlighting.
- Version selector and a "now" scrubber showing each vehicle's state.

> **Gate G2, 5:30:** all three disruptions work end to end, structured and text; the confirm gate is enforced; every diff row has a reason; the validator is green after every replan; at least 70% of acceptance tests pass. Take a 15-minute break and eat.

### Phase 3: Break it, then fix it (5:30–7:30)

**P2:**
- Hypothesis fuzzers (random scenarios × random disruption sequences → I1–I12). Failures print a seed and replayable JSON.
- Edge suite: failure at t=0, exactly at a stop's end, or on an idle vehicle; closure on an unused edge or overlapping another; unplaceable urgent delivery; replan-of-replan; no-op replan = all kept.

**P1:**
- Tune weights and profile (target ≤ 2 s per replan at 100 deliveries / 10 vehicles).
- Brute-force comparison on tiny instances for the optimality-gap number.
- ★ Hold-at-origin so a closure can't create a non-FIFO anomaly.
- ★ Decision trace ("cheapest feasible slot +6 min; runner-up V3 +11").

**P3:**
- Parser hardening with at least 30 phrasings, including hostile ones: unknown place, a partial name matching two places, missing time, contradictory info, two events in one report. A failed parse falls back to the pre-filled form.
- ★ Optional LLM extractor with guardrails: the mention must appear verbatim in the text and resolve exactly, with a timeout and fallback.
- JSON/CSV import with field-alias adapters.

**P4:**
- Verify panel (live I1–I12 checklist), Method & Limits page, empty/error/loading states.
- ★ Customer-message drafts for moved/broken deliveries, diff export (CSV/JSON).
- A Playwright smoke test of the demo path.

> **Gate G3, 7:30, feature freeze:** every R1–R15 demonstrable, acceptance tests 100%, 1,000+ fuzz cases green, performance budget met.

### Phase 4: Polish and story (7:30–9:00)

- **P4:** visual polish, diff transitions, screenshots.
- **P3:** README (architecture, algorithm, assumptions, limits, how to run, evidence), pre-seeded demo state, one-command offline `make demo`, backup screen recording.
- **P1 + P2:** bug triage only, full regression, "judge chaos" inputs, final performance run. Spare capacity goes to P4's UI backlog.
- **All, from 8:15:** write the 5-minute script, assign speaking parts, rehearse once.

### Phase 5: Rehearse and submit (9:00–10:00)

- Code freeze at 9:00; only critical fixes with two-person review.
- Two timed dry runs on the demo laptop, a clean-clone install test on a second machine, submit by 9:40, and keep 20 minutes of buffer.

---

## 6. Four Claude sessions without collisions

- **The repo is the shared brain.** Separate accounts share no memory, so `CLAUDE.md` is the first thing every session reads: brief, R1–R15, D1–D10, architecture, lane ownership, commands, definition of done, and don'ts (no map libraries, no network calls except the flagged LLM extractor, no edits outside your lane). Claude Code picks it up automatically; in chat, paste it as your first message.
- **One writer per directory.** Cross-lane needs go in `docs/CONTRACT_CHANGES.md` or a PR comment, never a silent edit. After the freeze, contract changes are additive only (new optional fields), announced in chat, and signed off by P1 and P3.
- **Fixtures first.** UI and API never wait for the engine (mock mode plus golden fixtures), and the engine never waits for the UI.
- **Tests first.** Every session starts from failing acceptance tests for its requirement IDs.
- **Adversarial cross-review.** Before merging a major module, a different lane's Claude gets: "Construct an input that breaks invariant I2 / I5 / I6." The validator author (P2) attacks the solver (P1).
- **Small PRs, trunk-based.** Merge at least hourly. `make check` (ruff, pytest, tsc, build) must be green and main must always run. Use one clone or worktree per session.
- **Fresh session per task (≤ 60 min).** Paste failing output instead of describing it. For the solver and replanner, make Claude state its approach first and have the lane owner approve it in two minutes.
- **Pace usage.** Account limits are real, so keep prompts focused and stagger heavy generation. If one account runs dry, the lane's tests and docs let a teammate take over.
- **Sync.** Hold a 5-minute stand-up each hour (done / next / blocked), with hard gates at 3:00, 5:30, 7:30 and 9:00.

### Kickoff prompt (same for everyone; swap the last line)

```
Read CLAUDE.md, docs/ASSUMPTIONS.md and docs/REQUIREMENTS.md. You are building lane <X> of ReRoute and may only edit <your directories>. Code against contract/ models and fixtures; don't change them (propose changes in docs/CONTRACT_CHANGES.md). Work test-first against the acceptance tests for <R-ids>. Keep functions pure and deterministic. When done, run `make check` and report: what's done, assumptions you made, open questions.
Task: <P1: simulate_route… | P2: validator + snapshot… | P3: API + resolver… | P4: Gantt from fixtures…>
```

If you have access to Claude Code, run each person's session in it, inside their own clone, so Claude can edit its lane and run `make check` itself.

---

## 7. Proof and demo

Every spec line needs something you can point at on stage:

| Spec line | Mechanism | Proof on stage |
|-----------|-----------|----------------|
| Matrix-only inputs, explainable algorithm, limits, arrivals + waits | One simulator; regret insertion + ruin-and-recreate; schematic map only | Gantt with hatched waits; Method & Limits page |
| Never overload at any point; unplaceable → reason | Load checked at the start and after every pickup; per-vehicle diagnostics | Load-vs-capacity line under each route; unplaced list with reasons; fuzz result |
| Three disruptions, structured or text | Disruption union + one `replan()` | Live demo of each, in both input modes |
| Confirm before effect; unknown location rejected | Propose → preview → confirm; exact-match resolver | Server returns 409 without confirm and 422 on an unknown place; a judge types a hostile report |
| Replan from current state; nothing after failure | `snapshot(now)` + freeze rule | I5/I6 invariants; Verify panel |
| Side-by-side, kept/moved/broken with reason | Reason ledger → diff | Compare view; every row carries a cause code and a sentence |

### Five-minute demo

| Time | Step |
|------|------|
| 0:30 | Morning plan: arrivals with hatched waits, load line under each route, two unplaced deliveries with reasons. |
| 1:00 | Closure via form → preview → apply → side-by-side with kept/moved/broken and reasons. |
| 1:00 | Vehicle failure by text: highlighted interpretation, assumptions, confirm card. The rescue pickup appears and completed stops are unchanged. |
| 0:30 | A hostile report naming an unknown place is rejected and nothing changes. |
| 0:45 | Urgent delivery placed; the load line never crosses capacity. |
| 0:45 | Verify panel (all green), fuzz and optimality-gap numbers, Method & Limits. |
| 0:30 | Hand the keyboard to a judge: "type any report." |

### One-line answers for the four predictable challenges

- **Is it optimal?** No; we measured the gap, and in return it is explainable.
- **How do you know it never overloads?** An independent validator gate plus fuzzing.
- **What about vague reports?** The confirm gate shows defaults, and unknowns are rejected.
- **What happens to cargo on a failed vehicle?** D3, and it's configurable.

---

## 8. Risks and cut-lines

- **G1 slips by more than 30 minutes:** drop ruin-and-recreate and the map; keep insertion + Gantt.
- **G2 slips:** do text input for closure and failure first, and urgent via the form only.
- **Never cut:** the validator gate, the confirm gate with unknown-location rejection, reasons on every diff row, the side-by-side view, and Method & Limits.
- **Cut first (★):** LLM extractor, OR-Tools benchmark, CSV import, animations, customer messages.
- **Demo insurance:** offline build, backup video, pre-seeded state, and a second laptop with a clean clone.
- **Fatigue:** it causes the worst bugs between hours 7 and 9, so the break at G2 and the 9:00 freeze are not optional.
