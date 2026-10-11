"""Deterministic, matrix-only travel-time calculation."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from contract.models import RoadClosure, Scenario


def travel_time(
    scenario_matrix: Scenario | Sequence[Sequence[int]],
    closures: Sequence[RoadClosure],
    a: str | int,
    b: str | int,
    depart_time: int,
    *,
    location_index: Mapping[str, int] | None = None,
    now: int = 0,
) -> int:
    """Return the direct matrix time with active closures applied.

    Overlapping closures are composed in input order after grouping by mode:
    set first, then multiply, then add. This is deterministic and keeps the
    closure rule independent of caller ordering between different modes.
    """
    if isinstance(scenario_matrix, Scenario):
        matrix = scenario_matrix.travel_times
        location_index = {location.id: i for i, location in enumerate(scenario_matrix.locations)}
        now = scenario_matrix.now
    else:
        matrix = scenario_matrix

    def index(value: str | int) -> int:
        if isinstance(value, int):
            return value
        if location_index is None or value not in location_index:
            raise ValueError(f"unknown location {value!r}")
        return location_index[value]

    a_index, b_index = index(a), index(b)
    value = float(matrix[a_index][b_index])
    active = [
        closure
        for closure in closures
        if max(closure.start, now) <= depart_time < closure.end
        and (
            (closure.a == a and closure.b == b)
            or (closure.both_directions and closure.a == b and closure.b == a)
        )
    ]
    for mode in ("set_minutes", "multiply", "add_minutes"):
        for closure in active:
            if closure.mode == mode:
                if mode == "set_minutes":
                    value = closure.value
                elif mode == "multiply":
                    value *= closure.value
                else:
                    value += closure.value
    return max(0, math.ceil(value))
