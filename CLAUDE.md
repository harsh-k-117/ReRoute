# CLAUDE.md: ReRoute

Read this first. Claude Code picks it up automatically; in chat, paste it as your first message.

## Brief
Disruption-aware vehicle routing. Build an initial plan from a time matrix, then replan after **road closure**, **vehicle failure** or **urgent delivery**, entered by form or free text. The dispatcher stays in control: propose -> preview -> confirm. The engine never emits an invalid plan and shows proof.

## Read before coding
- `docs/ASSUMPTIONS.md`: D1-D10 (locked; do not re-debate)
- `docs/REQUIREMENTS.md`: R1-R15 -> module -> test -> demo step
- `docs/TECH_STACK.md`: the stack below, with reasons
- `docs/CONTRACT_CHANGES.md`: how to ask for a contract change

## Tech stack (use exactly this)
- **Backend/engine:** Python 3.12, FastAPI, Pydantic v2, uv. Pure, deterministic functions (seeded RNG, iteration budgets, ties by ID).
- **Solver:** custom regret-2 insertion + ruin-and-recreate. OR-Tools **only** in `engine/benchmarks/`.
- **Verification:** pytest, Hypothesis, ruff. The validator in `verify/` must NOT import the engine's simulator.
- **Text input:** rule-based parser + exact-match resolver. Optional LLM extractor (Anthropic API, JSON out) behind `REROUTE_LLM_EXTRACTOR=1`, with timeout + fallback.
- **Frontend:** Vite, React, TypeScript, Tailwind, shadcn/ui, TanStack Query, Zustand, custom SVG + d3-scale, openapi-typescript, Playwright.
- **Map:** schematic SVG only (x/y or MDS from the matrix).

## Lanes (single writer per directory)
| Lane | Owns |
|------|------|
| P1 Algorithm | `engine/`, `contract/` (author), `tests/unit/engine/` |
| P2 Replan & quality | `replan/`, `verify/`, `diff/`, `tests/acceptance/`, `tests/property/`, `tests/edge/` |
| P3 Integration & language | `api/`, `nlp/`, `data/`, `scripts/`, `frontend/src/features/disruptions/` |
| P4 UX & story | rest of `frontend/`, `docs/pitch/` |

`contract/` is shared and frozen at 1:00 (tag `contract-v1`). After that: additive only, via `docs/CONTRACT_CHANGES.md`, signed off by P1 and P3.

## Commands
`make install` · `make dev` · `make check` (ruff, pytest, tsc, build) · `make fuzz` · `make types` · `make demo`

## Definition of done
- Acceptance tests for your R-ids pass; `make check` is green; `main` always runs.
- No invariant I1-I12 regression; validator gate still blocks bad plans.
- Small PR, merged within the hour.

## Don'ts
- No map libraries. No CDNs. No network calls except the flagged LLM extractor.
- No edits outside your lane. Cross-lane needs -> `docs/CONTRACT_CHANGES.md` or a PR comment.
- No fuzzy matching of locations or vehicles. Unknown/ambiguous -> reject the whole report.
- No wall-clock budgets in the solver.
