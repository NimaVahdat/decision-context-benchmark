# Decision Context Bench

**A benchmark for behavioral memory: does an agent actually *apply* what it was corrected on last time?**

Most "agent memory" evaluations test recall — can the system fetch a fact it stored? Decision Context Bench tests something harder and more useful: when a human corrects an agent ("flag runway risk at the top", "escalate billing tickets, skip the KB"), does a memory system make the agent **change its behavior** on a new, unseen task — without being told again?

Each scenario pairs a **control** run (no memory) that should score ≈0 — proving the agent doesn't already do the right thing — against a **treatment** run where your memory approach injects what it learned. The lift between them is the signal.

```
seed traces (past runs + human corrections)
        │  capture
        ▼
   your memory approach ──inject──▶ agent runs an unseen task ──▶ LLM judge scores it
        ▲                                                              │
        └────────────── control = same task, no memory  ──────────────┘
                          lift = treatment − control
```

- **71 scenarios** across **9 behavioral dimensions** (recall, temporal coherence, scope precision, conditional activation, …).
- **Approach-agnostic**: bring any memory system by implementing one small Python Protocol.
- **Provider-agnostic**: agent and judge run through `pydantic-ai` (OpenAI, Anthropic, Vertex/Gemini).
- **Byte-level prompt control**: you decide exactly what text is injected and into which channel.

---

## Quickstart

```bash
# 1. Install the bench (core has no DB or approach dependencies)
uv sync

# 2. Credentials for the providers you'll use (judge defaults to openai:gpt-4.1)
export OPENAI_API_KEY=...                 # OpenAI (and the default judge)
export EVAL_FIXTURES_DIR=bench/fixtures   # mock-tool data
# For Vertex/Anthropic models also: export GCP_PROJECT_ID=...  GCP_LOCATION=...

# 3. Smoke-test the harness with the no-op template agent on one scenario
uv run python -m bench.run \
    --agent examples/agent_template.py \
    --scenario basic_format_table --runs 1 \
    --model openai:gpt-4.1-mini --judge-model openai:gpt-4.1

# 4. See the bundled example agents
uv run python -m bench.run --list-examples
```

The template agent is a pass-through with no memory, so it scores like the control — that's expected; it just proves the harness runs. To see real lift, point `--agent` at a memory approach (see **Bring your own approach** below).

---

## How a scenario runs

For each scenario the bench drives your approach module through this lifecycle:

```
setup()                                  # once, when the module loads
  └─ per scenario:
       prepare()                         # reset your memory store
       capture_one(trace) × N            # ingest the seed traces (past runs + corrections), in order
       get_injection(...)                # up-front correction text (optional)
       get_prior_messages(...)           # corrections as fabricated dialogue (optional)
       run_agent(...) × runs             # execute the agent on the unseen task
            └─ on_tool_result(...)       # after each tool call: surface per-tool rules (optional)
teardown()                               # once, at the end
```

The bench runs **control** (same task, your hooks return nothing) and **treatment** (your full approach) for every scenario, scores both with an LLM judge against a per-scenario rubric, and reports the lift.

---

## Results & metrics

Output is written under `bench/results/` (override with `BENCH_RESULTS_DIR`):

```
results/
  <approach>/<scenario_id>.json   # per-scenario: one record per run
  control/<scenario_id>.json      # the no-memory baseline
  full_results.json               # control + treatment, all runs
  report.txt                      # aggregated table: mean score, lift, tokens, latency
```

Each run record carries:

| Field | Meaning |
| --- | --- |
| `judge_score` | 0–1 rubric score from the LLM judge |
| `judge_reasoning` | the judge's justification |
| `injection_tokens` | tokens your approach injected (the cost of the memory) |
| `agent_input_tokens` / `agent_output_tokens` / `agent_requests` / `agent_tool_calls` | agent run stats |
| `agent_latency_ms` / `seed_query_latency_ms` | wall-clock for the run and for retrieval |

The headline metric is **lift = mean(treatment) − mean(control)** per approach, summarized in `report.txt`. A healthy benchmark shows control ≈ 0 (the agent doesn't already comply) and a strong approach pushing treatment high.

---

## Bring your own approach

The bench is **duck-typed**: write one Python file exposing the [`AgentModule`](bench/core/agent_interface.py) Protocol and point `--agent` at it. No subclassing, no registration.

```bash
cp examples/agent_template.py examples/agent_my_approach.py
# fill in the TODOs, then:
uv run python -m bench.run --agent examples/agent_my_approach.py --suite basic --runs 1
```

### The contract

| Member | Purpose |
| --- | --- |
| `name: str` | Identifier → results directory `results/<name>/`. |
| `async setup()` | One-time init (DB, model loading). |
| `async prepare()` | Per-scenario reset — clear your memory store so scenarios don't bleed. |
| `async capture_one(trace)` | Ingest one seed trace; called per seed, in order. |
| `async get_injection(...) -> str` | Up-front correction text (or `""`). |
| `async on_tool_result(...) -> str` | Per-tool-call hook; return rule text or `""`. |
| `async run_agent(...) -> AgentResult` | Execute one agent run. |
| `async teardown()` | One-time cleanup. |
| `async get_prior_messages(...)` *(optional)* | Deliver corrections as fabricated user/assistant turns instead of via the system prompt. |

Most implementations delegate `run_agent` to the bundled runner, which executes the skill against the mock tools and handles channel routing for you:

```python
from bench.core.agent_runner import run_from_protocol
from bench.core.channels import Channel

async def run_agent(*, skill, query, company, injection_text, tool_callback, prior_messages=None):
    return await run_from_protocol(
        skill=skill, query=query, company=company,
        injection_text=injection_text, tool_callback=tool_callback,
        prior_messages=prior_messages,
        initial_channel=Channel.USER_TURN,     # where get_injection() text goes
        per_tool_channel=Channel.SYSTEM_PART,  # where on_tool_result() text goes
    )
```

### Injection channels

*How* memory reaches the model is your decision, expressed as data: an `Injection(content, channel)` is delivered **verbatim** (no hidden wrapping). Channels split by timing:

| Timing | Channels | Notes |
| --- | --- | --- |
| **Initial** (before first model call) | `SYSTEM_APPEND`, `SYSTEM_PREPEND`, `USER_TURN`, `ASSISTANT_TURN` | `USER_TURN` (corrections as "something the user said earlier") generalized best across frontier models. |
| **Per-tool-call** (after each tool result) | `SYSTEM_PART`, `TOOL_RESULT_SUFFIX`, `USER_NOTE` | See the safety note below. |

> **Why the per-tool channel matters.** Safety-trained models (Anthropic Opus 4.5+, GPT-5) discount text appended to tool returns (`TOOL_RESULT_SUFFIX`) as untrusted prompt-injection. The same text delivered as a `SYSTEM_PART` (a `SystemPromptPart` on the next request) is treated as trusted operating instructions and survives. `TOOL_RESULT_SUFFIX` is the cheapest path and fine on Haiku 4.5 / GPT-4.1 / Sonnet 4.5; `SYSTEM_PART` is the robust default.

Pick channels per call via `run_from_protocol(initial_channel=…, per_tool_channel=…)`, or drop to [`run_agent`](bench/core/agent_runner.py) and return your own `list[Injection]` for full control (mixed channels, custom framing, calling a provider SDK directly).

See [`examples/`](examples/) for nine worked agents (`forge_dc`, `lucid_dc`, `hybrid_raw`, `doc_naive`, `doc_chunk`, plus `mem0`/`zep` baselines).

---

## CLI reference

```bash
uv run python -m bench.run --agent <path> [selection] [options]
```

| Flag | Description |
| --- | --- |
| `--agent PATH[,PATH...]` | One or more approach modules to run against the same scenarios. |
| `--all` | Run all 71 scenarios. |
| `--suite NAME` | Run a named suite: `basic`, `chains`, `data`, `long`, `actors`, `fast`, `key`, `advanced`, `self_assess`. |
| `--scenario ID` | Run a single scenario (e.g. `basic_content_qrr`). |
| `--scenarios A,B,C` | Run a comma-separated list (ids or prefixes). |
| `--runs N` | Repeats per scenario (default 1; use 3–5 to average out variance). |
| `--model STR` | Agent model. Accepts `provider:model` or a bare alias (`claude-opus-4-7` → `vertexai-anthropic:…`). Sets `BENCH_AGENT_MODEL`. |
| `--judge-model STR` | Judge model (default `openai:gpt-4.1`). Sets `BENCH_JUDGE_MODEL`. |
| `--list-examples` | List bundled example agents. |
| `--name-suffix STR` | Suffix the results dir (keeps cross-model runs from clobbering). |

`bench/agent.py` is the reference no-injection agent (the standalone control).

---

## Providers & environment

Agent and judge both go through `pydantic-ai`, so any `provider:model` string resolves:

| String | Provider |
| --- | --- |
| `openai:gpt-4.1` | OpenAI direct |
| `vertexai-anthropic:claude-opus-4-7` | Anthropic via Google Vertex |
| `vertexai-anthropic:claude-haiku-4-5@20251001` | Anthropic via Google Vertex |
| `vertexai-garden:gemini-2.5-pro` | Gemini via Google Vertex |

| Variable | Effect |
| --- | --- |
| `OPENAI_API_KEY` | Required for OpenAI models and the default judge. |
| `ANTHROPIC_API_KEY` | Required for direct Anthropic models. |
| `GCP_PROJECT_ID`, `GCP_LOCATION` | Required for `vertexai-*` models. |
| `EVAL_FIXTURES_DIR` | Path to mock-tool YAML fixtures (default `bench/fixtures`). |
| `BENCH_AGENT_MODEL` / `BENCH_JUDGE_MODEL` | Set automatically by `--model` / `--judge-model`. |
| `BENCH_RESULTS_DIR` | Override the results output directory. |
| `BENCH_USAGE_MODULES` | Comma-separated dotted paths to approach usage accumulators for token attribution (optional). |

> The **bench core needs no database**. Some sample agents do: the Decision Context approaches (`forge_dc`, `lucid_dc`, `hybrid_raw`, `doc_naive`, `doc_chunk`) use Postgres + pgvector and are installed separately from the sibling [`decision-context-memory`](../decision-context-memory) repo (each package ships its own `docker-compose.yml`). `agent_mem0.py` needs `mem0ai`. These are kept out of the base deps so `uv sync` stays clean; install only the ones you run.

---

## Behavioral dimensions (71 scenarios)

| Dimension | Tests | Count |
| --- | --- | --- |
| `recall` | Format, terminology, phrasing reproduction | 9 |
| `temporal_coherence` | Correction chains, supersession, evolution, forgetting | 9 |
| `conditional_activation` | Data-triggered rules, multi-hop conditions, security gating | 12 |
| `scope_precision` | Per-actor, per-subject, cross-skill isolation | 8 |
| `behavioral_change` | Changing tool-call sequences and procedural steps | 7 |
| `implicit_learning` | Self-assessment from tool traces, query strategy, retry patterns | 10 |
| `persistence` | Long conversations, scale (50–100 corrections), multi-session | 10 |
| `exception_handling` | Ephemeral vs persistent corrections, rule precedence | 3 |
| `generalization_boundary` | When a correction should (and shouldn't) transfer to new subjects | 3 |

Scenarios run over realistic **skills** (company analysis, scoring, security assessment, customer support) backed by **mock tools** (`eval_lookup`, `async_lookup`, `web_search`, `security_lookup`, `support_lookup`) reading YAML fixtures — so runs are deterministic and offline except for the LLM calls.

---

## Building seeds

Scenarios ship with pre-built seed files captured from real agent runs (`bench/seeds/*.json`). To regenerate:

```bash
make seeds-list                                              # status of all scenario seeds
make seeds-build                                             # rebuild all
uv run python bench/seedgen/build_scenario.py --scenario basic_content_qrr   # rebuild one
uv run python bench/seedgen/capture_trace.py --skill eval-analyst --company linear.app  # debug one trace
```

Each scenario's seeds are real traces: an initial run, then the human correction replayed as a multi-turn follow-up (conversation history preserved, only the new turn captured).

---

## Repository layout

```
bench/
  run.py                 # CLI entry point (runs control + treatment, writes report.txt)
  metrics.py             # aggregation, lift, report formatting
  agent.py               # reference no-injection control agent
  playground.py          # interactive injection testing

  core/
    agent_interface.py   # the AgentModule Protocol (the contract)
    channels.py          # Channel enum + Injection (what/where to inject)
    agent_runner.py      # run_agent / run_from_protocol (the bundled runner)
    tool_harness.py      # mock-tool dispatch + per-tool callback wiring
    orchestrator.py      # per-scenario control + treatment loop
    scoring.py           # combines LLM judge + programmatic checks
    skills.py            # load skill prompts (.md) and model settings
    config.py            # model resolution, approach config
    results.py           # save/load/cache result JSON
    usage.py             # pluggable token-usage accumulators

  judge/                 # LLM-as-judge + deterministic checks
  tools/                 # simulated tools (read YAML fixtures)
  scenarios/             # 71 scenarios across 9 dimensions + dataclasses
  seedgen/               # build/capture real seed traces
  fixtures/              # YAML company/support/security data
  seeds/                 # pre-built seed JSON (one per scenario)
  skills/                # skill prompt definitions (.md + frontmatter)

examples/                # worked approach modules + agent_template.py
```

---

## Development

```bash
make install      # uv sync
make test         # pytest
make lint-check   # ruff + guard that bench/ stays approach-agnostic
make typing       # mypy
make clean        # remove caches/artifacts
```

`make lint-check` includes a guard that fails if any approach-specific identifier leaks into `bench/` — the core stays generic; approaches live in `examples/`.

---

## License

MIT. (Add a `LICENSE` file before publishing.)

## Citation

This benchmark accompanies a paper currently under double-blind review. Please cite:

```bibtex
@misc{anonymous2026decisioncontext,
  title        = {Decision Context: Persistent Behavioral Learning for AI Agents},
  author       = {Anonymous},
  year         = {2026},
  note         = {Under review at NeurIPS 2026 (PALM Workshop)},
  howpublished = {\url{https://anonymous.4open.science/r/decision-context-benchmark-0278}}
}
```

The full citation (author list, venue, DOI/link) will be added here once the paper is public.
