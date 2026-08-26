# Prompts — Prompt Template Library + Evaluation / Tuning Framework

> Systematic prompt template management, versioning, evaluation and A/B tuning for the Airymax platform.
> A leaf repository under the [Airymax ecosystem](https://atomgit.com/openairymax/ecosystem).

**Language:** English | [简体中文](README_zh.md)

[![Version](https://img.shields.io/badge/version-0.1.1-5a6b7e)](https://atomgit.com/openairymax/prompts)
[![License](https://img.shields.io/badge/license-AGPL--3.0+Apache--2.0-4a90d9)](LICENSE)
[![Branch](https://img.shields.io/badge/branch-feature%2Fofficial--hubs--01-6f7b8e)](https://atomgit.com/openairymax/prompts)

**Repository:** `git@atomgit.com:openairymax/prompts.git` · **Branch:** `feature/official-hubs-01`

---

## Overview

`ecosystem/prompts/` is the **prompt template library and evaluation / tuning framework** of the Airymax AI Agent Runtime Platform. It provides everything needed to version, evaluate and continuously optimize the prompts that drive agent behavior — the cognitive, memory, security and system prompts executed by every agent in the ecosystem.

The repository ships a curated catalog of **14 official prompt templates** across 4 categories (Cognition / Memory / Security / System), a **registry** (`registry.yaml`) that tracks version, category and lifecycle status (`stable` / `testing` / `deprecated`) for every template, an **evaluation framework** (`tuner/`) that runs prompts against JSONL datasets and produces precision / recall / hallucination / latency reports, and an **A/B testing framework** that compares two prompt versions on the same dataset with paired t-test significance. Templates are plain YAML with `system`, `user_template`, `output_schema` and `metrics` sections.

Within the ecosystem layer, `prompts/` is a self-contained template library with **no upstream Airymax repository dependency**. It is consumed downstream by agent applications (via the Airymax SDKs), the AgentRT runtime (which reads `registry.yaml` to resolve prompt names/versions and serves `/v1/prompt/execute`), CI/CD pipelines (which run the evaluator as a quality gate before promoting a prompt from `testing` to `stable`), and prompt authors (who use the A/B tester to validate candidates).

## Directory Structure

```
prompts/
├── registry.yaml                       # Prompt registry (version / category / status)
├── templates/                          # Prompt template library (14 templates)
│   ├── cognition/                      # Cognitive prompts (4)
│   │   ├── intent_classify.yaml        # Intent classification
│   │   ├── entity_extract.yaml         # Named entity extraction
│   │   ├── plan_generate.yaml          # Plan generation
│   │   └── reflection.yaml             # Reflection
│   ├── memory/                         # Memory prompts (4)
│   │   ├── extract_facts.yaml          # Atomic fact extraction
│   │   ├── dedup_decision.yaml         # Deduplication decision
│   │   ├── summarize.yaml              # Iterative summarization
│   │   └── rule_generate.yaml          # L4 rule induction
│   ├── security/                       # Security prompts (3)
│   │   ├── code_review.yaml            # Code security review
│   │   ├── security_scan.yaml          # System security scan
│   │   └── input_validate.yaml         # Input validation
│   └── system/                         # System prompts (3)
│       ├── default_agent.yaml          # Default agent
│       ├── coding_agent.yaml           # Coding agent
│       └── research_agent.yaml         # Research agent
├── datasets/                           # Evaluation datasets (JSONL)
│   ├── cognition/                      # 3 dataset versions + generators
│   │   ├── dataset_v1.jsonl
│   │   ├── dataset_v2.jsonl
│   │   ├── dataset_v3.jsonl
│   │   ├── gen_v3_p1.py … gen_v3_p10.py # Dataset generation scripts
│   │   ├── gen_v3_combine.py
│   │   └── merge_v3.py
│   ├── memory/                         # dataset_v1, dataset_v2
│   ├── security/                       # dataset_v1
│   └── system/                         # dataset_v1
├── tuner/                              # Evaluation & tuning framework
│   ├── src/
│   │   ├── scorer.py                   # Field-level precision / recall / hallucination
│   │   ├── evaluate.py                 # Dataset-driven evaluator + report builder
│   │   └── ab_test.py                  # Paired t-test A/B comparison
│   └── tests/
│       └── test_tuner.py
├── .github/workflows/ci.yml            # CI pipeline
├── .gitignore
└── README.md                           # This file
```

## Core Components

### Prompt Catalog (14 templates)

| Category | Count | Templates | Description |
|----------|:-----:|-----------|-------------|
| **Cognition** | 4 | `intent_classify`, `entity_extract`, `plan_generate`, `reflection` | Cognitive tasks: classification, extraction, planning, reflection |
| **Memory** | 4 | `extract_facts`, `dedup_decision`, `summarize`, `rule_generate` | Memory operations: fact extraction, dedup, summarization, rule induction |
| **Security** | 3 | `code_review`, `security_scan`, `input_validate` | Security: code review, security scan, input validation |
| **System** | 3 | `default_agent`, `coding_agent`, `research_agent` | System prompts for different agent personas |

Every template is a YAML file with `name`, `version`, `description`, `model_family`, `temperature`, `max_tokens`, a `system` block, a `user_template` (with `{placeholders}`), an `output_schema` (JSON Schema) and a `metrics` block declaring the quality gates the evaluator checks against (`target_precision`, `target_recall`, `max_hallucination_rate`).

### Registry (`registry.yaml`)

The single source of truth for every prompt's metadata — name, version, category, path, description, `model_family` and `status` (`stable` / `testing` / `deprecated`). All 14 templates are currently `stable`. The runtime resolves prompt names/versions through this registry.

### Evaluation & Tuning Framework (`tuner/`)

- **`scorer.py`** — field-level precision / recall / hallucination detection against `output_schema`.
- **`evaluate.py`** — dataset-driven evaluator that runs a prompt version across a JSONL dataset and produces an aggregated report (avg precision, avg recall, hallucination rate, latency). Supports an offline mode when the gateway is unreachable.
- **`ab_test.py`** — paired t-test A/B comparison of a baseline vs candidate version on the same dataset, returning `significant` and `p_value`.

### Evaluation Datasets (`datasets/`)

JSONL datasets organized by category. The cognition category ships 3 versions plus 10 partition generators (`gen_v3_p1.py` … `gen_v3_p10.py`), a combiner and a merger, demonstrating reproducible dataset construction.

## Upstream Dependencies

**None — `prompts/` is a self-contained template library.** It does not import any other Airymax repository and only relies on standard tooling to render and evaluate templates:

| Dependency | Purpose |
|------------|---------|
| Python ≥ 3.10 | Tuner runtime |
| `PyYAML` | Template & registry parsing |
| `requests` (optional) | Gateway calls during online evaluation; offline mode works without it |
| `pytest` | Tuner tests |

## Downstream Consumers

| Consumer | How it uses `prompts/` |
|----------|------------------------|
| **Agent applications** | Load templates via the Airymax SDK (`sdk-python` / `sdk-go` / `sdk-rust` / `sdk-typescript`) and render them with runtime context |
| **AgentRT runtime** | Reads `registry.yaml` to resolve prompt names and versions; serves `/v1/prompt/execute` endpoints |
| **CI / CD pipelines** | Run `tuner/src/evaluate.py` as a quality gate before promoting a prompt from `testing` to `stable` |
| **Prompt authors** | Use `tuner/src/ab_test.py` to validate that a candidate version beats the baseline before merging |
| **Examples (`ecosystem/examples`)** | `prompt-tuner-demo` consumes the tuner framework and dataset format |

## Usage / Quick Start

### Programmatic evaluation

```python
from tuner.src.evaluate import PromptEvaluator

evaluator = PromptEvaluator(
    prompts_dir="ecosystem/prompts",
    gateway_url="http://localhost:8080",   # optional, offline mode if unreachable
)
report = evaluator.evaluate(
    prompt_name="extract_facts",
    version="1.0.0",
    dataset_path="datasets/memory/dataset_v1.jsonl",
)
print(report.avg_precision, report.avg_recall, report.hallucination_rate)
```

### A/B testing

```python
from tuner.src.ab_test import ABTestRunner

runner = ABTestRunner(
    prompts_dir="ecosystem/prompts",
    gateway_url="http://localhost:8080",
)
report = runner.ab_test(
    prompt_name="intent_classify",
    baseline_version="1.0.0",
    candidate_version="1.1.0",
    dataset_path="datasets/cognition/dataset_v1.jsonl",
)
print(report.recommendation)
print(report.significance_tests)  # per-metric significant / p_value
```

### CLI

```bash
# Evaluate a prompt against a dataset
python -m tuner.src.evaluate intent_classify \
    --version 1.0.0 \
    --dataset datasets/cognition/dataset_v1.jsonl \
    --output report.json

# Run tuner tests
python -m pytest tuner/tests/ -v
```

### Adding a new prompt

1. Create a YAML template under the appropriate `templates/<category>/` directory.
2. Register it in `registry.yaml` with `status: testing`.
3. (Optional) Add an evaluation dataset under `datasets/<category>/`.
4. Validate with the evaluator: `python -m tuner.src.evaluate <name> --dataset <path>`.
5. Once quality gates pass, flip `status` to `stable`.

## Build

`prompts/` is a pure YAML + Python library with no compiled artifact. Install the tuner dependencies and run the test suite:

```bash
# Tuner runtime dependencies
pip install pyyaml requests pytest

# Run the tuner test suite
python -m pytest tuner/tests/ -v
```

CI is defined in `.github/workflows/ci.yml` and runs the tuner tests on every push.

## Branch Strategy

This leaf repository is on the **`feature/official-hubs-01`** branch (active development). The management repository that aggregates it stays on `main`.

## License

Dual-licensed under **AGPL v3 + Apache 2.0** (SPDX: `AGPL-3.0-or-later OR Apache-2.0`). See [LICENSE](LICENSE) for the full text.

Copyright (c) 2025-2026 SPHARX Ltd. All Rights Reserved.
