"""Security lookup tool for the security-assessor skill.

Returns security incident data from YAML fixtures, keyed by alert ID
and data source (network, auth, vulnerabilities, behavior).
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

import yaml


def _fixtures_dir() -> Path:
    env_dir = os.environ.get("EVAL_FIXTURES_DIR")
    if env_dir:
        return Path(env_dir)
    return Path(__file__).parent.parent / "fixtures"


@lru_cache(maxsize=4)
def _load_fixture(source: str) -> dict:
    path = _fixtures_dir() / f"security_{source}.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


_cache: dict[str, str] = {}


def security_lookup(source: str, query: str) -> str:
    """Look up security incident data.

    Args:
        source: One of "network", "auth", "vulnerabilities", "behavior"
        query: The alert ID (e.g., "alert-1001")

    Returns:
        JSON string with the security data for this alert and source.
    """
    cache_key = f"{source}:{query}"
    if cache_key in _cache:
        return _cache[cache_key]

    data = _load_fixture(source)
    alert_id = query.strip().lower()

    if alert_id in data:
        result = json.dumps(data[alert_id], indent=2)
    else:
        result = json.dumps(
            {
                "error": f"No data found for alert '{query}' in {source}",
                "available_alerts": list(data.keys())[:5],
            }
        )

    _cache[cache_key] = result
    return result
