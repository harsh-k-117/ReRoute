"""Golden fixture access for deterministic mock mode."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURE_DIR = Path(__file__).parents[1] / "contract" / "fixtures"


def fixture(name: str) -> Any:
    path = FIXTURE_DIR / name
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))
