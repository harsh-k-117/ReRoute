"""contract/models.py - Pydantic v2 models = the single contract (DRAFT until contract-v1)

Lane : P1 Algorithm lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 (models ARE the contract: -> OpenAPI -> TypeScript via openapi-typescript) · JSON fixtures
Spec : D1-D10, I1-I12
"""
from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

# D1: time is integer minutes since midnight everywhere in this file.
Minutes = int


class _Model(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


# ---- Scenario --------------------------------------------------------------
class Vehicle(_Model):
    id: str
    capacity: int
    start_location: str  # the depot unless the scenario says otherwise
    shift_end: Minutes | None = None


class Delivery(_Model):
    id: str
    location: str
    demand: int
    window_open: Minutes
    window_close: Minutes  # D2/D9: hard window on service START
    service_time: Minutes
    priority: int = 1  # D6: urgent = 2
    release_time: Minutes = 0  # urgent: report time (D3)
    pickup_location: str | None = None  # D3: None = loaded at depot in the morning plan


class Config(_Model):
    transfer_minutes: Minutes = 0  # D3 flag: failed-vehicle parcel transfer time
    return_to_depot: bool = False
    seed: int = 0  # D10
    iterations: int = 200  # D10: iteration budget, not wall-clock


class Scenario(_Model):
    name: str
    depot: str
    locations: list[str]
    aliases: dict[str, list[str]] = Field(default_factory=dict)  # exact-match resolver (D8)
    coords: dict[str, tuple[float, float]] | None = None  # schematic map; else MDS from matrix
    matrix: list[list[Minutes]]  # direct times in minutes, rounded up (D1/D4)
    vehicles: list[Vehicle]
    deliveries: list[Delivery]
    config: Config = Field(default_factory=Config)


# ---- Plan ------------------------------------------------------------------
class Stop(_Model):
    kind: Literal["pickup", "delivery"]
    delivery_id: str
    location: str
    arrival: Minutes
    wait: Minutes  # D2: always shown
    start: Minutes
    depart: Minutes
    load_after: int  # I2: checked at start and after every pickup


class Route(_Model):
    vehicle_id: str
    stops: list[Stop]


class Unplaced(_Model):
    delivery_id: str
    reason_codes: list[str]  # oversize | window_unreachable | no_capacity_at_stop_k | pushes_stop_x_late | no_vehicle_available | no_feasible_slot
    per_vehicle: dict[str, str] = Field(default_factory=dict)  # binding constraint per vehicle
    earliest_feasible_eta: Minutes | None = None  # D9 negotiation hint (star)


class Plan(_Model):
    scenario: str
    routes: list[Route]
    unplaced: list[Unplaced]


class Violation(_Model):
    stop_index: int
    code: str
    detail: str


class RouteSim(_Model):
    route: Route
    violations: list[Violation]


# ---- Replan state ----------------------------------------------------------
class VehicleState(_Model):
    vehicle_id: str
    ready_location: str
    ready_time: Minutes
    on_board_load: int
    frozen_stops: list[Stop]  # D5
    available: bool = True
    breakdown_site: str | None = None


class PlanState(_Model):
    now: Minutes
    vehicles: list[VehicleState]
    pool: list[str]  # delivery ids to (re)insert


# ---- Disruptions (union) ---------------------------------------------------
class RoadClosure(_Model):
    type: Literal["road_closure"] = "road_closure"
    from_location: str
    to_location: str
    start: Minutes
    end: Minutes
    mode: Literal["add", "set", "multiply"] = "add"  # D4
    value: float
    both_directions: bool = True


class VehicleFailure(_Model):
    type: Literal["vehicle_failure"] = "vehicle_failure"
    vehicle_id: str
    at: Minutes


class UrgentDelivery(_Model):
    type: Literal["urgent_delivery"] = "urgent_delivery"
    delivery: Delivery
    reported_at: Minutes


Disruption = Annotated[Union[RoadClosure, VehicleFailure, UrgentDelivery], Field(discriminator="type")]


# ---- Text -> proposal -> confirm (D8, I9, I10) -----------------------------
class SourceSpan(_Model):
    field: str
    start: int
    end: int


class Proposal(_Model):
    id: str
    status: Literal["pending", "confirmed", "discarded", "rejected"]
    disruption: Disruption | None = None
    spans: list[SourceSpan] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)  # amber
    warnings: list[str] = Field(default_factory=list)
    rejections: list[str] = Field(default_factory=list)  # red; any rejection rejects the whole report
    impact_preview: dict[str, int] = Field(default_factory=dict)


# ---- Diff / reasons (D7, I8) ----------------------------------------------
CauseCode = Literal[
    "completed", "vehicle_failed", "closure_delay", "displaced_by_urgent", "knock_on", "no_feasible_slot"
]


class DiffRow(_Model):
    delivery_id: str
    klass: Literal["kept", "moved", "broken"]
    new: bool = False  # NEW badge for urgent deliveries
    cause: CauseCode | None = None
    sentence: str = ""
    old_vehicle: str | None = None
    new_vehicle: str | None = None
    old_eta: Minutes | None = None
    new_eta: Minutes | None = None


class Diff(_Model):
    rows: list[DiffRow]


class ReplanResult(_Model):
    version: int
    plan: Plan
    diff: Diff
    validation: "ValidationReport"


# ---- Validation ------------------------------------------------------------
class InvariantResult(_Model):
    id: Literal["I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9", "I10", "I11", "I12"]
    ok: bool
    detail: str = ""


class ValidationReport(_Model):
    ok: bool
    results: list[InvariantResult]


ReplanResult.model_rebuild()
