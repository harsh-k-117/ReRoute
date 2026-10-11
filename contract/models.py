"""Pydantic contract for ReRoute; times are integer minutes since midnight (D1)."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Location(ContractModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    x: float | None = None
    y: float | None = None


class Vehicle(ContractModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    capacity: NonNegativeInt
    shift_end: NonNegativeInt | None = None
    start_location_id: str


class Delivery(ContractModel):
    id: str
    location_id: str
    demand: NonNegativeInt
    window_open: NonNegativeInt
    window_close: NonNegativeInt
    service_time: NonNegativeInt
    priority: PositiveInt = 1
    release_time: NonNegativeInt | None = None

    @model_validator(mode="after")
    def valid_window(self) -> Delivery:
        if self.window_close < self.window_open:
            raise ValueError("window_close must be greater than or equal to window_open")
        return self


class ScenarioConfig(ContractModel):
    transfer_minutes: NonNegativeInt = 10
    return_to_depot: bool = False


class Scenario(ContractModel):
    name: str
    depot_id: str
    locations: list[Location]
    vehicles: list[Vehicle]
    deliveries: list[Delivery]
    travel_times: list[list[NonNegativeInt]]
    now: NonNegativeInt = 0
    start_time: NonNegativeInt = 0
    config: ScenarioConfig = Field(default_factory=ScenarioConfig)
    seed: int = 0

    @model_validator(mode="after")
    def validate_references_and_matrix(self) -> Scenario:
        location_ids = [location.id for location in self.locations]
        if len(location_ids) != len(set(location_ids)):
            raise ValueError("location ids must be unique")
        known = set(location_ids)
        if self.depot_id not in known:
            raise ValueError("depot_id must identify a location")
        if any(v.start_location_id not in known for v in self.vehicles):
            raise ValueError("every vehicle start_location_id must identify a location")
        if any(d.location_id not in known for d in self.deliveries):
            raise ValueError("every delivery location_id must identify a location")
        size = len(self.locations)
        if len(self.travel_times) != size or any(len(row) != size for row in self.travel_times):
            raise ValueError("travel_times must be a square matrix indexed by locations order")
        return self


class ReasonCode(StrEnum):
    OVERSIZE = "oversize"
    WINDOW_UNREACHABLE = "window_unreachable"
    NO_CAPACITY_AT_STOP = "no_capacity_at_stop"
    PUSHES_STOP_LATE = "pushes_stop_late"
    NO_VEHICLE_AVAILABLE = "no_vehicle_available"
    NO_FEASIBLE_SLOT = "no_feasible_slot"
    UNKNOWN_LOCATION = "unknown_location"
    OTHER = "other"


class Reason(ContractModel):
    code: ReasonCode
    vehicle_id: str | None = None
    detail: str


class Unplaced(ContractModel):
    delivery_id: str
    reasons: list[Reason]
    earliest_feasible_eta: NonNegativeInt | None = None


class StopKind(StrEnum):
    DEPOT_START = "depot_start"
    PICKUP = "pickup"
    DELIVERY = "delivery"
    DEPOT_END = "depot_end"


class Stop(ContractModel):
    kind: StopKind
    delivery_id: str | None = None
    parcel_ids: list[str] = Field(default_factory=list)
    location_id: str
    arrival: NonNegativeInt
    wait: NonNegativeInt = 0
    service_start: NonNegativeInt
    depart: NonNegativeInt
    load_after: NonNegativeInt
    window_open: NonNegativeInt | None = None
    window_close: NonNegativeInt | None = None
    frozen: bool = False
    badges: list[str] = Field(default_factory=list)


class Route(ContractModel):
    vehicle_id: str
    stops: list[Stop]
    total_travel: NonNegativeInt = 0
    total_wait: NonNegativeInt = 0
    failed_at: NonNegativeInt | None = None
    violations: list[str] = Field(default_factory=list)


class Plan(ContractModel):
    version_id: str
    scenario_ref: str
    routes: list[Route]
    unplaced: list[Unplaced] = Field(default_factory=list)
    created_from: str | None = None
    seed: int = 0


class VehicleReadyState(ContractModel):
    vehicle_id: str
    frozen_stops: list[Stop]
    ready_location_id: str
    ready_time: NonNegativeInt
    onboard_load: NonNegativeInt
    failed_at: NonNegativeInt | None = None


class PlanSnapshot(ContractModel):
    plan_ref: str
    now: NonNegativeInt
    vehicles: list[VehicleReadyState]


class RoadClosure(ContractModel):
    type: Literal["road_closure"]
    a: str
    b: str
    mode: Literal["add_minutes", "set_minutes", "multiply"]
    value: float
    both_directions: bool = True
    start: NonNegativeInt
    end: NonNegativeInt

    @model_validator(mode="after")
    def valid_period_and_value(self) -> RoadClosure:
        if self.end <= self.start:
            raise ValueError("closure end must be after start")
        if self.value < 0 or (self.mode == "multiply" and self.value < 1):
            raise ValueError("closure value must be non-negative (and >= 1 for multiply)")
        return self


class VehicleFailure(ContractModel):
    type: Literal["vehicle_failure"]
    vehicle_id: str
    at_time: NonNegativeInt
    transfer_minutes: NonNegativeInt | None = None


class UrgentDelivery(ContractModel):
    type: Literal["urgent_delivery"]
    delivery: Delivery
    report_time: NonNegativeInt
    priority: PositiveInt = 2


Disruption = Annotated[
    RoadClosure | VehicleFailure | UrgentDelivery,
    Field(discriminator="type"),
]


class SourceSpan(ContractModel):
    field: str
    start: NonNegativeInt
    end: NonNegativeInt

    @model_validator(mode="after")
    def valid_span(self) -> SourceSpan:
        if self.end < self.start:
            raise ValueError("span end must not precede start")
        return self


class ProposalStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISCARDED = "discarded"


class Proposal(ContractModel):
    id: str
    source: Literal["form", "text"]
    original_text: str | None = None
    disruption: Disruption
    spans: list[SourceSpan] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    rejections: list[str] = Field(default_factory=list)
    status: ProposalStatus = ProposalStatus.PENDING
    impact_preview: ReplanResult | None = None  # resolved after ReplanResult is defined below


class Classification(StrEnum):
    KEPT = "kept"
    MOVED = "moved"
    BROKEN = "broken"


class DiffRow(ContractModel):
    delivery_id: str
    classification: Classification
    cause_code: str
    sentence: str
    before_vehicle_id: str | None = None
    after_vehicle_id: str | None = None
    before_eta: NonNegativeInt | None = None
    after_eta: NonNegativeInt | None = None
    badge: str | None = None
    earliest_feasible_eta: NonNegativeInt | None = None


class Diff(ContractModel):
    rows: list[DiffRow]
    kept_count: NonNegativeInt = 0
    moved_count: NonNegativeInt = 0
    broken_count: NonNegativeInt = 0


class LedgerAction(StrEnum):
    EJECT = "eject"
    INSERT = "insert"
    MOVE = "move"
    COMPLETE = "complete"


class LedgerCause(StrEnum):
    COMPLETED = "completed"
    VEHICLE_FAILED = "vehicle_failed"
    CLOSURE_DELAY = "closure_delay"
    DISPLACED_BY_URGENT = "displaced_by_urgent"
    KNOCK_ON = "knock_on"
    NO_FEASIBLE_SLOT = "no_feasible_slot"


class LedgerEntry(ContractModel):
    delivery_id: str
    action: LedgerAction
    cause_code: LedgerCause
    detail: str


class InvariantResult(ContractModel):
    id: Literal["I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9", "I10", "I11", "I12"]
    passed: bool
    details: str


class ValidationReport(ContractModel):
    checks: list[InvariantResult]
    passed: bool


class KpiSummary(ContractModel):
    kept_count: NonNegativeInt = 0
    moved_count: NonNegativeInt = 0
    broken_count: NonNegativeInt = 0
    total_travel: NonNegativeInt = 0
    total_wait: NonNegativeInt = 0


class ReplanResult(ContractModel):
    plan: Plan
    previous_plan_ref: str
    diff: Diff
    validation_report: ValidationReport
    ledger_entries: list[LedgerEntry] = Field(default_factory=list)
    trace: list[str] | None = None


Proposal.model_rebuild()

__all__ = [
    "Classification",
    "Delivery",
    "Diff",
    "DiffRow",
    "Disruption",
    "InvariantResult",
    "KpiSummary",
    "LedgerAction",
    "LedgerCause",
    "LedgerEntry",
    "Location",
    "Plan",
    "PlanSnapshot",
    "Proposal",
    "ProposalStatus",
    "Reason",
    "ReasonCode",
    "ReplanResult",
    "RoadClosure",
    "Route",
    "Scenario",
    "ScenarioConfig",
    "SourceSpan",
    "Stop",
    "StopKind",
    "Unplaced",
    "UrgentDelivery",
    "ValidationReport",
    "Vehicle",
    "VehicleFailure",
    "VehicleReadyState",
]
