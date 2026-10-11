"""Small deterministic time grammar for reports."""

from __future__ import annotations

import re


def parse_time(value: str, now: int = 0) -> int | None:
    text = value.strip().casefold()
    match = re.fullmatch(r"(\d{1,2})(?::|\.)(\d{2})\s*(am|pm)?", text)
    if match:
        hour, minute, meridiem = int(match.group(1)), int(match.group(2)), match.group(3)
    else:
        match = re.fullmatch(r"(\d{1,2})\s*(am|pm)", text)
        if not match:
            return None
        hour, minute, meridiem = int(match.group(1)), 0, match.group(2)
    if meridiem:
        if hour == 12:
            hour = 0
        if meridiem == "pm":
            hour += 12
    return hour * 60 + minute if hour <= 23 and minute <= 59 else None


def parse_duration(value: str, now: int = 0) -> int | None:
    match = re.search(r"(\d+)\s*(?:minutes?|mins?)", value, re.I)
    if match:
        return now + int(match.group(1))
    match = re.search(r"(\d+)\s*(?:hours?|hrs?)", value, re.I)
    return now + int(match.group(1)) * 60 if match else None
