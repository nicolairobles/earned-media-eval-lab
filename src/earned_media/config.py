from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = ROOT / "specs"
DATA_DIR = ROOT / "data" / "fixtures"

SCORING_VERSION = "scoring-v1"


@functools.lru_cache(maxsize=None)
def load_yaml(name: str) -> dict[str, Any]:
    with open(SPECS_DIR / name) as f:
        return yaml.safe_load(f)


def scoring_policy() -> dict[str, Any]:
    return load_yaml("scoring-policy.yaml")


def threshold_policy() -> dict[str, Any]:
    return load_yaml("threshold-policy.yaml")
