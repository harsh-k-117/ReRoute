# Requirements

The following requirements are derived only from the supplied [SPEC.md](SPEC.md).

| Requirement | Module(s) | Acceptance test file | Demo step |
|---|---|---|---|
| R1. Assign deliveries to vehicles and order their stops. | `engine/construct.py` | `tests/acceptance/test_r01_initial_plan.py` | Create the morning plan |
| R2. Respect vehicle capacities. | `engine/construct.py`, `engine/simulate.py` | `tests/acceptance/test_r03_never_overload.py` | Show route load |
| R3. Respect delivery sizes. | `contract/`, `engine/construct.py` | `tests/acceptance/test_r01_initial_plan.py` | Create the morning plan |
| R4. Respect hard delivery time windows. | `engine/simulate.py` | `tests/acceptance/test_r02_arrivals_and_waits.py` | Inspect stop timings |
| R5. Use the supplied simulated travel-time matrix, without live mapping or GPS. | `engine/travel.py` | `tests/edge/test_closure_edges.py` | Explain matrix travel |
| R6. Use an explainable routing or allocation algorithm and state its limits. | `engine/`, `docs/ASSUMPTIONS.md` | `tests/unit/engine/test_construct.py` | Open Method & Limits |
| R7. Show arrival times and waiting before a window opens. | `engine/simulate.py`, `frontend/src/features/gantt/` | `tests/acceptance/test_r02_arrivals_and_waits.py` | Show the timeline |
| R8. Report an unplaceable delivery with its reason. | `engine/diagnose.py`, `contract/` | `tests/acceptance/test_r04_unplaced_reasons.py` | Inspect unplaced deliveries |
| R9. Support road-closure disruptions with a stated period and increased edge travel time. | `replan/closure.py` | `tests/acceptance/test_r05_closure.py` | Apply a road closure |
| R10. Support vehicle failures at a stated time. | `replan/failure.py` | `tests/acceptance/test_r06_vehicle_failure.py` | Fail a vehicle |
| R11. Support urgent deliveries added during the day. | `replan/urgent.py` | `tests/acceptance/test_r07_urgent_delivery.py` | Add an urgent delivery |
| R12. Accept structured disruptions or text descriptions. | `api/`, `nlp/` | `tests/acceptance/test_r08_text_interpretation.py` | Enter a disruption |
| R13. Require dispatcher confirmation before interpreted text changes take effect. | `nlp/`, `api/routes/proposals.py` | `tests/acceptance/test_r09_confirm_gate.py` | Confirm the proposal |
| R14. Reject unknown locations rather than guessing. | `nlp/resolver.py`, `api/` | `tests/acceptance/test_r10_unknown_location_rejected.py` | Submit an unknown location |
| R15. Replan from current state, preserve completed stops, exclude failed-vehicle future stops, and show side-by-side kept/moved/broken results with reasons. | `replan/`, `diff/`, `frontend/src/features/compare/` | `tests/acceptance/test_r11_replan_from_current_state.py`, `tests/acceptance/test_r12_failed_vehicle_no_stops.py`, `tests/acceptance/test_r13_side_by_side_diff.py`, `tests/acceptance/test_r14_kept_moved_broken.py`, `tests/acceptance/test_r15_reasons_on_every_row.py` | Compare original and revised plans |