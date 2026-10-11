# ASSUMPTIONS (D1-D10)

Locked in the first 20 minutes. Do not re-debate. If an organizer answer contradicts D2, D3 or D9, change **that one** assumption; the architecture does not move.

| # | Decision |
|---|----------|
| D1 | Time is integer minutes since midnight; the matrix is in minutes (round fractions up). |
| D2 | A window constrains service start. Early arrival waits: `start = max(arrival, open)`, `depart = start + service time`. Wait is always shown. |
| D3 | Cargo model: every parcel is on board or needs a pickup stop. Morning plan: all loaded at the depot. Urgent: picked up at the depot, released at report time. Failed vehicle: undelivered parcels are picked up at its last known stop (or depot) after the failure plus a transfer time (config flag). Load is checked at the start and after every pickup. |
| D4 | Closure raises that edge's time (+N min, new value, or xk; both directions unless stated) for departures in `[max(start, now), end)`. Matrix entries are direct times; no automatic detours. |
| D5 | Freeze: a stop is fixed if its service ended <= now, is in progress, or the vehicle is already driving to it. A failed vehicle keeps only stops finished by its failure time. |
| D6 | Objective, in order: fewest priority-weighted broken -> fewest moved/shifted -> least travel + wait. Urgent priority = 2. |
| D7 | kept = same vehicle, ETA within +-5 min; moved = other vehicle or larger ETA/sequence change, still in window; broken = cannot be placed in its window. A new urgent delivery is moved (placed) or broken (not placed) and always badged NEW. |
| D8 | Text: interpret -> preview -> confirm. Unknown or ambiguous location/vehicle rejects the whole report; no fuzzy matching. Missing optional fields get visible, editable defaults. |
| D9 | Windows are hard. For a broken delivery show the earliest feasible ETA as a negotiation hint, never silently serve it late. |
| D10 | Deterministic: seeded RNG, iteration budgets instead of wall-clock, ties broken by ID. |

## Questions for the organizers (first 15 minutes)

- Is there a sample dataset or file format?
- Are windows hard?
- Can a failed vehicle's parcels be transferred (where and when)?
- Must vehicles return to the depot, or is there a shift end?
