"""Mocked-tool harness shared by the agent run loops.

The benchmark's tools (eval_lookup, async_lookup, security_lookup,
support_lookup, web_search) are deterministic fixtures. This module
owns the machinery the manual run loop needs to expose them to a
pydantic-ai model and execute the calls:

* ``_clear_tool_caches`` — reset per-scenario tool state
* ``_build_tool_defs``  — pydantic-ai ``ToolDefinition``s whose
  descriptions carry the real docstrings (so the model uses valid
  ``source`` values instead of inventing them)
* ``_execute_tool``     — dispatch a tool call to its fixture
* ``_parse_tool_args``  — normalize tool-call args to a dict

Extracted so both ``bench.core.agent_runner`` (the unified channel
runner) and any other loop can reuse it without duplication.
"""

from __future__ import annotations

from typing import Any


def _clear_tool_caches(skill_slug: str) -> None:
    try:
        from bench.tools.eval_lookup import _cache

        _cache.clear()
    except Exception:
        pass
    if "async" in skill_slug:
        try:
            from bench.tools.async_lookup import reset_counts

            reset_counts()
        except Exception:
            pass
    if "security" in skill_slug:
        try:
            from bench.tools.security_lookup import _cache as _sc

            _sc.clear()
        except Exception:
            pass
    if "support" in skill_slug:
        try:
            from bench.tools.support_lookup import _cache as _supc

            _supc.clear()
        except Exception:
            pass


def _execute_tool(name: str, args: dict, skill_slug: str) -> str:
    source = args.get("source", "")
    query = args.get("query", "")
    if name == "eval_lookup":
        from bench.tools.eval_lookup import eval_lookup

        return eval_lookup(source, query)
    if name == "async_lookup":
        from bench.tools.async_lookup import async_lookup

        return async_lookup(source, query)
    if name == "security_lookup":
        from bench.tools.security_lookup import security_lookup

        return security_lookup(source, query)
    if name == "support_lookup":
        from bench.tools.support_lookup import support_lookup

        return support_lookup(source, query)
    if name == "web_search":
        from bench.tools.web_search import web_search

        return web_search(query)
    return f"Unknown tool: {name}"


def _build_tool_defs(skill_slug: str):
    """Build pydantic-ai tool definitions whose descriptions come from
    the underlying tool functions' real docstrings, so the model sees
    the valid ``source`` parameter values."""
    from pydantic_ai.tools import ToolDefinition

    spec_two = {
        "type": "object",
        "properties": {
            "source": {"type": "string"},
            "query": {"type": "string"},
        },
        "required": ["source", "query"],
    }
    spec_query = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
        },
        "required": ["query"],
    }

    from bench.tools.eval_lookup import eval_lookup

    eval_desc = (eval_lookup.__doc__ or "").strip()

    defs = [
        ToolDefinition(
            name="eval_lookup",
            parameters_json_schema=spec_two,
            description=eval_desc,
        ),
    ]
    if "async" in skill_slug:
        from bench.tools.async_lookup import async_lookup

        defs.append(
            ToolDefinition(
                name="async_lookup",
                parameters_json_schema=spec_two,
                description=(async_lookup.__doc__ or "").strip()
                or (
                    "Look up company data. source='premium' (preferred, may "
                    "need retries) or source='basic' (fallback, always "
                    "available)."
                ),
            )
        )
    if "security" in skill_slug:
        from bench.tools.security_lookup import security_lookup

        defs.append(
            ToolDefinition(
                name="security_lookup",
                parameters_json_schema=spec_two,
                description=(security_lookup.__doc__ or "").strip()
                or (
                    "Look up security incident data. source: 'network', "
                    "'auth', 'vulnerabilities', or 'behavior'. query: alert ID."
                ),
            )
        )
    if "support" in skill_slug:
        from bench.tools.support_lookup import support_lookup

        defs.append(
            ToolDefinition(
                name="support_lookup",
                parameters_json_schema=spec_two,
                description=(support_lookup.__doc__ or "").strip()
                or ("Look up support ticket data."),
            )
        )
    if "researcher" in skill_slug:
        from bench.tools.web_search import web_search

        defs.append(
            ToolDefinition(
                name="web_search",
                parameters_json_schema=spec_query,
                description=(web_search.__doc__ or "").strip()
                or ("Search for information about a company. Returns JSON with search results."),
            )
        )
    return defs


def _parse_tool_args(args: Any) -> dict[str, Any]:
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        import json

        try:
            parsed = json.loads(args)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}
