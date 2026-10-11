# ReRoute

ReRoute is an explainable delivery-planning engine for dynamic fleet replanning. It creates an initial plan from a depot, vehicles, deliveries, hard time windows, service times, and a simulated travel-time matrix, then replans after closures, vehicle failures, and urgent deliveries.

The project deliberately uses matrix travel times only: it does not call live mapping, GPS, or tile services. Every revised plan is independently validated before it is presented, and changes are classified as kept, moved, or broken with a reason.

## Quick start

Requirements: Python 3.12 and `uv`. Node LTS and pnpm are needed for the frontend checks.

```sh
uv sync
make check
make dev
```

`make demo` is reserved for the complete demo flow and currently prints `not built yet`.

See [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) for the requirements derived from the supplied challenge statement and [CLAUDE.md](CLAUDE.md) for project conventions.