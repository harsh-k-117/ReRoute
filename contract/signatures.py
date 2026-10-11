"""contract/signatures.py - stub signatures so every lane can import from minute one

Lane : P1 Algorithm lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 (models ARE the contract: -> OpenAPI -> TypeScript via openapi-typescript) · JSON fixtures
Spec : contract-v1
"""
from __future__ import annotations

from collections.abc import Callable, Sequence

from contract.models import (
    Diff, Disruption, Plan, PlanState, Proposal, ReplanResult, Route, RouteSim,
    Scenario, ValidationReport,
)

TravelFn = Callable[[str, str, int], int]  # (from, to, depart_time) -> minutes (D4)

# engine/ (P1)
SimulateRoute = Callable[..., RouteSim]
BuildPlan = Callable[..., Plan]
InsertDeliveries = Callable[..., Plan]
Improve = Callable[..., Plan]
DiagnoseUnplaced = Callable[..., Plan]

# replan/ (P2)
Snapshot = Callable[..., PlanState]
Replan = Callable[..., ReplanResult]

# verify/ + diff/ (P2)
Validate = Callable[..., ValidationReport]
Classify = Callable[..., Diff]

# nlp/ (P3)
Interpret = Callable[..., Proposal]
