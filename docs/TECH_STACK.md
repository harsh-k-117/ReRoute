# Tech stack

| Layer | Pick | Why |
|-------|------|-----|
| Engine + API | Python 3.12, FastAPI, Pydantic v2, uv | Fast to write and test algorithms. Pydantic models are the contract: OpenAPI -> TypeScript types, so UI and API cannot drift. |
| Solver | Custom pure Python: regret-2 insertion + ruin-and-recreate | Explainable in a minute; handles time-dependent closures, frozen prefixes and pickups natively; no solver dependency to break on the day. |
| Oracles | Brute-force enumeration on tiny instances; OR-Tools only in benchmarks (star) | Lets us quote an optimality gap. |
| Verification | pytest, Hypothesis, ruff | Property-based fuzzing of invariants is the strongest credibility signal. |
| Text input | Rule-based parser + exact-match resolver (primary). Optional LLM extractor (Anthropic API, JSON output) behind a flag, with timeout + fallback (star) | Primary path is offline and deterministic. The LLM only extracts mentions as written and never sees the location list. |
| Frontend | Vite, React, TypeScript, Tailwind, shadcn/ui, TanStack Query, Zustand, custom SVG + d3-scale, openapi-typescript | Polished, interactive UI quickly; hand-rolled SVG gives full control of Gantt, load profile, diff ghosts. |
| Map | No tile map. Schematic SVG from x/y if supplied, else MDS layout from the time matrix | No network dependency. |
| Packaging | `make dev` / `check` / `demo`; FastAPI serves the built UI | One offline command. Local fonts, no CDNs. |
| Collaboration | Private GitHub repo, trunk-based, `CLAUDE.md`, `make check` as merge gate | The repo is the only shared memory across four Claude accounts. |

## Where each piece lives

| Piece | Directory | Lane |
|-------|-----------|------|
| Pydantic contract + fixtures | `contract/` | P1 (shared, frozen 1:00) |
| Simulator + solver | `engine/` | P1 |
| Replan, validator, diff, acceptance tests, fuzzers | `replan/`, `verify/`, `diff/`, `tests/` | P2 |
| API, text interpreter, scenarios, CLI | `api/`, `nlp/`, `data/`, `scripts/` | P3 |
| UI (disruption console = P3) | `frontend/` | P4 |
| Pitch, demo script | `docs/pitch/` | P4 |
