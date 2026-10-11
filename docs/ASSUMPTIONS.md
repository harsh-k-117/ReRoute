# Assumptions and invariants

These decisions are fixed unless an explicit contract change is recorded.

| ID | Decision |
|---|---|
| D1 | Time is integer minutes since midnight; the matrix is in minutes and fractions round up. |
| D2 | A window constrains service start. Early arrival waits: `start = max(arrival, open)`, `depart = start + service time`; wait is always shown. |
| D3 | Parcels are either on board or need a pickup stop. Morning parcels load at the depot. Urgent parcels are picked up at the depot and released at report time. Failed-vehicle undelivered parcels are picked up at the last known stop or depot after failure plus a configurable transfer time, defaulting to 10 minutes. Load is checked at the start and after every pickup. |
| D4 | A closure changes one edge's time for departures in `[max(start, now), end)`, in both directions unless stated. Matrix entries are direct times; no automatic detours are added. |
| D5 | A stop is frozen if service ended by `now`, is in progress, or the vehicle is already driving to it. A failed vehicle keeps only stops finished by failure time. |
| D6 | The lexicographic objective is fewest priority-weighted broken, then fewest moved/shifted, then least travel plus wait. Urgent priority is 2. |
| D7 | Kept means same vehicle and ETA within +/-5 minutes; moved means another vehicle or a larger ETA/sequence change while still in-window; broken means it cannot be placed in its window. New urgent deliveries are moved when placed and broken otherwise, and are badged NEW. |
| D8 | Text flow is interpret, preview, confirm. Unknown or ambiguous locations/vehicles reject the whole report; no fuzzy matching. Missing optional fields receive visible, editable defaults. |
| D9 | Windows are hard. Broken deliveries show the earliest feasible ETA as a negotiation hint and are never silently served late. |
| D10 | Results are deterministic: seeded randomness, iteration budgets rather than wall-clock limits, and ID tie-breakers. |

| ID | Invariant |
|---|---|
| I1 | Every delivery appears exactly once, placed or unplaced with a reason. |
| I2 | Load never exceeds capacity at the start or after any pickup. |
| I3 | Service starts inside its window and wait is `max(0, open - arrival)`. |
| I4 | Travel times equal the matrix plus the closure rule. |
| I5 | Nothing remains on a failed vehicle after its failure time. |
| I6 | Frozen stops are byte-identical. |
| I7 | A pickup precedes its delivery on the same vehicle. |
| I8 | Every moved or broken row has a cause. |
| I9 | An unknown location is rejected and state is unchanged. |
| I10 | Text disruptions cannot apply without confirmation. |
| I11 | Equal input and seed produce equal output. |
| I12 | A no-op replan changes nothing. |

## Stated limits

The solver is heuristic and has no general optimality guarantee; the gap is measured on small instances. The model supports one depot, one capacity dimension, no split parcels, direct-edge closure timing with no mid-edge rerouting, vehicles committed to their next stop while in transit, hard windows, and a target scale of 200 deliveries and 15 vehicles.