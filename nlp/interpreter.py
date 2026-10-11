"""Offline rule-based dispatcher report interpreter."""

from __future__ import annotations

import re
from uuid import uuid4

from contract.models import (
    Delivery,
    Proposal,
    RoadClosure,
    SourceSpan,
    UrgentDelivery,
    VehicleFailure,
)

from .resolver import resolve
from .time_grammar import parse_time


def _span(text: str, value: str, field: str) -> SourceSpan | None:
    index = text.casefold().find(value.casefold())
    return SourceSpan(field=field, start=index, end=index + len(value)) if index >= 0 else None


def interpret(text: str, scenario, now: int | None = None) -> Proposal:
    report_now = scenario.now if now is None else now
    spans: list[SourceSpan] = []
    warnings: list[str] = []
    rejections: list[str] = []
    lowered = text.casefold().strip()
    if not lowered:
        raise ValueError("Report cannot be empty.")
    if sum(word in lowered for word in ("close", "blocked", "broke", "failed", "urgent")) > 1:
        rejections.append("Submit one disruption per report.")

    if any(word in lowered for word in ("close", "blocked")):
        match = re.search(
            r"(?:between|from)\s+(.+?)\s+(?:and|to)\s+(.+?)(?:\s+(?:from|until|at)\s+|$)",
            text,
            re.I,
        )
        if match:
            left_text, right_text = match.group(1).strip(), match.group(2).strip()
        else:
            left_text = right_text = ""
        left, _ = resolve(left_text, scenario.locations)
        right, _ = resolve(right_text, scenario.locations)
        if not left or not right:
            rejections.append("Unknown or ambiguous closure location.")
        if left and right:
            spans.extend(
                filter(
                    None,
                    [_span(text, left_text, "location_a"), _span(text, right_text, "location_b")],
                )
            )
        times = re.findall(r"\b\d{1,2}(?::|\.)\d{2}\s*(?:am|pm)?|\b\d{1,2}\s*(?:am|pm)", text, re.I)
        start = parse_time(times[0], report_now) if times else report_now
        end = parse_time(times[1], report_now) if len(times) > 1 else 1440
        if not times:
            warnings.append("No closure time given; assumed active from now until end of day.")
        disruption = RoadClosure(
            type="road_closure",
            a=getattr(left, "id", left_text),
            b=getattr(right, "id", right_text),
            mode="add_minutes",
            value=60 if "twice" in lowered else 20,
            both_directions=True,
            start=start,
            end=max(start + 1, end),
        )
    elif any(word in lowered for word in ("broke", "failed", "breakdown")):
        vehicle_match = re.search(r"(van\s+\d+|vehicle\s+\d+|v\d+)", text, re.I)
        vehicle, _ = (
            resolve(vehicle_match.group(1), scenario.vehicles) if vehicle_match else (None, [])
        )
        if not vehicle:
            rejections.append("Vehicle name is missing, unknown, or ambiguous.")
        time_match = re.search(
            r"\b\d{1,2}(?::|\.)\d{2}\s*(?:am|pm)?|\b\d{1,2}\s*(?:am|pm)", text, re.I
        )
        at_time = parse_time(time_match.group(0), report_now) if time_match else report_now
        if vehicle_match:
            span = _span(text, vehicle_match.group(1), "vehicle")
            if span:
                spans.append(span)
        disruption = VehicleFailure(
            type="vehicle_failure",
            vehicle_id=getattr(vehicle, "id", vehicle_match.group(1) if vehicle_match else ""),
            at_time=at_time,
        )
    else:
        location_match = re.search(r"(?:at|to)\s+([A-Za-z][\w ]+)", text, re.I)
        location, _ = (
            resolve(location_match.group(1).strip(), scenario.locations)
            if location_match
            else (None, [])
        )
        if not location:
            rejections.append("Urgent delivery location is missing, unknown, or ambiguous.")
        delivery = Delivery(
            id=f"NEW-{uuid4().hex[:8]}",
            location_id=getattr(
                location, "id", location_match.group(1).strip() if location_match else ""
            ),
            demand=1,
            window_open=report_now,
            window_close=1440,
            service_time=5,
            priority=2,
            release_time=report_now,
        )
        disruption = UrgentDelivery(
            type="urgent_delivery", delivery=delivery, report_time=report_now
        )

    return Proposal(
        id=uuid4().hex,
        source="text",
        original_text=text,
        disruption=disruption,
        spans=spans,
        assumptions=warnings,
        rejections=rejections,
    )
