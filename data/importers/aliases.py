"""Field-name adapters for common organizer and spreadsheet column names."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "name": ("scenario_name", "scenario", "title"),
    "depot_id": ("depot", "depot_location", "depot_location_id"),
    "locations": ("stops", "places"),
    "vehicles": ("fleet", "trucks"),
    "deliveries": ("orders", "jobs"),
    "travel_times": ("travel_time_matrix", "time_matrix", "matrix"),
    "location_id": ("location", "place_id", "stop_id", "destination_id"),
    "id": ("delivery_id", "order_id", "job_id", "vehicle_id"),
    "demand": ("size", "load", "quantity", "parcel_count"),
    "window_open": ("window_start", "earliest", "ready_time", "time_window_start"),
    "window_close": ("window_end", "latest", "due_time", "time_window_end"),
    "service_time": ("service_minutes", "stop_duration", "duration"),
    "capacity": ("vehicle_capacity", "max_load"),
    "start_location_id": ("start_location", "home_location_id"),
    "shift_end": ("shift_end_time", "available_until"),
    "aliases": ("alternative_names", "synonyms"),
    "x": ("longitude", "east"),
    "y": ("latitude", "north"),
    "now": ("current_time", "dispatch_time"),
    "start_time": ("route_start", "depot_departure"),
}


def adapt_fields(
    data: Mapping[str, Any], aliases: Mapping[str, tuple[str, ...]] = FIELD_ALIASES
) -> dict[str, Any]:
    """Copy recognized aliases to canonical keys without fuzzy matching.

    Canonical keys always win when both a canonical key and an alias are present.
    Unknown keys are preserved so Pydantic can report them as invalid contract data.
    """
    normalized = dict(data)
    for canonical, alternatives in aliases.items():
        if canonical not in normalized:
            for alternative in alternatives:
                if alternative in normalized:
                    normalized[canonical] = normalized[alternative]
                    break
        for alternative in alternatives:
            normalized.pop(alternative, None)
    return normalized
