"""Configuration constants and helpers."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# -- Constants -----------------------------------------------

EVAL_DIR = Path(__file__).resolve().parent.parent
# ``BENCH_RESULTS_DIR`` lets each process write to its own results
# folder. Used to run approach groups in parallel without clobbering
# the shared control/report/full_results files.
RESULTS_DIR = Path(os.environ.get("BENCH_RESULTS_DIR", str(EVAL_DIR / "results")))
SKILLS_DIR = EVAL_DIR / "skills"
FIXTURES_DIR = EVAL_DIR / "fixtures"


# -- Model Resolution ----------------------------------------


def _resolve_model(
    model_string: str,
    provider_config: dict[str, Any] | None = None,
) -> str | Any:
    """Resolve a provider:model string to a pydantic-ai model."""
    provider_config = provider_config or {}

    if ":" not in model_string:
        return f"openai:{model_string}"

    provider, model_name = model_string.split(":", 1)
    config = provider_config.get(provider, {})

    if provider == "openai":
        # Return a concrete Model instance so callers that bypass
        # ``pydantic_ai.Agent`` and invoke ``model.request()``
        # directly (notably ``bench.core.agent_runner``) work the
        # same on OpenAI as on the Vertex providers.
        from pydantic_ai.models.openai import OpenAIModel

        return OpenAIModel(model_name, provider="openai")

    if provider == "vertexai-anthropic":
        from anthropic import AsyncAnthropicVertex
        from pydantic_ai.models.anthropic import (
            AnthropicModel,
        )
        from pydantic_ai.providers.anthropic import (
            AnthropicProvider,
        )

        project = (
            config.get("project")
            or os.environ.get("GCP_PROJECT_ID")
            or os.environ.get("GOOGLE_CLOUD_PROJECT")
        )
        location = (
            config.get("location")
            or os.environ.get("GCP_LOCATION_ANTHROPIC")
            or os.environ.get("GCP_LOCATION")
            or "us-central1"
        )

        vertex_client = AsyncAnthropicVertex(
            region=location,
            project_id=project or "",
        )
        prov = AnthropicProvider(
            anthropic_client=vertex_client,
        )
        return AnthropicModel(model_name, provider=prov)

    if provider in ("vertexai", "vertexai-garden"):
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import (
            GoogleProvider,
        )

        project = (
            config.get("project")
            or os.environ.get("GCP_PROJECT_ID")
            or os.environ.get("GOOGLE_CLOUD_PROJECT")
        )
        location = config.get("location", "us-central1")
        os.environ.setdefault(
            "GOOGLE_CLOUD_PROJECT",
            project or "",
        )
        os.environ.setdefault(
            "GOOGLE_CLOUD_LOCATION",
            location,
        )
        google_prov = GoogleProvider(vertexai=True)
        return GoogleModel(model_name, provider=google_prov)

    raise ValueError(f"Unknown provider: {provider}")


# -- Infra Checks -------------------------------------------


def _check_port(host: str, port: int) -> bool:
    """Check if a TCP port is reachable."""
    import socket

    try:
        sock = socket.create_connection(
            (host, port),
            timeout=2,
        )
        sock.close()
        return True
    except (OSError, ConnectionRefusedError):
        return False
