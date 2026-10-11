# File structure

The repository is organized by delivery-planning responsibility:

```text
api/       FastAPI application, routes, store, and mock mode
contract/  Shared models, signatures, and fixtures
data/      Scenario generators and importers
diff/      Plan comparison and explanations
docs/      Requirements, fixed assumptions, architecture, and pitch material
engine/    Travel, simulation, construction, improvement, diagnosis, and benchmarks
frontend/  Vite/React user interface
nlp/       Structured text interpretation and entity resolution
replan/    Freeze, disruption application, snapshots, and replanning
scripts/   CLI, demo, fuzz, and generated-type helpers
tests/     Acceptance, edge, property, and unit tests
verify/    Independent invariant checks
```

Lane ownership is documented in [CLAUDE.md](../CLAUDE.md).