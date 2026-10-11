"""Exact-match resolution for dispatcher names."""

from __future__ import annotations

import re
from collections.abc import Sequence


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def resolve(value: str, items: Sequence[object]) -> tuple[object | None, list[object]]:
    needle = normalize(value)
    matches = []
    for item in items:
        names = [getattr(item, "id", ""), getattr(item, "name", "")]
        names.extend(getattr(item, "aliases", []))
        if needle in {normalize(name) for name in names}:
            matches.append(item)
    return (matches[0], matches) if len(matches) == 1 else (None, matches)
