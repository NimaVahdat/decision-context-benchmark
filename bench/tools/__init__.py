"""Simulated tools for benchmark evaluation.

eval_lookup: Company data lookup from YAML fixtures
async_lookup: Async/retry simulation (premium vs basic)
web_search: Web search simulation with query pattern matching
"""

from bench.tools.async_lookup import async_lookup
from bench.tools.eval_lookup import eval_lookup
from bench.tools.web_search import web_search

__all__ = ["async_lookup", "eval_lookup", "web_search"]
