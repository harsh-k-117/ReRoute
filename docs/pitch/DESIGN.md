# ReRoute Phase 12 design

## Direction

Light, calm, high-contrast operations dashboard. The interface is deliberately
quiet so route geometry and timing carry the visual weight.

## Palette

- Canvas: `#f5f7f5`
- Surface: `#ffffff`
- Ink: `#1d2923`
- Muted text: `#66736b`
- Border: `#dfe7e1`
- Accent: `#315f9f` (actions and focus only)
- Vehicle route colors: blue, violet, teal, and slate
- Classification colors only: kept (green), moved (amber), broken (red)
- Assumption and error tokens are reserved for later disruption UI.

No external fonts or network-dependent visual resources are used. The map uses
the checked-in OSM-derived Pune road GeoJSON and coordinate manifest under
`frontend/public/`, with attribution in `frontend/public/pune-map-attribution.txt`.
This geometry is display-only; planning continues to use the deterministic
travel-time matrix and does not claim live GPS tracking.

## Typography and spacing

System sans-serif stack with tabular numerals for time and KPI values. The
spacing unit is 4px; panels use 16px padding, 12px gaps, and 10px radii.
Focus rings are always visible for keyboard users.

## Layout sketch

```text
┌─────────────────────────────────────────────────────────────────────┐
│ ReRoute · Scenario picker · MOCK/REAL · now                         │
├───────────────┬─────────────────────────────────────────────────────┤
│ scenario      │ KPI bar: planned · vehicles · travel · wait         │
│ navigation    ├───────────────────────────────┬─────────────────────┤
│               │ vehicle Gantt + load profiles  │ offline road map    │
│               ├───────────────────────────────┴─────────────────────┤
│               │ sortable stop table                                  │
│               ├───────────────────────────────┬─────────────────────┤
│               │ unplaced deliveries/reasons  │ plan notes            │
└───────────────┴───────────────────────────────┴─────────────────────┘
```

The layout collapses to one column below 1100px and remains usable at a
1280px laptop width.