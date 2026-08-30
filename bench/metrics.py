"""Unified metric calculations for context graph evaluation v2.

Pure functions -- no IO, no imports from evaluation submodules.
Covers agent effectiveness and latency benchmarks.

Token counts use a word-based approximation (~1.3 tokens/word).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

# -- Token Counting ------------------------------------------


def count_tokens(text: str) -> int:
    """Estimate token count using word-based approximation.

    Rough heuristic: ~1.3 tokens per word for English text.
    """
    if not text:
        return 0
    words = text.split()
    return int(len(words) * 1.3)


# -- Data Classes --------------------------------------------


@dataclass
class ScenarioResult:
    """Results for one scenario x approach x run."""

    scenario_id: str
    approach: str
    run: int
    judge_score: float
    judge_reasoning: str = ""
    output: str = ""
    injection_text: str = ""
    tool_injections: list | None = None
    injection_tokens: int = 0
    seed_query_latency_ms: float = 0.0
    capture_latency_ms: float = 0.0
    query_latency_ms: float = 0.0
    agent_latency_ms: float = 0.0
    judge_latency_ms: float = 0.0
    # Agent LLM usage (from pydantic-ai RunUsage)
    agent_input_tokens: int = 0
    agent_output_tokens: int = 0
    agent_requests: int = 0
    agent_tool_calls: int = 0
    # Approach-side LLM and embedding usage (capture phase)
    capture_llm_in: int = 0
    capture_llm_out: int = 0
    capture_llm_reqs: int = 0
    capture_embed_in: int = 0
    capture_embed_calls: int = 0
    # Approach-side LLM and embedding usage (query phase = Stage 1 only)
    query_llm_in: int = 0
    query_llm_out: int = 0
    query_llm_reqs: int = 0
    query_embed_in: int = 0
    query_embed_calls: int = 0
    # Approach-side Stage 2+ re-retrieval (per-tool-call, during agent loop)
    stage2_llm_in: int = 0
    stage2_llm_out: int = 0
    stage2_llm_reqs: int = 0
    stage2_embed_in: int = 0
    stage2_embed_calls: int = 0


@dataclass
class AggregatedResult:
    """Aggregated results for one scenario x approach."""

    scenario_id: str
    approach: str
    mean_score: float
    scores: list[float] = field(default_factory=list)
    score_range: float = 0.0
    mean_injection_tokens: float = 0.0
    mean_seed_query_latency_ms: float = 0.0
    mean_capture_latency_ms: float = 0.0
    mean_query_latency_ms: float = 0.0
    mean_agent_latency_ms: float = 0.0
    mean_total_latency_ms: float = 0.0
    # Agent LLM usage aggregates
    mean_agent_input_tokens: float = 0.0
    mean_agent_output_tokens: float = 0.0
    mean_agent_requests: float = 0.0
    mean_agent_tool_calls: float = 0.0
    # Approach-side LLM + embedding usage aggregates
    mean_capture_llm_in: float = 0.0
    mean_capture_llm_out: float = 0.0
    mean_capture_llm_reqs: float = 0.0
    mean_capture_embed_in: float = 0.0
    mean_capture_embed_calls: float = 0.0
    mean_query_llm_in: float = 0.0
    mean_query_llm_out: float = 0.0
    mean_query_llm_reqs: float = 0.0
    mean_query_embed_in: float = 0.0
    mean_query_embed_calls: float = 0.0
    mean_stage2_llm_in: float = 0.0
    mean_stage2_llm_out: float = 0.0
    mean_stage2_llm_reqs: float = 0.0
    mean_stage2_embed_in: float = 0.0
    mean_stage2_embed_calls: float = 0.0
    # Efficacy rate: fraction of injected runs that scored > 0
    efficacy_rate: float = 0.0


@dataclass
class LatencyPoint:
    """Latency measurement for one approach at one N."""

    approach: str
    n_corrections: int
    capture_ms: float = 0.0
    query_ms: float = 0.0
    total_ms: float = 0.0


# -- Aggregation ---------------------------------------------


def aggregate_results(
    results: list[ScenarioResult],
) -> list[AggregatedResult]:
    """Group results by (scenario, approach) and compute stats."""
    groups: dict[tuple[str, str], list[ScenarioResult]] = {}
    for r in results:
        key = (r.scenario_id, r.approach)
        groups.setdefault(key, []).append(r)

    aggregated: list[AggregatedResult] = []
    for (sid, approach), group in sorted(groups.items()):
        scores = [r.judge_score for r in group]
        tokens = [r.injection_tokens for r in group]
        sq_lats = [r.seed_query_latency_ms for r in group]
        cap_lats = [r.capture_latency_ms for r in group]
        q_lats = [r.query_latency_ms for r in group]
        ag_lats = [r.agent_latency_ms for r in group]
        total_lats = [r.seed_query_latency_ms + r.agent_latency_ms for r in group]

        in_tok = [r.agent_input_tokens for r in group]
        out_tok = [r.agent_output_tokens for r in group]
        reqs = [r.agent_requests for r in group]
        tcalls = [r.agent_tool_calls for r in group]

        cap_llm_in = [r.capture_llm_in for r in group]
        cap_llm_out = [r.capture_llm_out for r in group]
        cap_llm_reqs = [r.capture_llm_reqs for r in group]
        cap_emb_in = [r.capture_embed_in for r in group]
        cap_emb_calls = [r.capture_embed_calls for r in group]
        q_llm_in = [r.query_llm_in for r in group]
        q_llm_out = [r.query_llm_out for r in group]
        q_llm_reqs = [r.query_llm_reqs for r in group]
        q_emb_in = [r.query_embed_in for r in group]
        q_emb_calls = [r.query_embed_calls for r in group]
        s2_llm_in = [r.stage2_llm_in for r in group]
        s2_llm_out = [r.stage2_llm_out for r in group]
        s2_llm_reqs = [r.stage2_llm_reqs for r in group]
        s2_emb_in = [r.stage2_embed_in for r in group]
        s2_emb_calls = [r.stage2_embed_calls for r in group]

        injected_runs = [r for r in group if r.injection_tokens > 0]
        efficacy_rate = (
            round(sum(1 for r in injected_runs if r.judge_score > 0) / len(injected_runs), 3)
            if injected_runs
            else 0.0
        )

        aggregated.append(
            AggregatedResult(
                scenario_id=sid,
                approach=approach,
                mean_score=round(
                    statistics.mean(scores),
                    3,
                ),
                scores=scores,
                score_range=round(
                    max(scores) - min(scores),
                    3,
                ),
                mean_injection_tokens=round(
                    statistics.mean(tokens),
                    1,
                )
                if tokens
                else 0.0,
                mean_seed_query_latency_ms=round(
                    statistics.mean(sq_lats),
                    0,
                )
                if sq_lats
                else 0.0,
                mean_agent_latency_ms=round(
                    statistics.mean(ag_lats),
                    0,
                )
                if ag_lats
                else 0.0,
                mean_total_latency_ms=round(
                    statistics.mean(total_lats),
                    0,
                )
                if total_lats
                else 0.0,
                mean_agent_input_tokens=round(
                    statistics.mean(in_tok),
                    0,
                )
                if in_tok
                else 0.0,
                mean_agent_output_tokens=round(
                    statistics.mean(out_tok),
                    0,
                )
                if out_tok
                else 0.0,
                mean_agent_requests=round(
                    statistics.mean(reqs),
                    1,
                )
                if reqs
                else 0.0,
                mean_agent_tool_calls=round(
                    statistics.mean(tcalls),
                    1,
                )
                if tcalls
                else 0.0,
                mean_capture_latency_ms=round(statistics.mean(cap_lats), 0) if cap_lats else 0.0,
                mean_query_latency_ms=round(statistics.mean(q_lats), 0) if q_lats else 0.0,
                mean_capture_llm_in=round(statistics.mean(cap_llm_in), 0) if cap_llm_in else 0.0,
                mean_capture_llm_out=round(statistics.mean(cap_llm_out), 0) if cap_llm_out else 0.0,
                mean_capture_llm_reqs=round(statistics.mean(cap_llm_reqs), 2)
                if cap_llm_reqs
                else 0.0,
                mean_capture_embed_in=round(statistics.mean(cap_emb_in), 0) if cap_emb_in else 0.0,
                mean_capture_embed_calls=round(statistics.mean(cap_emb_calls), 2)
                if cap_emb_calls
                else 0.0,
                mean_query_llm_in=round(statistics.mean(q_llm_in), 0) if q_llm_in else 0.0,
                mean_query_llm_out=round(statistics.mean(q_llm_out), 0) if q_llm_out else 0.0,
                mean_query_llm_reqs=round(statistics.mean(q_llm_reqs), 2) if q_llm_reqs else 0.0,
                mean_query_embed_in=round(statistics.mean(q_emb_in), 0) if q_emb_in else 0.0,
                mean_query_embed_calls=round(statistics.mean(q_emb_calls), 2)
                if q_emb_calls
                else 0.0,
                mean_stage2_llm_in=round(statistics.mean(s2_llm_in), 0) if s2_llm_in else 0.0,
                mean_stage2_llm_out=round(statistics.mean(s2_llm_out), 0) if s2_llm_out else 0.0,
                mean_stage2_llm_reqs=round(statistics.mean(s2_llm_reqs), 2) if s2_llm_reqs else 0.0,
                mean_stage2_embed_in=round(statistics.mean(s2_emb_in), 0) if s2_emb_in else 0.0,
                mean_stage2_embed_calls=round(statistics.mean(s2_emb_calls), 2)
                if s2_emb_calls
                else 0.0,
                efficacy_rate=efficacy_rate,
            ),
        )

    return aggregated


# -- Lift Computation ----------------------------------------


def compute_lift(
    control_results: list[AggregatedResult],
    treatment_results: list[AggregatedResult],
) -> dict[str, dict[str, float]]:
    """Compute lift (treatment - control) per scenario.

    Returns:
        {scenario_id: {approach: lift_value}}
    """
    control_by_scenario: dict[str, float] = {}
    for r in control_results:
        control_by_scenario[r.scenario_id] = r.mean_score

    lifts: dict[str, dict[str, float]] = {}
    for r in treatment_results:
        sid = r.scenario_id
        control_score = control_by_scenario.get(sid, 0.0)
        lift = round(r.mean_score - control_score, 3)
        lifts.setdefault(sid, {})[r.approach] = lift

    return lifts


# -- Report Formatting ---------------------------------------


def format_report(
    control: list[AggregatedResult],
    treatments: list[AggregatedResult],
    approaches: list[str],
) -> str:
    """Format the comparison report as text."""
    ctrl_by_sid: dict[str, float] = {}
    for r in control:
        ctrl_by_sid[r.scenario_id] = r.mean_score

    treat_by_key: dict[tuple[str, str], AggregatedResult] = {}
    for r in treatments:
        treat_by_key[(r.scenario_id, r.approach)] = r

    scenario_ids = sorted({r.scenario_id for r in control})

    cols = ["Scenario", "Control", *approaches]
    col_widths = [max(14, len(c) + 2) for c in cols]
    header = "".join(c.ljust(w) for c, w in zip(cols, col_widths))

    lines = [
        "=" * len(header),
        "Evaluation v2 -- Agent Effectiveness",
        "=" * len(header),
        "",
        header,
        "-" * len(header),
    ]

    approach_sums: dict[str, list[float]] = {a: [] for a in approaches}
    control_scores: list[float] = []

    for sid in scenario_ids:
        ctrl = ctrl_by_sid.get(sid, 0.0)
        control_scores.append(ctrl)
        row = [sid[:12].ljust(col_widths[0])]
        row.append(f"{ctrl:.2f}".ljust(col_widths[1]))

        for i, approach in enumerate(approaches):
            agg = treat_by_key.get((sid, approach))
            if agg:
                score = agg.mean_score
                approach_sums[approach].append(score)
                cell = f"{score:.2f}"
            else:
                cell = "\u2014"
            row.append(cell.ljust(col_widths[2 + i]))

        lines.append("".join(row))

    lines.append("-" * len(header))
    avg_row = ["Average".ljust(col_widths[0])]
    ctrl_avg = statistics.mean(control_scores) if control_scores else 0.0
    avg_row.append(f"{ctrl_avg:.2f}".ljust(col_widths[1]))
    for i, approach in enumerate(approaches):
        scores = approach_sums[approach]
        if scores:
            avg = statistics.mean(scores)
            avg_row.append(f"{avg:.2f}".ljust(col_widths[2 + i]))
        else:
            avg_row.append("\u2014".ljust(col_widths[2 + i]))
    lines.append("".join(avg_row))

    lift_row = ["Lift".ljust(col_widths[0])]
    lift_row.append("\u2014".ljust(col_widths[1]))
    for i, approach in enumerate(approaches):
        scores = approach_sums[approach]
        if scores:
            lift = statistics.mean(scores) - ctrl_avg
            lift_row.append(f"{lift:+.2f}".ljust(col_widths[2 + i]))
        else:
            lift_row.append("\u2014".ljust(col_widths[2 + i]))
    lines.append("".join(lift_row))

    lines.append("=" * len(header))

    # Injection tokens summary
    lines.append("")
    lines.append("Injection Tokens (mean per query):")
    for approach in approaches:
        tokens = [
            treat_by_key[(sid, approach)].mean_injection_tokens
            for sid in scenario_ids
            if (sid, approach) in treat_by_key
        ]
        if tokens:
            avg_tok = statistics.mean(tokens)
            lines.append(f"  {approach}: {avg_tok:.0f}")

    # Efficacy rate
    lines.append("")
    lines.append("Efficacy Rate (fraction of injected runs that scored > 0):")
    for approach in approaches:
        aggs = [
            treat_by_key[(sid, approach)] for sid in scenario_ids if (sid, approach) in treat_by_key
        ]
        if aggs:
            er = statistics.mean([a.efficacy_rate for a in aggs])
            lines.append(f"  {approach}: {er:.1%}")

    # Latency summary
    lines.append("")
    lines.append("Latency (mean ms per run):")
    lat_header = "  {:20s} {:>10s} {:>10s} {:>10s} {:>10s}".format(
        "Approach",
        "Capture",
        "Query",
        "Agent",
        "Total",
    )
    lines.append(lat_header)
    for approach in approaches:
        aggs = [
            treat_by_key[(sid, approach)] for sid in scenario_ids if (sid, approach) in treat_by_key
        ]
        if aggs:
            cap = statistics.mean([a.mean_capture_latency_ms for a in aggs])
            q = statistics.mean([a.mean_query_latency_ms for a in aggs])
            ag = statistics.mean([a.mean_agent_latency_ms for a in aggs])
            tot = statistics.mean([a.mean_total_latency_ms for a in aggs])
            lines.append(f"  {approach:20s} {cap:>10.0f} {q:>10.0f} {ag:>10.0f} {tot:>10.0f}")

    ctrl_aggs = [r for r in control if r.mean_agent_latency_ms > 0]
    if ctrl_aggs:
        ctrl_ag = statistics.mean([a.mean_agent_latency_ms for a in ctrl_aggs])
        lines.append(
            "  {:20s} {:>10s} {:>10s} {:>10.0f} {:>10.0f}".format(
                "control", "\u2014", "\u2014", ctrl_ag, ctrl_ag
            )
        )

    # Agent LLM usage summary
    lines.append("")
    lines.append("Agent LLM Usage (mean per run):")
    usage_header = "  {:20s} {:>10s} {:>10s} {:>10s} {:>10s}".format(
        "Approach",
        "In Tok",
        "Out Tok",
        "Requests",
        "Tool Calls",
    )
    lines.append(usage_header)
    for approach in approaches:
        aggs = [
            treat_by_key[(sid, approach)] for sid in scenario_ids if (sid, approach) in treat_by_key
        ]
        if aggs:
            in_t = statistics.mean([a.mean_agent_input_tokens for a in aggs])
            out_t = statistics.mean([a.mean_agent_output_tokens for a in aggs])
            req = statistics.mean([a.mean_agent_requests for a in aggs])
            tc = statistics.mean([a.mean_agent_tool_calls for a in aggs])
            lines.append(f"  {approach:20s} {in_t:>10.0f} {out_t:>10.0f} {req:>10.1f} {tc:>10.1f}")

    ctrl_usage_aggs = [r for r in control if r.mean_agent_input_tokens > 0]
    if ctrl_usage_aggs:
        in_t = statistics.mean([a.mean_agent_input_tokens for a in ctrl_usage_aggs])
        out_t = statistics.mean([a.mean_agent_output_tokens for a in ctrl_usage_aggs])
        req = statistics.mean([a.mean_agent_requests for a in ctrl_usage_aggs])
        tc = statistics.mean([a.mean_agent_tool_calls for a in ctrl_usage_aggs])
        lines.append(
            "  {:20s} {:>10.0f} {:>10.0f} {:>10.1f} {:>10.1f}".format(
                "control", in_t, out_t, req, tc
            )
        )

    # Approach-side LLM + embedding usage (capture + query Stage 1 + Stage 2)
    lines.append("")
    lines.append("Approach LLM Usage (mean per scenario):")
    lines.append("  Q1 = Stage 1 (initial injection before agent runs).")
    lines.append("  Q2 = Stage 2+ (per-tool-call re-retrieval inside agent loop).")
    appr_header = (
        "  {:20s} {:>8s} {:>8s} {:>8s} {:>10s} "
        "{:>8s} {:>8s} {:>8s} {:>8s} "
        "{:>8s} {:>8s} {:>8s} {:>8s}"
    ).format(
        "Approach",
        "Cap In",
        "Cap Out",
        "Cap Rq",
        "Cap Embed",
        "Q1 In",
        "Q1 Out",
        "Q1 Rq",
        "Q1 Emb",
        "Q2 In",
        "Q2 Out",
        "Q2 Rq",
        "Q2 Emb",
    )
    lines.append(appr_header)
    for approach in approaches:
        aggs = [
            treat_by_key[(sid, approach)] for sid in scenario_ids if (sid, approach) in treat_by_key
        ]
        if aggs:
            cap_in = statistics.mean([a.mean_capture_llm_in for a in aggs])
            cap_out = statistics.mean([a.mean_capture_llm_out for a in aggs])
            cap_reqs = statistics.mean([a.mean_capture_llm_reqs for a in aggs])
            cap_emb = statistics.mean([a.mean_capture_embed_in for a in aggs])
            q1_in = statistics.mean([a.mean_query_llm_in for a in aggs])
            q1_out = statistics.mean([a.mean_query_llm_out for a in aggs])
            q1_reqs = statistics.mean([a.mean_query_llm_reqs for a in aggs])
            q1_emb = statistics.mean([a.mean_query_embed_in for a in aggs])
            q2_in = statistics.mean([a.mean_stage2_llm_in for a in aggs])
            q2_out = statistics.mean([a.mean_stage2_llm_out for a in aggs])
            q2_reqs = statistics.mean([a.mean_stage2_llm_reqs for a in aggs])
            q2_emb = statistics.mean([a.mean_stage2_embed_in for a in aggs])
            lines.append(
                f"  {approach:20s} {cap_in:>8.0f} {cap_out:>8.0f} "
                f"{cap_reqs:>8.1f} {cap_emb:>10.0f} "
                f"{q1_in:>8.0f} {q1_out:>8.0f} {q1_reqs:>8.1f} {q1_emb:>8.0f} "
                f"{q2_in:>8.0f} {q2_out:>8.0f} {q2_reqs:>8.1f} {q2_emb:>8.0f}"
            )

    # Total tokens per scenario: split into LLM vs Embed (different $ cost per token)
    lines.append("")
    lines.append("Total Tokens (mean per scenario, LLM vs Embed):")
    lines.append("  LLM = capture LLM + query LLM (Stage 1 + Stage 2) + agent in/out.")
    lines.append("  Embed = capture embed + query embed (Stage 1 + Stage 2).")
    total_header = "  {:20s} {:>12s} {:>12s} {:>14s}".format(
        "Approach", "LLM Tok", "Embed Tok", "Total Tok"
    )
    lines.append(total_header)
    for approach in approaches:
        aggs = [
            treat_by_key[(sid, approach)] for sid in scenario_ids if (sid, approach) in treat_by_key
        ]
        if aggs:
            llm_tok = statistics.mean(
                [
                    a.mean_capture_llm_in
                    + a.mean_capture_llm_out
                    + a.mean_query_llm_in
                    + a.mean_query_llm_out
                    + a.mean_stage2_llm_in
                    + a.mean_stage2_llm_out
                    + a.mean_agent_input_tokens
                    + a.mean_agent_output_tokens
                    for a in aggs
                ]
            )
            emb_tok = statistics.mean(
                [
                    a.mean_capture_embed_in + a.mean_query_embed_in + a.mean_stage2_embed_in
                    for a in aggs
                ]
            )
            total = llm_tok + emb_tok
            lines.append(f"  {approach:20s} {llm_tok:>12.0f} {emb_tok:>12.0f} {total:>14.0f}")

    return "\n".join(lines)


def format_latency_report(
    points: list[LatencyPoint],
    approaches: list[str],
) -> str:
    """Format latency benchmark results as a text table."""
    by_n: dict[int, dict[str, LatencyPoint]] = {}
    for p in points:
        by_n.setdefault(p.n_corrections, {})[p.approach] = p

    n_values = sorted(by_n.keys())
    if not n_values:
        return "(no latency data)"

    lines = [
        "=" * 70,
        "Latency Benchmark",
        "=" * 70,
        "",
    ]

    header = f"  {'N':>6s}"
    for a in approaches:
        header += f"  {a:>14s}"

    for metric in ("Capture", "Query", "Total"):
        lines.append(f"{metric} Latency (ms):")
        lines.append(header)
        lines.append("  " + "-" * (6 + 16 * len(approaches)))

        for n in n_values:
            row = f"  {n:>6d}"
            for a in approaches:
                lp: LatencyPoint | None = by_n[n].get(a)
                if lp:
                    val = getattr(
                        lp,
                        f"{metric.lower()}_ms",
                    )
                    row += f"  {val:>14.0f}"
                else:
                    row += f"  {'\u2014':>14s}"
            lines.append(row)

        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)
