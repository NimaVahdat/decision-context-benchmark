"""Bench-side proxy to approach usage accumulators.

The bench orchestrator records per-scenario LLM and embedding token
counts for two phases: ``capture`` (offline ingestion of seed traces)
and ``query`` (online retrieval and rule injection). The actual
accumulators live in the adopter's approach package; this module
gives the orchestrator a single place to read and reset them, with
lazy imports so the bench still runs when no approach package is
installed.

To wire an adopter package into the bench, set
``BENCH_USAGE_MODULES`` to a comma-separated list of dotted import
paths, e.g.::

    export BENCH_USAGE_MODULES="my_approaches.shared.usage,other_pkg.usage"

Each listed module must expose the following names:

* ``set_phase(phase: str) -> None``
* ``reset_all() -> None``
* ``reset_capture_usage() -> None``
* ``reset_query_usage() -> None``
* ``get_capture_usage() -> dict[str, int]``
* ``get_query_usage() -> dict[str, int]``

When multiple modules are listed, their counters are summed. If
``BENCH_USAGE_MODULES`` is unset or no listed module can be imported,
``get_capture()`` and ``get_query()`` return zeroed dictionaries and
the bench continues to run; injection-token attribution simply shows
zero for that approach.
"""

from __future__ import annotations

import contextlib
import importlib
import os
from typing import Any

_EMPTY: dict[str, int] = {
    "llm_in": 0,
    "llm_out": 0,
    "llm_reqs": 0,
    "embed_in": 0,
    "embed_calls": 0,
}

_MODS_CACHE: list[Any] | None = None


def _mods() -> list[Any]:
    """Return all configured usage modules. Cached after first call."""
    global _MODS_CACHE
    if _MODS_CACHE is not None:
        return _MODS_CACHE

    paths = os.environ.get("BENCH_USAGE_MODULES", "")
    mods: list[Any] = []
    for raw in paths.split(","):
        dotted = raw.strip()
        if not dotted:
            continue
        with contextlib.suppress(Exception):
            mods.append(importlib.import_module(dotted))
    _MODS_CACHE = mods
    return mods


def set_phase(phase: str) -> None:
    for mod in _mods():
        mod.set_phase(phase)


def reset_all() -> None:
    for mod in _mods():
        mod.reset_all()


def reset_capture() -> None:
    for mod in _mods():
        mod.reset_capture_usage()


def reset_query() -> None:
    for mod in _mods():
        mod.reset_query_usage()


def _sum_dicts(*dicts: dict[str, int]) -> dict[str, int]:
    result = dict(_EMPTY)
    for d in dicts:
        for k in result:
            result[k] += d.get(k, 0)
    return result


def get_capture() -> dict[str, int]:
    mods = _mods()
    if not mods:
        return dict(_EMPTY)
    return _sum_dicts(*(mod.get_capture_usage() for mod in mods))


def get_query() -> dict[str, int]:
    mods = _mods()
    if not mods:
        return dict(_EMPTY)
    return _sum_dicts(*(mod.get_query_usage() for mod in mods))
