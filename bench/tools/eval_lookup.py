"""Evaluation lookup tool — returns canned data from YAML fixtures.

Self-contained version for dc-bench. No external dependencies
beyond PyYAML. Reads fixture files from bench/fixtures/.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

_DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _get_fixtures_dir() -> Path:
    """Resolve the fixture directory.

    Checks EVAL_FIXTURES_DIR env var first, then
    falls back to the default bench/fixtures/ path.
    """
    override = os.environ.get("EVAL_FIXTURES_DIR")
    if override:
        return Path(override)
    return _DEFAULT_FIXTURES_DIR


# Cache loaded YAML files in memory.
_cache: dict[str, dict] = {}


def _load_source(source: str) -> dict:
    """Load and cache a fixture YAML file."""
    if source in _cache:
        return _cache[source]

    fixtures_dir = _get_fixtures_dir()
    path = fixtures_dir / f"{source}.yaml"
    if not path.exists():
        return {}

    with open(path) as f:
        data = yaml.safe_load(f) or {}
    _cache[source] = data
    return data


def eval_lookup(source: str, query: str) -> str:
    """Look up data from an evaluation data source.

    Args:
        source: The data source to query (e.g. "financials",
            "market", "team", "profile", "brief")
        query: The company domain to look up (e.g. "linear.app")

    Returns:
        Formatted text with the requested data, or an error
        message if the source or company is not found.
    """
    data = _load_source(source)
    if not data:
        return json.dumps(
            {"error": f"Unknown data source: {source}"},
        )

    entry = data.get(query)
    if entry is None:
        return json.dumps(
            {
                "error": (f"No data found for '{query}' in {source}"),
            },
        )

    # Format the entry as readable key-value text
    if isinstance(entry, dict):
        lines = [f"## {source.title()} — {query}", ""]
        for key, value in entry.items():
            label = key.replace("_", " ").title()
            lines.append(f"- **{label}**: {value}")
        return "\n".join(lines)

    return json.dumps(entry)
