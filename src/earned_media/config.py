from __future__ import annotations

import functools
import os
from pathlib import Path
from typing import Any

import yaml

# In the repo's src layout this resolves to the repo root. When the package is
# pip-installed (e.g. in Docker) it resolves into site-packages, so deployments
# must set APP_ROOT to the directory holding specs/, data/, and evals/.
ROOT = Path(os.environ.get("APP_ROOT", Path(__file__).resolve().parents[2]))
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
