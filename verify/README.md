# Independent validator notes

The validator is intentionally separate from the solver: it recomputes route timing, load, and closure arithmetic from the scenario matrix instead of reusing the engine. The aim is to catch bugs that a shared simulator would miss.

## Five sneaky failure modes we try to guard against

1. Load check only at the route start. A vehicle can look safe at departure but become overloaded after a pickup later on the route.
2. Waiting computed from the departure time instead of the arrival time. Early arrivals are allowed to wait, but the wait should be `max(0, open - arrival)`.
3. Time-dependent closure applied on arrival instead of departure. A route is only delayed when the vehicle departs during the closure window.
4. Frozen stops compared by vehicle and position but not by exact bytes. A frozen stop can appear fixed while silently changing its service start or load value.
5. Pickup/delivery ordering checked only by counting stops, not by sequence. A pickup after a delivery is logically invalid even if the total delivery count is correct.

This review is intentionally adversarial: if a solver and the validator share the same arithmetic bug, the check will fail to catch it. The P2 lane therefore reimplements the rules directly from the contract and the matrix.
