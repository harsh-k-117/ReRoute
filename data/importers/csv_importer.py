"""CSV scenario importer for locations, vehicles, deliveries, and travel times."""

from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TextIO

from pydantic import ValidationError

from contract.models import Scenario

from .aliases import adapt_fields


def _read_csv(source: str | bytes | Path | TextIO, label: str) -> list[dict[str, str]]:
    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8-sig")
    elif isinstance(source, bytes):
        text = source.decode("utf-8-sig")
    elif isinstance(source, str):
        path = Path(source)
        if "\n" not in source and path.is_file():
            text = path.read_text(encoding="utf-8-sig")
        else:
            text = source
    else:
        text = source.read()
    clean_text = text.lstrip("\ufeff")
    sample = clean_text[:2048]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","
    rows = list(csv.DictReader(io.StringIO(clean_text), delimiter=delimiter))
    if not rows:
        raise ValueError(f"{label} CSV has a header but no data rows")
    return [{str(k).strip(): (v or "").strip() for k, v in row.items() if k} for row in rows]


def _value(row: Mapping[str, str], key: str, *, required: bool = True, default: Any = None) -> Any:
    normalized = adapt_fields(row)
    if key in normalized and normalized[key] != "":
        return normalized[key]
    if required:
        raise ValueError(f"CSV row is missing required field {key!r}")
    return default


def _number(value: Any, field: str, *, optional: bool = False) -> int | None:
    if value is None or value == "":
        if optional:
            return None
        raise ValueError(f"CSV field {field!r} is required")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"CSV field {field!r} must be an integer, got {value!r}") from exc


def _clock(value: Any, field: str, *, optional: bool = False) -> int | None:
    if value is None or value == "":
        if optional:
            return None
        raise ValueError(f"CSV field {field!r} is required")
    if isinstance(value, str) and ":" in value:
        try:
            match = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*([ap]\.?m\.?)?\s*", value, re.I)
            if match is None:
                raise ValueError
            hours, minutes = int(match.group(1)), int(match.group(2))
            meridiem = match.group(3)
            if meridiem:
                if not 1 <= hours <= 12:
                    raise ValueError
                hours = hours % 12 + (12 if meridiem.lower().startswith("p") else 0)
        except ValueError as exc:
            raise ValueError(f"CSV field {field!r} must be minutes or HH:MM") from exc
        if not 0 <= hours <= 23 or not 0 <= minutes <= 59:
            raise ValueError(f"CSV field {field!r} is not a valid time: {value!r}")
        return hours * 60 + minutes
    return _number(value, field, optional=optional)


def _aliases(value: str) -> list[str]:
    if not value:
        return []
    if value.lstrip().startswith("["):
        parsed = json.loads(value)
        if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
            raise ValueError("aliases must be a JSON array of strings or a comma-separated list")
        return parsed
    return [part.strip() for part in value.split(",") if part.strip()]


def _resolve_location(value: str, locations: Sequence[dict[str, Any]]) -> str:
    candidate = value.strip().casefold()
    matches = {
        str(location["id"])
        for location in locations
        if candidate
        in {
            str(location["id"]).casefold(),
            str(location["name"]).casefold(),
            *(alias.casefold() for alias in location.get("aliases", [])),
        }
    }
    if len(matches) == 1:
        return matches.pop()
    if not matches:
        raise ValueError(f"unknown location {value!r}; use an exact id, name, or alias")
    raise ValueError(f"ambiguous location {value!r}; use its exact location id")


def _normalize_rows(rows: list[dict[str, str]], section: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        try:
            normalized.append(adapt_fields(row))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{section} CSV row {row_number}: {exc}") from exc
    return normalized


def _travel_matrix(source: str | bytes | Path | TextIO, location_ids: list[str]) -> list[list[int]]:
    rows = _read_csv(source, "travel times")
    matrix = [
        [0 if i == j else -1 for j in range(len(location_ids))] for i in range(len(location_ids))
    ]
    index = {location_id: i for i, location_id in enumerate(location_ids)}
    columns = {key.casefold(): key for key in rows[0]}
    from_key = next(
        (columns[k] for k in ("from", "from_id", "origin", "origin_id") if k in columns), None
    )
    to_key = next(
        (columns[k] for k in ("to", "to_id", "destination", "destination_id") if k in columns), None
    )
    minutes_key = next(
        (columns[k] for k in ("minutes", "travel_minutes", "travel_time", "time") if k in columns),
        None,
    )
    if from_key and to_key and minutes_key:
        for row_number, row in enumerate(rows, start=2):
            source_id, target_id = row[from_key], row[to_key]
            if source_id not in index or target_id not in index:
                raise ValueError(
                    f"travel times CSV row {row_number} references an unknown location"
                )
            minutes = _number(row[minutes_key], "minutes")
            matrix[index[source_id]][index[target_id]] = minutes
        for i in range(len(index)):
            for j in range(i + 1, len(index)):
                a, b = matrix[i][j], matrix[j][i]
                if a < 0 and b >= 0:
                    matrix[i][j] = b
                elif b < 0 and a >= 0:
                    matrix[j][i] = a
    else:
        # Matrix form: first column is a location id; remaining columns are ids.
        row_key = next(
            (columns[k] for k in ("location_id", "from", "id", "location") if k in columns), None
        )
        if row_key is None:
            raise ValueError(
                "travel times CSV needs from,to,minutes columns or a matrix with location_id rows"
            )
        for row_number, row in enumerate(rows, start=2):
            source_id = row[row_key]
            if source_id not in index:
                raise ValueError(
                    f"travel times CSV row {row_number} references unknown location {source_id!r}"
                )
            for target_id in location_ids:
                column = columns.get(target_id.casefold())
                if column is None:
                    raise ValueError(f"travel times CSV is missing matrix column {target_id!r}")
                matrix[index[source_id]][index[target_id]] = _number(
                    row[column], f"{source_id}->{target_id}"
                )
    if any(value < 0 for row in matrix for value in row):
        raise ValueError(
            "travel times CSV must define every matrix entry, or an inferable edge list"
        )
    for i in range(len(matrix)):
        if matrix[i][i] != 0:
            raise ValueError("travel times matrix diagonal entries must be zero")
    return matrix


def import_scenario_csv(
    locations_csv: str | bytes | Path | TextIO,
    vehicles_csv: str | bytes | Path | TextIO,
    deliveries_csv: str | bytes | Path | TextIO,
    travel_times_csv: str | bytes | Path | TextIO,
    *,
    name: str = "imported-csv",
    depot_id: str = "DEPOT",
    now: int | str = 0,
    start_time: int | str = 0,
    seed: int = 0,
    config: Mapping[str, Any] | None = None,
) -> Scenario:
    """Import four CSV tables and validate the result with ``Scenario``.

    Location, vehicle, and delivery headers accept the exact aliases documented in
    :mod:`data.importers.aliases`. Travel time CSV may be an ID-keyed square matrix
    or an edge list with ``from,to,minutes`` columns.
    """
    locations_rows = _normalize_rows(_read_csv(locations_csv, "locations"), "locations")
    locations: list[dict[str, Any]] = []
    for row in locations_rows:
        locations.append(
            {
                "id": _value(row, "location_id"),
                "name": _value(row, "name"),
                "aliases": _aliases(_value(row, "aliases", required=False, default="")),
                **({"x": float(row["x"])} if row.get("x", "") else {}),
                **({"y": float(row["y"])} if row.get("y", "") else {}),
            }
        )

    vehicles: list[dict[str, Any]] = []
    for row in _normalize_rows(_read_csv(vehicles_csv, "vehicles"), "vehicles"):
        start_location = _value(row, "start_location_id", required=False, default=depot_id)
        vehicles.append(
            {
                "id": _value(row, "id"),
                "name": _value(row, "name", required=False, default=_value(row, "id")),
                "aliases": _aliases(_value(row, "aliases", required=False, default="")),
                "capacity": _number(_value(row, "capacity"), "capacity"),
                "shift_end": _clock(
                    _value(row, "shift_end", required=False, default=None),
                    "shift_end",
                    optional=True,
                ),
                "start_location_id": _resolve_location(str(start_location), locations),
            }
        )

    deliveries: list[dict[str, Any]] = []
    for row in _normalize_rows(_read_csv(deliveries_csv, "deliveries"), "deliveries"):
        location = _resolve_location(str(_value(row, "location_id")), locations)
        delivery: dict[str, Any] = {
            "id": _value(row, "id"),
            "location_id": location,
            "demand": _number(_value(row, "demand"), "demand"),
            "window_open": _clock(_value(row, "window_open"), "window_open"),
            "window_close": _clock(_value(row, "window_close"), "window_close"),
            "service_time": _number(_value(row, "service_time"), "service_time"),
        }
        for key, converter in (("priority", _number), ("release_time", _clock)):
            raw = _value(row, key, required=False, default=None)
            if raw is not None:
                delivery[key] = (
                    converter(raw, key, optional=True)
                    if converter is _clock
                    else converter(raw, key)
                )
        deliveries.append(delivery)

    location_ids = [str(location["id"]) for location in locations]
    depot = _resolve_location(depot_id, locations)
    data = {
        "name": name,
        "depot_id": depot,
        "locations": locations,
        "vehicles": vehicles,
        "deliveries": deliveries,
        "travel_times": _travel_matrix(travel_times_csv, location_ids),
        "now": _clock(now, "now"),
        "start_time": _clock(start_time, "start_time"),
        "config": dict(config or {}),
        "seed": seed,
    }
    try:
        return Scenario.model_validate(data)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        raise ValueError(f"CSV data does not match the ReRoute contract: {details}") from exc


load_scenario_csv = import_scenario_csv

__all__ = ["import_scenario_csv", "load_scenario_csv"]
