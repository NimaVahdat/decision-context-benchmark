"""Skill prompt and model loading."""

from __future__ import annotations

from bench.core.config import SKILLS_DIR


def _load_skill_prompt(skill_slug: str) -> str:
    """Load the system prompt from a skill markdown."""
    path = SKILLS_DIR / f"{skill_slug}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"Skill not found: {path}",
        )

    text = path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


def _load_skill_model(skill_slug: str) -> str:
    """Read the model from a skill's YAML frontmatter.

    If the `BENCH_AGENT_MODEL` env var is set, it overrides the skill's
    frontmatter model for every skill. Use this to sweep the bench
    across model backbones without editing the skill files. Format is
    pydantic-ai's `provider:model` string, e.g.:
        export BENCH_AGENT_MODEL="openai:gpt-4.1"
        export BENCH_AGENT_MODEL="vertexai-anthropic:claude-sonnet-4-6@20251001"
    """
    import os

    import yaml as _yaml

    override = os.environ.get("BENCH_AGENT_MODEL")
    if override:
        return override

    path = SKILLS_DIR / f"{skill_slug}.md"
    text = path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta = _yaml.safe_load(parts[1]) or {}
            return str(meta.get("model", ""))
    return ""
