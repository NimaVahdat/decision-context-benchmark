"""Customer support lookup tool — returns canned data from YAML fixtures.

Mirrors eval_lookup but for support scenarios.
Sources: lookup_account, check_order_status, search_knowledge_base,
         search_by_email, escalation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

_DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

_cache: dict[str, dict] = {}


def _get_fixtures_dir() -> Path:
    override = os.environ.get("EVAL_FIXTURES_DIR")
    if override:
        return Path(override)
    return _DEFAULT_FIXTURES_DIR


def _load_source(source: str) -> dict:
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


def support_lookup(source: str, query: str) -> str:
    """Look up customer support data.

    Args:
        source: Data source — one of:
            "lookup_account"       — account details, tier, status
            "check_order_status"   — recent orders and history
            "search_knowledge_base" — KB articles for the ticket topic
            "search_by_email"      — find account when account_id unavailable
            "escalation"           — escalate ticket to tier-2 support
        query: Company domain (e.g. "acme-corp.io")

    Returns:
        Formatted data or error message if source/company not found.
    """
    valid = {
        "lookup_account",
        "check_order_status",
        "search_knowledge_base",
        "search_by_email",
        "escalation",
    }
    if source not in valid:
        return json.dumps({"error": f"Unknown source: {source}. Valid: {sorted(valid)}"})

    data = _load_source(source)
    if not data:
        return json.dumps({"error": f"Source unavailable: {source}"})

    entry = data.get(query)
    if entry is None:
        return json.dumps({"error": f"No data found for '{query}' in {source}"})

    if isinstance(entry, dict):
        if "error" in entry:
            return json.dumps(entry)
        lines = [f"## {source.replace('_', ' ').title()} — {query}", ""]
        for key, value in entry.items():
            label = key.replace("_", " ").title()
            lines.append(f"- **{label}**: {value}")
        return "\n".join(lines)

    return json.dumps(entry)
