"""LLM-as-judge for context-graph evaluation v2.

Uses a strong model to score whether an agent's output incorporates a
specific correction, based on a rubric.

Two code paths:

* **OpenAI judge models** (provider ``openai`` or a bare model name)
  use a raw ``AsyncOpenAI`` chat-completions call with a prompt that
  templates each rubric criterion as an explicit JSON key. This
  reproduces the original (pre-refactor) judge exactly, which the
  paper results were generated with. The templated keys both pin the
  score-dict keys and keep the model's scoring calibration stable.

* **Other providers** (e.g. ``vertexai-anthropic:...``) fall back to
  pydantic-ai with an ordered-list output schema, so the judge stays
  provider-pluggable.

Override the judge via ``BENCH_JUDGE_MODEL`` (e.g. ``openai:gpt-4.1``,
``vertexai-anthropic:claude-opus-4-7``).
"""

from __future__ import annotations

import json
import logging
import os
import textwrap
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from bench.scenarios.models import (
    RubricItem,
    Scenario,
)

logger = logging.getLogger(__name__)

JUDGE_MODEL = os.environ.get("BENCH_JUDGE_MODEL", "openai:gpt-4.1")


class JudgeRawOutput(BaseModel):
    """Ordered-list output schema for the pydantic-ai fallback path."""

    scores: list[float] = Field(
        default_factory=list,
        description=(
            "One score in [0.0, 1.0] per rubric criterion, in the "
            "exact order the rubric is presented."
        ),
    )
    reasoning: str = Field(
        default="",
        description="Brief natural-language justification.",
    )


@dataclass
class JudgeResult:
    """Result from the LLM judge."""

    scores: dict[str, float] = field(
        default_factory=dict,
    )
    reasoning: str = ""
    weighted_score: float = 0.0


def _format_rubric(rubric: list[RubricItem]) -> str:
    """Format rubric items for the judge prompt."""
    lines = []
    for i, item in enumerate(rubric, 1):
        mode_tag = " [NEGATIVE -- score 1.0 if ABSENT]" if item.mode == "negative" else ""
        lines.append(f"{i}. {item.criterion} (weight: {item.weight}){mode_tag}")
    return "\n".join(lines)


def _weighted(scores: dict[str, float], rubric: list[RubricItem]) -> float:
    """Compute the rubric-weighted score in [0, 1]."""
    total_weight = sum(r.weight for r in rubric)
    weighted = 0.0
    for item in rubric:
        weighted += scores.get(item.criterion, 0.0) * item.weight
    if total_weight > 0:
        weighted /= total_weight
    return round(weighted, 3)


def _is_openai_judge(model_string: str) -> bool:
    """OpenAI judge models keep the original raw-chat-completions path
    so the paper's scoring calibration is reproduced exactly."""
    return ":" not in model_string or model_string.startswith("openai:")


def _openai_model_name(model_string: str) -> str:
    """Strip a leading ``openai:`` provider prefix if present."""
    if model_string.startswith("openai:"):
        return model_string.split(":", 1)[1]
    return model_string


async def _judge_openai(
    response: str,
    correction: str,
    rubric: list[RubricItem],
    model_name: str,
) -> JudgeResult:
    """Original judge implementation (verbatim behavior).

    Raw ``AsyncOpenAI`` chat-completions call whose prompt templates
    each rubric criterion as a JSON key. This is what the paper runs
    used; do not "modernize" it without re-baselining every saved
    result, because the scoring calibration is sensitive to the prompt
    shape (see the judge-drift investigation in the project history).
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    rubric_text = _format_rubric(rubric)
    criteria_names = [item.criterion for item in rubric]

    prompt = textwrap.dedent(f"""\
        You are evaluating whether an AI response
        incorporates a specific correction from a user.

        CORRECTION THE USER PREVIOUSLY GAVE:
        "{correction}"

        RUBRIC (score each criterion):
        {rubric_text}

        RESPONSE TO EVALUATE:
        ---
        {response}
        ---

        For each rubric criterion, assign a score:
        - 1.0: The criterion is clearly satisfied
        - 0.5: Partially satisfied or ambiguous
        - 0.0: Not satisfied at all

        For criteria marked [NEGATIVE], REVERSE the
        scoring: 1.0 if the described behavior is
        ABSENT from the response, 0.0 if it IS present,
        0.5 if ambiguous.

        Return ONLY valid JSON with no other text:
        {{
          "scores": {{{", ".join(f'"{c}": <score>' for c in criteria_names)}}},
          "reasoning": "<brief explanation>"
        }}""")

    try:
        resp = await client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": ("You are a precise evaluation judge. Return only valid JSON."),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
            temperature=0,
        )
        raw = resp.choices[0].message.content or "{}"

        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines)

        parsed = json.loads(raw)
        scores = parsed.get("scores", {})
        reasoning = parsed.get("reasoning", "")

        return JudgeResult(
            scores=scores,
            reasoning=reasoning,
            weighted_score=_weighted(scores, rubric),
        )
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("Judge parse error: %s", exc)
        return JudgeResult(reasoning=f"Parse error: {exc}", weighted_score=0.0)
    except Exception as exc:
        logger.error("Judge call failed: %s", exc)
        return JudgeResult(reasoning=f"Judge error: {exc}", weighted_score=0.0)


async def _judge_pydantic_ai(
    response: str,
    correction: str,
    rubric: list[RubricItem],
    model_string: str,
) -> JudgeResult:
    """Provider-agnostic fallback for non-OpenAI judge models.

    Uses pydantic-ai with an ordered-list score schema (the model
    paraphrases criterion text when asked for dict keys, so we match
    by position instead). Calibration may differ slightly from the
    OpenAI path; use an OpenAI judge to reproduce paper numbers.
    """
    from pydantic_ai import Agent

    from bench.core.config import _resolve_model

    rubric_text = _format_rubric(rubric)
    prompt = textwrap.dedent(f"""\
        You are evaluating whether an AI response
        incorporates a specific correction from a user.

        CORRECTION THE USER PREVIOUSLY GAVE:
        "{correction}"

        RUBRIC (score each criterion):
        {rubric_text}

        RESPONSE TO EVALUATE:
        ---
        {response}
        ---

        For each rubric criterion, assign a score:
        - 1.0: The criterion is clearly satisfied
        - 0.5: Partially satisfied or ambiguous
        - 0.0: Not satisfied at all

        For criteria marked [NEGATIVE], REVERSE the
        scoring: 1.0 if the described behavior is
        ABSENT from the response, 0.0 if it IS present,
        0.5 if ambiguous.

        Return a JSON object with two fields:
        - "scores": a list of floats with EXACTLY {len(rubric)} entries,
          one per rubric criterion in the order shown above.
        - "reasoning": a brief natural-language explanation.""")

    try:
        agent: Agent[None, JudgeRawOutput] = Agent(
            model=_resolve_model(model_string),
            output_type=JudgeRawOutput,
            system_prompt="You are a precise evaluation judge.",
            model_settings={"temperature": 0},
        )
        result = await agent.run(prompt)
        score_list = result.output.scores
        scores: dict[str, float] = {}
        for i, item in enumerate(rubric):
            scores[item.criterion] = score_list[i] if i < len(score_list) else 0.0
        return JudgeResult(
            scores=scores,
            reasoning=result.output.reasoning,
            weighted_score=_weighted(scores, rubric),
        )
    except Exception as exc:
        logger.error("Judge call failed: %s", exc)
        return JudgeResult(reasoning=f"Judge error: {exc}", weighted_score=0.0)


async def judge_output(
    response: str,
    correction: str,
    rubric: list[RubricItem],
    model: str | None = None,
) -> JudgeResult:
    """Judge whether a response incorporates a correction.

    Args:
        response: The agent's output to evaluate.
        correction: The correction that should be applied.
        rubric: Criteria to score against.
        model: provider:model string. Defaults to ``JUDGE_MODEL``
            (which honors the ``BENCH_JUDGE_MODEL`` env var).

    Returns:
        JudgeResult with per-criterion scores and reasoning.
    """
    model_string = model or JUDGE_MODEL
    if _is_openai_judge(model_string):
        return await _judge_openai(response, correction, rubric, _openai_model_name(model_string))
    return await _judge_pydantic_ai(response, correction, rubric, model_string)


async def judge_scenario(
    response: str,
    scenario: Scenario,
    model: str | None = None,
) -> JudgeResult:
    """Judge a response against a scenario's rubric.

    Builds a composite correction string from all seed
    traces that contain corrections (those with a
    parent_index).
    """
    corrections: list[str] = []
    for seed in scenario.seed_traces:
        if seed.parent_index is not None:
            corrections.append(seed.message_content)

    if not corrections:
        correction_text = "(no correction applied)"
    elif len(corrections) == 1:
        correction_text = corrections[0]
    else:
        numbered = [f"{i}. {c}" for i, c in enumerate(corrections, 1)]
        correction_text = "Multiple corrections applied:\n" + "\n".join(numbered)

    return await judge_output(
        response=response,
        correction=correction_text,
        rubric=scenario.rubric,
        model=model,
    )
