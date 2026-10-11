# ReRoute

Disruption-aware vehicle routing with a validator gate, reason-carrying diffs and a propose -> preview -> confirm dispatcher flow.

**Stack:** Python 3.12 · FastAPI · Pydantic v2 · uv (backend) / Vite · React · TypeScript · Tailwind · shadcn/ui · TanStack Query · Zustand · SVG + d3-scale (frontend)

## Quick start
```bash
make install
make dev      # API (mock mode) + UI dev server
make check    # merge gate: ruff, pytest, tsc, build
make demo     # one-command OFFLINE demo
```

## Docs
- [`CLAUDE.md`](CLAUDE.md): read first (every session)
- [`docs/ASSUMPTIONS.md`](docs/ASSUMPTIONS.md): D1-D10
- [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md): R1-R15
- [`docs/TECH_STACK.md`](docs/TECH_STACK.md): stack and where it lives
- [`docs/FILE_STRUCTURE.md`](docs/FILE_STRUCTURE.md): annotated file tree
