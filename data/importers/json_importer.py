"""JSON scenario importer with exact field-name adapters and contract validation."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from contract.models import Scenario

from .aliases import adapt_fields


def _read_payload(source: str | bytes | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(source, Mapping):
        return dict(source)
    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
    elif isinstance(source, bytes):
        try:
            text = source.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"scenario JSON must be UTF-8 encoded: {exc}") from exc
    elif isinstance(source, str):
        candidate = source.strip()
        if candidate.startswith("{") or candidate.startswith("["):
            text = source
        else:
            path = Path(source)
            if not path.is_file():
                raise ValueError(f"scenario JSON path does not exist: {source}")
            text = path.read_text(encoding="utf-8")
    else:
        raise TypeError("scenario JSON must be a mapping, JSON text, bytes, or file path")

    try:
        value = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid scenario JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("scenario JSON must contain a JSON object")
    return value


def _normalize_scenario(data: dict[str, Any]) -> dict[str, Any]:
    # Generated scenario-pack entries carry demo disruptions beside the scenario.
    if "scenario" in data:
        nested = data["scenario"]
        if not isinstance(nested, dict):
            raise ValueError("scenario pack field 'scenario' must be an object")
        data = dict(nested)

    data = adapt_fields(data)
    for key in ("locations", "vehicles", "deliveries"):
        entries = data.get(key)
        if isinstance(entries, list):
            data[key] = [adapt_fields(row) if isinstance(row, Mapping) else row for row in entries]

    locations = data.get("locations", [])
    if isinstance(locations, list):
        lookup: dict[str, set[str]] = {}
        for location in locations:
            if not isinstance(location, dict) or not isinstance(location.get("id"), str):
                continue
            aliases = location.get("aliases", [])
            aliases = aliases if isinstance(aliases, list) else []
            for label in [location["id"], location.get("name"), *aliases]:
                if isinstance(label, str):
                    lookup.setdefault(label.strip().casefold(), set()).add(location["id"])

        def resolve_location(value: Any, field: str) -> Any:
            if not isinstance(value, str):
                return value
            matches = lookup.get(value.strip().casefold(), set())
            if len(matches) == 1:
                return next(iter(matches))
            if len(matches) > 1:
                raise ValueError(f"ambiguous location {value!r} in {field}; use its exact id")
            raise ValueError(f"unknown location {value!r} in {field}")

        if "depot_id" in data:
            data["depot_id"] = resolve_location(data["depot_id"], "depot_id")
        vehicles = data.get("vehicles", [])
        for vehicle in vehicles if isinstance(vehicles, list) else []:
            if isinstance(vehicle, dict) and "start_location_id" in vehicle:
                vehicle["start_location_id"] = resolve_location(
                    vehicle["start_location_id"], "vehicles.start_location_id"
                )
        deliveries = data.get("deliveries", [])
        for delivery in deliveries if isinstance(deliveries, list) else []:
            if isinstance(delivery, dict) and "location_id" in delivery:
                delivery["location_id"] = resolve_location(
                    delivery["location_id"], "deliveries.location_id"
                )

    # Accept organizer windows written as clock strings, while the contract stores
    # integer minutes since midnight.
    for row in data.get("deliveries", []):
        if not isinstance(row, dict):
            continue
        for key in ("window_open", "window_close", "release_time"):
            value = row.get(key)
            if isinstance(value, str) and ":" in value:
                row[key] = _parse_clock(value, f"deliveries.{key}")
    return data


def _parse_clock(value: str, field: str) -> int:
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
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field} must be minutes or HH:MM, got {value!r}") from exc
    if not 0 <= hours <= 23 or not 0 <= minutes <= 59:
        raise ValueError(f"{field} is not a valid 24-hour time: {value!r}")
    return hours * 60 + minutes


def import_scenario_json(source: str | bytes | Path | Mapping[str, Any]) -> Scenario:
    """Load a scenario object or a generated scenario-pack JSON file.

    Field aliases are explicit; names and identifiers are never guessed. Pydantic
    validation errors are wrapped with a concise importer-level prefix.
    """
    normalized = _normalize_scenario(_read_payload(source))
    try:
        return Scenario.model_validate(normalized)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        raise ValueError(f"scenario does not match the ReRoute contract: {details}") from exc


load_scenario_json = import_scenario_json

__all__ = ["import_scenario_json", "load_scenario_json"]
