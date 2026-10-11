"""Environment-backed API settings."""

from __future__ import annotations

import os
from pathlib import Path


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().casefold() in {"1", "true", "yes", "on"}


def scenario_dir() -> Path:
    return Path(os.getenv("REROUTE_SCENARIO_DIR", Path(__file__).parents[1] / "data" / "scenarios"))


def mock_mode() -> bool:
    return env_bool("REROUTE_MOCK_MODE")
