"""Upload routes for scenarios (Mode A) and pre-built schedules (Mode B).

Two-phase pattern (preview / confirm) mirrors the disruption proposal flow:
  POST /scenarios/upload/preview  -> UploadPreview  (stores nothing)
  POST /scenarios/upload/confirm  -> InitialPlanResponse (commits to session)

  POST /plan/import/preview       -> ImportPreview  (stores nothing)
  POST /plan/import/confirm       -> ImportResult   (commits to session)

  GET  /templates/{kind}          -> CSV / JSON template file
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import secrets
import time
import zipfile
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from api.deps import get_store, set_store
from api.mock import fixture
from api.settings import mock_mode
from api.store import SessionStore, available_scenarios, register_uploaded_scenario
from contract.models import (
    Plan,
    Reason,
    ReasonCode,
    Route,
    Scenario,
    Stop,
    StopKind,
    Unplaced,
    ValidationReport,
)
from data.importers import import_scenario_csv, import_scenario_json
from engine.construct import build_plan
from engine.simulate import simulate_route
from verify.validator import validate

router = APIRouter()

# ---------------------------------------------------------------------------
# Size limits
# ---------------------------------------------------------------------------
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_ZIP_UNCOMPRESSED = 20 * 1024 * 1024  # 20 MB
WARN_DELIVERIES = 200
WARN_VEHICLES = 15

# ---------------------------------------------------------------------------
# In-memory preview store (token -> parsed data)
# ---------------------------------------------------------------------------
_PREVIEWS: dict[str, dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

ColumnMapping = dict[str, str]  # detected_col -> canonical_field


class UploadPreview(BaseModel):
    token: str
    format: Literal["json", "csv_bundle", "zip"]
    counts: dict[str, int]
    column_mapping: ColumnMapping = {}
    assumptions: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []


class InitialPlanResponse(BaseModel):
    plan: Plan
    validation_report: ValidationReport
    scenario_name: str
    is_uploaded: bool = True


class ConfirmRequest(BaseModel):
    token: str
    build_plan_flag: bool = True


class ImportPreview(BaseModel):
    token: str
    counts: dict[str, int]
    missing_delivery_ids: list[str] = []
    arrival_warnings: list[str] = []
    errors: list[str] = []


class ImportResult(BaseModel):
    plan: Plan
    validation_report: ValidationReport
    is_valid: bool
    arrival_warnings: list[str] = []
    unplaced: list[str] = []


class ImportConfirmRequest(BaseModel):
    token: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_size(data: bytes, label: str) -> None:
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"{label} exceeds maximum upload size of 5 MB ({len(data)} bytes).",
        )


def _safe_zip_extract(zip_bytes: bytes) -> dict[str, bytes]:
    """Extract a ZIP safely: no path traversal, honour uncompressed size cap."""
    result: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        total_uncompressed = sum(info.file_size for info in zf.infolist())
        if total_uncompressed > MAX_ZIP_UNCOMPRESSED:
            raise ValueError(
                f"ZIP uncompressed content ({total_uncompressed} bytes) "
                f"exceeds the {MAX_ZIP_UNCOMPRESSED // (1024 * 1024)} MB limit."
            )
        for info in zf.infolist():
            name = info.filename
            # Reject any entry with path separators or parent references
            if "/" in name or "\\" in name or ".." in name:
                raise ValueError(
                    f"ZIP entry {name!r} contains path separators or '..' (zip-slip protection)."
                )
            result[name] = zf.read(name)
    return result


def _find_file(files: dict[str, bytes], *keywords: str) -> bytes | None:
    """Return first entry whose lowercase name contains any keyword."""
    for name, data in files.items():
        lower = name.lower()
        for kw in keywords:
            if kw in lower:
                return data
    return None


def _euclidean_matrix(locations: list[dict[str, Any]], speed_kph: float) -> list[list[int]]:
    """Compute travel-time matrix from x/y coords, rounding each value UP (D1)."""
    n = len(locations)
    matrix = [[0] * n for _ in range(n)]
    for i, a in enumerate(locations):
        for j, b in enumerate(locations):
            if i == j:
                continue
            dx = float(a["x"]) - float(b["x"])
            dy = float(a["y"]) - float(b["y"])
            dist_km = math.sqrt(dx * dx + dy * dy)
            matrix[i][j] = math.ceil(dist_km / speed_kph * 60)
    return matrix


# ---------------------------------------------------------------------------
# Preview helpers
# ---------------------------------------------------------------------------

SPEED_FACTOR_KPH = float(os.getenv("REROUTE_XY_SPEED_KPH", "30"))


def _parse_scenario_json(data: bytes) -> tuple[Scenario, list[str], list[str], ColumnMapping]:
    """Return (scenario, assumptions, warnings, column_mapping)."""
    assumptions: list[str] = []
    warnings: list[str] = []

    try:
        raw = json.loads(data.decode("utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError("JSON must contain a top-level object.")

    # Unwrap scenario-pack shape
    payload = raw.get("scenario", raw)

    # Check for xy-only (no matrix)
    locs = payload.get("locations", payload.get("places", payload.get("stops", [])))
    has_matrix = any(
        k in payload for k in ("travel_times", "travel_time_matrix", "time_matrix", "matrix")
    )
    if not has_matrix:
        has_xy = (
            all(
                isinstance(loc, dict) and loc.get("x") is not None and loc.get("y") is not None
                for loc in locs
            )
            if locs
            else False
        )
        if has_xy:
            computed = _euclidean_matrix(locs, SPEED_FACTOR_KPH)
            payload["travel_times"] = computed
            assumptions.append(
                f"Travel-time matrix was computed from x/y coordinates using "
                f"Euclidean distance ÷ {SPEED_FACTOR_KPH} km/h, rounded UP (D1). "
                f"This is an editable assumption."
            )
        else:
            raise ValueError(
                "Neither a travel_times matrix nor x/y coordinates are present. "
                "Cannot infer travel times."
            )

    scenario = import_scenario_json(payload)
    _validate_upload_collections(scenario)

    # Warn on scale
    if len(scenario.deliveries) > WARN_DELIVERIES:
        warnings.append(
            f"Scenario has {len(scenario.deliveries)} deliveries, "
            f"above the tested limit of {WARN_DELIVERIES}."
        )
    if len(scenario.vehicles) > WARN_VEHICLES:
        warnings.append(
            f"Scenario has {len(scenario.vehicles)} vehicles, "
            f"above the tested limit of {WARN_VEHICLES}."
        )

    return scenario, assumptions, warnings, {}


def _parse_scenario_csv(
    files: dict[str, bytes],
) -> tuple[Scenario, list[str], list[str], ColumnMapping]:
    """Attempt to find locations/vehicles/deliveries/matrix CSVs inside a bundle."""
    assumptions: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    locs_data = _find_file(files, "location")
    veh_data = _find_file(files, "vehicle")
    del_data = _find_file(files, "deliver", "order", "job")
    mat_data = _find_file(files, "matrix", "travel", "time")

    # Check for missing required files
    missing = []
    if not locs_data:
        missing.append("locations")
    if not veh_data:
        missing.append("vehicles")
    if not del_data:
        missing.append("deliveries")
    if missing:
        raise ValueError(
            f"Missing required CSV file(s): {', '.join(missing)}. "
            "Expected files containing keywords: locations, vehicles, deliveries, "
            "and optionally matrix/travel."
        )

    # x/y fallback for matrix
    if not mat_data:
        # try to detect x/y in locations CSV
        import csv as _csv

        locs_text = locs_data.decode("utf-8-sig")
        reader = list(_csv.DictReader(io.StringIO(locs_text)))
        has_xy = (
            all(
                row.get("x", row.get("longitude", row.get("east", "")))
                and row.get("y", row.get("latitude", row.get("north", "")))
                for row in reader
            )
            if reader
            else False
        )
        if has_xy:
            loc_list = [
                {
                    "id": row.get("location_id", row.get("id", "")),
                    "x": float(row.get("x", row.get("longitude", row.get("east", 0)))),
                    "y": float(row.get("y", row.get("latitude", row.get("north", 0)))),
                }
                for row in reader
            ]
            mat = _euclidean_matrix(loc_list, SPEED_FACTOR_KPH)
            # Write as CSV matrix
            loc_ids = [item["id"] for item in loc_list]
            buf = io.StringIO()
            w = _csv.writer(buf)
            w.writerow(["location_id"] + loc_ids)
            for i, row_data in enumerate(mat):
                w.writerow([loc_ids[i]] + row_data)
            mat_data = buf.getvalue().encode("utf-8")
            assumptions.append(
                f"Travel-time matrix computed from x/y coordinates using "
                f"Euclidean distance ÷ {SPEED_FACTOR_KPH} km/h, rounded UP (D1). "
                f"Editable assumption."
            )
        else:
            raise ValueError(
                "No matrix CSV found and locations CSV has no x/y coordinates. "
                "Please supply a matrix CSV or add x/y columns."
            )

    if errors:
        raise ValueError("; ".join(errors))

    scenario = import_scenario_csv(
        locs_data,
        veh_data,
        del_data,
        mat_data,
    )
    _validate_upload_collections(scenario)

    if len(scenario.deliveries) > WARN_DELIVERIES:
        warnings.append(
            f"Scenario has {len(scenario.deliveries)} deliveries (tested limit: {WARN_DELIVERIES})."
        )
    if len(scenario.vehicles) > WARN_VEHICLES:
        warnings.append(
            f"Scenario has {len(scenario.vehicles)} vehicles (tested limit: {WARN_VEHICLES})."
        )

    return scenario, assumptions, warnings, {}


def _validate_upload_collections(scenario: Scenario) -> None:
    """Apply upload-specific uniqueness and matrix safety checks."""
    for label, values in (
        ("location", [item.id for item in scenario.locations]),
        ("vehicle", [item.id for item in scenario.vehicles]),
        ("delivery", [item.id for item in scenario.deliveries]),
    ):
        duplicates = sorted({value for value in values if values.count(value) > 1})
        if duplicates:
            raise ValueError(f"duplicate {label} id(s): {', '.join(duplicates)}")
    if any(
        scenario.travel_times[i][j] != scenario.travel_times[j][i]
        for i in range(len(scenario.travel_times))
        for j in range(i + 1, len(scenario.travel_times))
    ):
        raise ValueError("travel times matrix must be symmetric")


# ---------------------------------------------------------------------------
# Mode A: Scenario upload
# ---------------------------------------------------------------------------


@router.post("/scenarios/upload/preview", response_model=UploadPreview)
async def scenario_upload_preview(
    file: UploadFile | None = File(default=None),  # noqa: B008
    files: list[UploadFile] = File(default=[]),  # noqa: B008
) -> UploadPreview:
    """Parse and validate an uploaded scenario; store nothing."""
    if mock_mode():
        return UploadPreview(
            token="mock-preview-token",
            format="json",
            counts={"locations": 6, "vehicles": 3, "deliveries": 8},
            warnings=[],
            errors=[],
        )

    all_files: list[UploadFile] = ([file] if file is not None else []) + files
    if not all_files:
        raise HTTPException(status_code=422, detail="No file uploaded.")

    errors: list[str] = []
    scenario: Scenario | None = None
    assumptions: list[str] = []
    warnings: list[str] = []
    fmt: str = "json"
    column_mapping: ColumnMapping = {}

    try:
        data = await all_files[0].read()
        _check_size(data, all_files[0].filename or "file")
        name = (all_files[0].filename or "").lower()

        if name.endswith(".zip"):
            fmt = "zip"
            file_map = _safe_zip_extract(data)
            scenario, assumptions, warnings, column_mapping = _parse_scenario_csv(file_map)

        elif name.endswith(".json"):
            fmt = "json"
            scenario, assumptions, warnings, column_mapping = _parse_scenario_json(data)

        elif name.endswith(".csv"):
            # Multiple CSV files or single
            if len(all_files) > 1:
                fmt = "csv_bundle"
                file_map = {all_files[0].filename or "": data}
                for uf in all_files[1:]:
                    content = await uf.read()
                    _check_size(content, uf.filename or "")
                    file_map[uf.filename or ""] = content
                scenario, assumptions, warnings, column_mapping = _parse_scenario_csv(file_map)
            else:
                # Single CSV — not a valid scenario alone
                raise ValueError(
                    "A single CSV file is not a complete scenario. "
                    "Upload a JSON file, a ZIP bundle, or all four CSVs at once: "
                    "locations, vehicles, deliveries, and matrix."
                )
        else:
            raise ValueError(
                f"Unsupported file type: {name!r}. Accepted: .json, .csv (bundle of 4), .zip"
            )

    except (ValueError, KeyError) as exc:
        errors.append(str(exc))

    if errors:
        return UploadPreview(
            token="",
            format=fmt,  # type: ignore[arg-type]
            counts={},
            assumptions=assumptions,
            warnings=warnings,
            errors=errors,
        )

    assert scenario is not None
    token = secrets.token_hex(16)
    _PREVIEWS[token] = {"scenario": scenario}

    return UploadPreview(
        token=token,
        format=fmt,  # type: ignore[arg-type]
        counts={
            "locations": len(scenario.locations),
            "vehicles": len(scenario.vehicles),
            "deliveries": len(scenario.deliveries),
        },
        column_mapping=column_mapping,
        assumptions=assumptions,
        warnings=warnings,
        errors=[],
    )


@router.post("/scenarios/upload/confirm", response_model=InitialPlanResponse)
def scenario_upload_confirm(
    request: ConfirmRequest,
    store: SessionStore = Depends(get_store),  # noqa: B008
) -> InitialPlanResponse:
    """Commit a previewed scenario to the session and build the initial plan."""
    if mock_mode():
        plan = Plan.model_validate_json(json.dumps(fixture("plan_initial.json")))
        report = ValidationReport.model_validate_json(
            json.dumps(fixture("validation_report_ok.json"))
        )
        return InitialPlanResponse(
            plan=plan,
            validation_report=report,
            scenario_name="uploaded-mock",
            is_uploaded=True,
        )

    entry = _PREVIEWS.pop(request.token, None)
    if entry is None:
        raise HTTPException(
            status_code=409,
            detail="Preview token not found or already consumed. Call /preview first.",
        )

    scenario: Scenario = entry["scenario"]
    ts = int(time.time())
    # Keep the source name useful while guaranteeing uniqueness across uploads.
    name = f"uploaded-{scenario.name}-{ts}"
    suffix = 2
    while name in {item.name for item in available_scenarios()}:
        name = f"uploaded-{scenario.name}-{ts}-{suffix}"
        suffix += 1
    scenario = scenario.model_copy(update={"name": name})

    try:
        plan = build_plan(scenario)
        report = validate(scenario, plan)
        if not report.passed:
            raise HTTPException(status_code=500, detail=report.model_dump(mode="json"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Replace session store atomically
    new_store = SessionStore(
        scenario=scenario,
        plan=plan,
        versions={plan.version_id: plan},
        proposals={},
    )
    register_uploaded_scenario(scenario)
    set_store(new_store)

    return InitialPlanResponse(
        plan=plan,
        validation_report=report,
        scenario_name=name,
        is_uploaded=True,
    )


# ---------------------------------------------------------------------------
# Mode B: Plan import
# ---------------------------------------------------------------------------

_IMPORT_PREVIEWS: dict[str, dict[str, Any]] = {}


def _schedule_rows_from_json(raw: Any) -> list[dict[str, Any]] | None:
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict) and isinstance(raw.get("stops"), list):
        return [item for item in raw["stops"] if isinstance(item, dict)]
    return None


def _parse_schedule_rows(
    raw_rows: list[dict[str, Any]], scenario: Scenario
) -> tuple[list[tuple[str, int, str, str, int | None]], list[str]]:
    """Normalize JSON schedule rows using the same rules as CSV schedules."""
    errors: list[str] = []
    rows: list[tuple[str, int, str, str, int | None]] = []
    vehicles = {vehicle.id for vehicle in scenario.vehicles}
    deliveries = {delivery.id for delivery in scenario.deliveries}
    for row_number, row in enumerate(raw_rows, start=1):
        vehicle_id = str(row.get("vehicle_id", "")).strip()
        delivery_id = str(row.get("delivery_id", "")).strip()
        stop_type = str(row.get("stop_type", "")).strip().lower()
        try:
            sequence = int(row.get("sequence"))
        except (TypeError, ValueError):
            errors.append(f"schedule.json row {row_number}: sequence must be an integer.")
            continue
        if vehicle_id not in vehicles:
            errors.append(f"schedule.json row {row_number}: unknown vehicle_id {vehicle_id!r}.")
        if stop_type not in {"pickup", "delivery", "depot_start", "depot_end"}:
            errors.append(f"schedule.json row {row_number}: invalid stop_type {stop_type!r}.")
        if stop_type in {"pickup", "delivery"} and delivery_id not in deliveries:
            errors.append(
                f"schedule.json row {row_number}: delivery_id {delivery_id!r} "
                "is not in the scenario."
            )
        arrival: int | None = None
        if row.get("planned_arrival") not in (None, ""):
            try:
                from data.importers.csv_importer import _clock

                arrival = _clock(row["planned_arrival"], "planned_arrival")
            except ValueError as exc:
                errors.append(f"schedule.json row {row_number}: {exc}")
        rows.append((vehicle_id, sequence, stop_type, delivery_id, arrival))
    return rows, errors


def _parse_schedule_csv(
    data: bytes, scenario: Scenario
) -> tuple[
    list[tuple[str, int, str, str, int | None]],
    list[str],  # errors
]:
    """Parse a schedule CSV.  Returns (rows, errors)."""
    import csv as _csv

    text = data.decode("utf-8-sig")
    # Support both , and ; delimiters
    sample = text[:2048]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","
    reader = list(_csv.DictReader(io.StringIO(text), delimiter=delimiter))

    errors: list[str] = []
    rows: list[tuple[str, int, str, str, int | None]] = []

    from data.importers.aliases import FIELD_ALIASES

    def alias_key(header: str) -> str:
        lower = header.strip().lower()
        # direct match
        if lower in {"vehicle_id", "sequence", "stop_type", "delivery_id", "planned_arrival"}:
            return lower
        # alias lookup
        for canonical, alts in FIELD_ALIASES.items():
            if lower == canonical or lower in alts:
                return canonical
        return lower

    if not reader:
        errors.append("Schedule CSV has no data rows.")
        return rows, errors

    headers = {alias_key(h): h for h in reader[0]}
    required = {"vehicle_id", "sequence", "stop_type", "delivery_id"}
    missing_cols = required - set(headers)
    if missing_cols:
        errors.append(
            f"Schedule CSV is missing required columns: {', '.join(sorted(missing_cols))}. "
            "Required: vehicle_id, sequence, stop_type, delivery_id."
        )
        return rows, errors

    from data.importers.csv_importer import _clock

    vehicle_ids = {v.id for v in scenario.vehicles}
    delivery_ids = {d.id for d in scenario.deliveries}
    unknown_deliveries: list[str] = []

    for row_num, row in enumerate(reader, start=2):

        def cell(key: str, current_row: dict[str, str] = row) -> str:
            col = headers.get(key, key)
            return current_row.get(col, "").strip()

        vid = cell("vehicle_id")
        if vid not in vehicle_ids:
            errors.append(f"schedule.csv row {row_num}: unknown vehicle_id {vid!r}.")
            continue

        try:
            seq = int(cell("sequence"))
        except ValueError:
            errors.append(f"schedule.csv row {row_num}: sequence must be an integer.")
            continue

        stop_type = cell("stop_type").lower()
        if stop_type not in {"pickup", "delivery", "depot_start", "depot_end"}:
            errors.append(
                f"schedule.csv row {row_num}: stop_type {stop_type!r} is not recognized. "
                "Use: pickup, delivery, depot_start, depot_end."
            )
            continue

        did = cell("delivery_id")
        if did and did not in delivery_ids:
            unknown_deliveries.append(did)

        arr_raw = cell("planned_arrival")
        arr: int | None = None
        if arr_raw:
            try:
                arr = _clock(arr_raw, "planned_arrival")
            except ValueError:
                pass  # non-fatal, just won't produce warnings

        rows.append((vid, seq, stop_type, did, arr))

    if unknown_deliveries:
        unique_unknown = sorted(set(unknown_deliveries))
        errors.append(
            f"Schedule CSV references deliveries not in the scenario: "
            f"{', '.join(unique_unknown)}. The whole upload is rejected."
        )

    return rows, errors


def _build_imported_plan(
    rows: list[tuple[str, int, str, str, int | None]],
    scenario: Scenario,
) -> tuple[Plan, list[str], list[str]]:
    """Build a Plan from schedule rows by recomputing all timings.

    Returns (plan, arrival_warnings, missing_delivery_ids).
    """
    from collections import defaultdict

    delivery_map = {d.id: d for d in scenario.deliveries}

    # Group by vehicle, sort by sequence
    by_vehicle: dict[str, list[tuple[int, str, str, int | None]]] = defaultdict(list)
    for vid, seq, stop_type, did, arr in rows:
        by_vehicle[vid].append((seq, stop_type, did, arr))
    for vid in by_vehicle:
        by_vehicle[vid].sort(key=lambda x: x[0])

    routes: list[Route] = []
    placed_ids: set[str] = set()
    arrival_warnings: list[str] = []

    for vehicle in scenario.vehicles:
        vehicle_rows = by_vehicle.get(vehicle.id, [])
        stops_raw: list[Stop] = []

        # Ensure there's a depot_start
        has_depot_start = any(st == "depot_start" for _, st, _, _ in vehicle_rows)
        if not has_depot_start:
            stops_raw.append(
                Stop(
                    kind=StopKind.DEPOT_START,
                    location_id=scenario.depot_id,
                    arrival=scenario.start_time,
                    service_start=scenario.start_time,
                    depart=scenario.start_time,
                    load_after=0,
                )
            )

        for _, stop_type, did, _uploaded_arr in vehicle_rows:
            if stop_type == "depot_start":
                stops_raw.append(
                    Stop(
                        kind=StopKind.DEPOT_START,
                        location_id=scenario.depot_id,
                        arrival=scenario.start_time,
                        service_start=scenario.start_time,
                        depart=scenario.start_time,
                        load_after=0,
                    )
                )
            elif stop_type in {"pickup", "delivery"}:
                if not did or did not in delivery_map:
                    continue
                delivery = delivery_map[did]
                kind = StopKind.PICKUP if stop_type == "pickup" else StopKind.DELIVERY
                stops_raw.append(
                    Stop(
                        kind=kind,
                        delivery_id=did,
                        location_id=delivery.location_id,
                        arrival=scenario.start_time,
                        service_start=scenario.start_time,
                        depart=scenario.start_time,
                        load_after=0,
                    )
                )
                if stop_type == "delivery":
                    placed_ids.add(did)

        # Recompute timing via simulator
        route = simulate_route(scenario, vehicle.id, stops_raw)
        routes.append(route)

        # Produce arrival warnings for any uploaded_arr that differs from recomputed
        for idx, (_seq, _stop_type, did, uploaded_arr) in enumerate(vehicle_rows):
            if uploaded_arr is None:
                continue
            if idx + (0 if has_depot_start else 1) < len(route.stops):
                recomputed_stop = route.stops[idx + (0 if has_depot_start else 1)]
                diff = abs(recomputed_stop.arrival - uploaded_arr)
                if diff > 0:
                    arrival_warnings.append(
                        f"Vehicle {vehicle.id}, delivery {did!r}: "
                        f"uploaded arrival {uploaded_arr} min differs from "
                        f"recomputed {recomputed_stop.arrival} min (delta {diff} min)."
                    )

    # Build unplaced for missing deliveries
    all_delivery_ids = {d.id for d in scenario.deliveries}
    missing_ids = sorted(all_delivery_ids - placed_ids)
    unplaced = [
        Unplaced(
            delivery_id=did,
            reasons=[
                Reason(
                    code=ReasonCode.OTHER,
                    detail="not in uploaded schedule",
                )
            ],
        )
        for did in missing_ids
    ]

    plan = Plan(
        version_id=f"{scenario.name}-imported-v1",
        scenario_ref=scenario.name,
        routes=routes,
        unplaced=unplaced,
    )
    return plan, arrival_warnings, missing_ids


@router.post("/plan/import/preview", response_model=ImportPreview)
async def plan_import_preview(
    file: UploadFile = File(...),  # noqa: B008
    store: SessionStore = Depends(get_store),  # noqa: B008
) -> ImportPreview:
    """Parse a schedule CSV/JSON without committing anything."""
    if mock_mode():
        return ImportPreview(
            token="mock-import-token",
            counts={"stops": 12, "vehicles": 3},
            missing_delivery_ids=[],
            arrival_warnings=[],
            errors=[],
        )

    data = await file.read()
    _check_size(data, file.filename or "schedule")

    errors: list[str] = []
    plan: Plan | None = None
    arrival_warnings: list[str] = []
    missing_ids: list[str] = []

    try:
        fname = (file.filename or "").lower()
        if fname.endswith(".json"):
            raw = json.loads(data.decode("utf-8-sig"))
            if isinstance(raw, dict) and "routes" in raw:
                imported = Plan.model_validate(raw)
                routes = [
                    simulate_route(store.scenario, route.vehicle_id, route.stops)
                    for route in imported.routes
                ]
                plan = imported.model_copy(
                    update={"routes": routes, "scenario_ref": store.scenario.name}
                )
            else:
                schedule_rows = _schedule_rows_from_json(raw)
                if schedule_rows is None:
                    raise ValueError(
                        "Schedule JSON must be a list of stop rows or an object "
                        "with a 'stops' list."
                    )
                rows, errors = _parse_schedule_rows(schedule_rows, store.scenario)
                if not errors:
                    plan, arrival_warnings, missing_ids = _build_imported_plan(rows, store.scenario)
        elif fname.endswith(".csv"):
            rows, errors = _parse_schedule_csv(data, store.scenario)
            if not errors:
                plan, arrival_warnings, missing_ids = _build_imported_plan(rows, store.scenario)
        else:
            errors.append("Unsupported format. Use .csv or .json for schedule import.")
    except (ValueError, KeyError) as exc:
        errors.append(str(exc))

    if errors:
        return ImportPreview(
            token="",
            counts={},
            errors=errors,
        )

    assert plan is not None
    token = secrets.token_hex(16)
    _IMPORT_PREVIEWS[token] = {
        "plan": plan,
        "arrival_warnings": arrival_warnings,
        "missing_ids": missing_ids,
    }

    stop_count = sum(len(r.stops) for r in plan.routes)
    return ImportPreview(
        token=token,
        counts={
            "stops": stop_count,
            "vehicles": len(plan.routes),
            "placed_deliveries": len(store.scenario.deliveries) - len(missing_ids),
        },
        missing_delivery_ids=missing_ids,
        arrival_warnings=arrival_warnings,
        errors=[],
    )


@router.post("/plan/import/confirm", response_model=ImportResult)
def plan_import_confirm(
    request: ImportConfirmRequest,
    store: SessionStore = Depends(get_store),  # noqa: B008
) -> ImportResult:
    """Commit an imported plan. Validate it; load even if invalid, but flag it."""
    if mock_mode():
        plan = Plan.model_validate_json(json.dumps(fixture("plan_initial.json")))
        report = ValidationReport.model_validate_json(
            json.dumps(fixture("validation_report_ok.json"))
        )
        return ImportResult(
            plan=plan,
            validation_report=report,
            is_valid=report.passed,
        )

    entry = _IMPORT_PREVIEWS.pop(request.token, None)
    if entry is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Import preview token not found or already consumed. "
                "Call /plan/import/preview first."
            ),
        )

    plan: Plan = entry["plan"]
    arrival_warnings: list[str] = entry["arrival_warnings"]
    missing_ids: list[str] = entry["missing_ids"]

    report = validate(store.scenario, plan)

    # Always adopt, even if invalid
    store.plan = plan
    store.versions[plan.version_id] = plan

    return ImportResult(
        plan=plan,
        validation_report=report,
        is_valid=report.passed,
        arrival_warnings=arrival_warnings,
        unplaced=missing_ids,
    )


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TemplateKind = Literal[
    "scenario_json",
    "locations_csv",
    "vehicles_csv",
    "deliveries_csv",
    "matrix_csv",
    "schedule_csv",
]

_TEMPLATE_NAMES: dict[str, str] = {
    "scenario_json": "scenario_template.json",
    "locations_csv": "locations_template.csv",
    "vehicles_csv": "vehicles_template.csv",
    "deliveries_csv": "deliveries_template.csv",
    "matrix_csv": "matrix_template.csv",
    "schedule_csv": "schedule_template.csv",
}


def _micro_scenario() -> Scenario:
    from api.store import load_scenario

    try:
        return load_scenario("micro")
    except KeyError:
        return load_scenario("baseline")


def _scenario_json_template(scenario: Scenario) -> bytes:
    return json.dumps(scenario.model_dump(mode="json"), indent=2).encode("utf-8")


def _locations_csv_template(scenario: Scenario) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["location_id", "name", "aliases", "x", "y"])
    for loc in scenario.locations:
        w.writerow(
            [
                loc.id,
                loc.name,
                ",".join(loc.aliases),
                loc.x or "",
                loc.y or "",
            ]
        )
    return buf.getvalue().encode("utf-8")


def _vehicles_csv_template(scenario: Scenario) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["vehicle_id", "name", "capacity", "start_location", "shift_end"])
    for v in scenario.vehicles:
        shift = ""
        if v.shift_end is not None:
            h, m = divmod(v.shift_end, 60)
            shift = f"{h:02d}:{m:02d}"
        w.writerow([v.id, v.name, v.capacity, v.start_location_id, shift])
    return buf.getvalue().encode("utf-8")


def _deliveries_csv_template(scenario: Scenario) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "delivery_id",
            "location",
            "demand",
            "window_start",
            "window_end",
            "service_minutes",
            "priority",
        ]
    )
    for d in scenario.deliveries:
        wo_h, wo_m = divmod(d.window_open, 60)
        wc_h, wc_m = divmod(d.window_close, 60)
        w.writerow(
            [
                d.id,
                d.location_id,
                d.demand,
                f"{wo_h:02d}:{wo_m:02d}",
                f"{wc_h:02d}:{wc_m:02d}",
                d.service_time,
                d.priority,
            ]
        )
    return buf.getvalue().encode("utf-8")


def _matrix_csv_template(scenario: Scenario) -> bytes:
    loc_ids = [loc.id for loc in scenario.locations]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["location_id"] + loc_ids)
    for i, row in enumerate(scenario.travel_times):
        w.writerow([loc_ids[i]] + list(row))
    return buf.getvalue().encode("utf-8")


def _schedule_csv_template(scenario: Scenario, plan: Plan | None = None) -> bytes:
    """Template is an empty schedule CSV with the correct headers."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["vehicle_id", "sequence", "stop_type", "delivery_id", "planned_arrival"])
    if plan is not None:
        seq_counter: dict[str, int] = {}
        for route in plan.routes:
            vid = route.vehicle_id
            for stop in route.stops:
                seq_counter[vid] = seq_counter.get(vid, 0) + 1
                h, m = divmod(stop.arrival, 60)
                w.writerow(
                    [
                        vid,
                        seq_counter[vid],
                        stop.kind.value if hasattr(stop.kind, "value") else str(stop.kind),
                        stop.delivery_id or "",
                        f"{h:02d}:{m:02d}",
                    ]
                )
    return buf.getvalue().encode("utf-8")


@router.get("/templates/{kind}")
def get_template(
    kind: TemplateKind,
    store: SessionStore = Depends(get_store),  # noqa: B008
) -> Response:
    """Return a downloadable template generated from the micro scenario."""
    scenario = _micro_scenario()
    plan: Plan | None = None
    if kind == "schedule_csv":
        from engine.construct import build_plan as _build

        plan = _build(scenario)

    dispatch: dict[str, Any] = {
        "scenario_json": lambda: _scenario_json_template(scenario),
        "locations_csv": lambda: _locations_csv_template(scenario),
        "vehicles_csv": lambda: _vehicles_csv_template(scenario),
        "deliveries_csv": lambda: _deliveries_csv_template(scenario),
        "matrix_csv": lambda: _matrix_csv_template(scenario),
        "schedule_csv": lambda: _schedule_csv_template(scenario, plan),
    }
    content: bytes = dispatch[kind]()
    filename = _TEMPLATE_NAMES[kind]
    media_type = "application/json" if kind == "scenario_json" else "text/csv"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
