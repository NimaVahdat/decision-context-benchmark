"""Simulated async data lookup for retry scenarios.

Primary source (source="premium") behaves like BrightData:
returns "processing" status for unknown companies, never
resolves. The agent should learn to stop retrying and use
the fallback source (source="basic") instead.

For known companies, premium returns data immediately.
"""

from __future__ import annotations

import json

from bench.tools.eval_lookup import eval_lookup as _real_lookup

# Track call count per (source, query) to simulate retries
_call_counts: dict[str, int] = {}


def reset_counts() -> None:
    """Reset call counts between runs."""
    _call_counts.clear()


def async_lookup(source: str, query: str) -> str:
    """Look up data with async/retry simulation.

    Args:
        source: "premium" (preferred, may be processing)
                or "basic" (fallback, always available).
        query: Company domain.

    Returns:
        Data if available, or processing status if still
        fetching.
    """
    # Basic source always works — tries all sources including profile
    if source == "basic":
        result_parts = []
        for real_source in ["financials", "market", "team", "profile"]:
            data = _real_lookup(real_source, query)
            if "error" not in data:
                result_parts.append(data[:500])
        if result_parts:
            return "\n\n".join(result_parts)
        return json.dumps({"error": f"No data found for '{query}'"})

    # Premium source — known companies return immediately
    real_data = _real_lookup("financials", query)
    if "error" not in real_data:
        return real_data

    # Unknown companies: always "processing"
    key = f"{source}:{query}"
    _call_counts[key] = _call_counts.get(key, 0) + 1
    count = _call_counts[key]

    return json.dumps(
        {
            "status": "processing",
            "message": (
                f"Data collection for '{query}' is in progress. "
                f"Attempt {count}. The data is being fetched from "
                f"external sources and may take a few moments. "
                f"Please retry shortly."
            ),
            "retry_after_seconds": 5,
            "estimated_completion": "soon",
        }
    )
