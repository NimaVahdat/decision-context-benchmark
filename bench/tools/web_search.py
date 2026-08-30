"""Simulated web_search tool for evaluation.

Returns different quality results depending on query pattern.
Only ONE query pattern consistently returns 5 good results.
The agent has to learn which pattern works from experience.

Query patterns and their result quality:
- Company name only ("delve") → 1-2 generic results
- Domain ("delve.co") → 2-3 results, some generic
- Name + "funding" → 5 good results (THE WINNING PATTERN)
- Name + "team" → 1-2 results
- Name + "market" → 2-3 results
- Name + "revenue" → 0-1 results (too specific, nothing found)
- Industry keywords → 0-1 results (too broad)
"""

from __future__ import annotations

import json

# Company data for generating realistic results
_COMPANIES = {
    "delve.co": {
        "name": "Delve",
        "industry": "analytics",
        "funding_results": [
            "Delve raises $15M Series A led by Sequoia Capital for AI-native analytics platform",
            "Delve.co: YC-backed analytics startup hits $4.2M ARR with 180% growth",
            "Sequoia leads $15M round in Delve, AI analytics platform seeing rapid enterprise adoption",
            "Delve founding team raises seed from Y Combinator, pivots to NL query analytics",
            "Analytics startup Delve reports 125% net dollar retention, eyes Series B",
        ],
        "generic_results": [
            "Delve - Homepage",
            "Delve Analytics | LinkedIn",
        ],
        "team_results": [
            "Delve.co team page - 35 employees",
            "Delve CTO profile on LinkedIn",
        ],
        "market_results": [
            "Self-serve analytics market growing 28% CAGR",
            "Business intelligence market size $12B by 2028",
            "Top 10 analytics platforms compared",
        ],
    },
    "linear.app": {
        "name": "Linear",
        "industry": "project management",
        "funding_results": [
            "Linear raises $35M Series B at $400M valuation for modern issue tracking",
            "Linear.app: bootstrapped to $25M ARR before raising Series A from Accel",
            "Accel leads $25M Series A in Linear, project management tool with 120% growth",
            "Linear founding team includes ex-Uber and ex-Coinbase engineers",
            "Linear reports 140% NRR, 2000+ paying teams, eyes profitability",
        ],
        "generic_results": [
            "Linear - The issue tracking tool you'll enjoy using",
            "Linear App | LinkedIn",
        ],
        "team_results": [
            "Linear team - 85 employees across SF and Helsinki",
        ],
        "market_results": [
            "Project management software market $8B",
            "Jira vs Linear vs Asana comparison 2025",
        ],
    },
    "meridian.bio": {
        "name": "Meridian Bio",
        "industry": "biotech",
        "funding_results": [
            "Meridian Bio raises $15M Series A from a16z Bio + Health for computational biology platform",
            "Meridian.bio: pharma partnerships drive $8M ARR with 120% growth in biotech-SaaS",
            "a16z Bio leads Series A in Meridian Bio, computational biology startup",
            "Meridian Bio receives $2M NIH SBIR grant for protein folding research",
            "Biotech-SaaS hybrid Meridian Bio reports milestone-based revenue of $8M ARR",
        ],
        "generic_results": [
            "Meridian Bio - Computational Biology Platform",
            "Meridian Bio | Crunchbase",
        ],
        "team_results": [
            "Meridian Bio VP hired from NREL",
        ],
        "market_results": [
            "Computational biology market opportunities",
            "Biotech SaaS companies to watch",
        ],
    },
}

# Default for unknown companies
_DEFAULT = {
    "name": "Unknown",
    "industry": "technology",
    "funding_results": [],
    "generic_results": [
        "No relevant results found",
    ],
    "team_results": [],
    "market_results": [],
}


def web_search(query: str) -> str:
    """Search for information about a company.

    Args:
        query: Search query string.

    Returns:
        JSON string with search results. Each result has
        a title and relevance score (0-1).
    """
    query_lower = query.lower().strip()

    # Detect company from query
    company_data = _DEFAULT
    for domain, data in _COMPANIES.items():
        name_lower = str(data["name"]).lower()
        if name_lower in query_lower or domain in query_lower:
            company_data = data
            break

    # Detect query pattern
    pattern = _classify_query(query_lower, company_data)

    # Generate results based on pattern
    results = _generate_results(pattern, company_data)

    return json.dumps(
        {
            "query": query,
            "results_count": len(results),
            "results": results,
        },
        indent=2,
    )


def _classify_query(query: str, data: dict) -> str:
    """Classify the query pattern."""
    name = data["name"].lower()

    # Check for the winning pattern: name + "funding"
    if "funding" in query or "raised" in query or "investor" in query:
        return "funding"

    # Check for specific topic queries
    if "team" in query or "hiring" in query or "employee" in query:
        return "team"
    if "market" in query or "industry" in query or "competitor" in query:
        return "market"
    if "revenue" in query or "arr" in query or "financial" in query:
        return "revenue"  # too specific, bad results

    # Check for domain-only query
    if ".co" in query or ".app" in query or ".bio" in query or ".io" in query:
        return "domain"

    # Check for name-only query
    if name in query and len(query.split()) <= 3:
        return "name_only"

    # Broad industry query
    return "broad"


def _generate_results(
    pattern: str,
    data: dict,
) -> list[dict]:
    """Generate results based on query pattern."""
    match pattern:
        case "funding":
            # THE WINNING PATTERN — 5 good results
            return [{"title": r, "relevance": 0.9} for r in data["funding_results"]]

        case "name_only":
            # 1-2 generic results
            return [{"title": r, "relevance": 0.3} for r in data["generic_results"][:2]]

        case "domain":
            # 2-3 mixed results
            results = [{"title": r, "relevance": 0.3} for r in data["generic_results"][:1]]
            results.extend([{"title": r, "relevance": 0.6} for r in data["market_results"][:2]])
            return results

        case "team":
            # 1-2 results
            return [{"title": r, "relevance": 0.7} for r in data["team_results"][:2]]

        case "market":
            # 2-3 results
            return [{"title": r, "relevance": 0.6} for r in data["market_results"][:3]]

        case "revenue":
            # 0-1 results — too specific
            return [{"title": "No specific revenue data found", "relevance": 0.1}]

        case "broad":
            # 0-1 results — too vague
            return [{"title": "Too many results, please narrow your search", "relevance": 0.1}]

        case _:
            return []
