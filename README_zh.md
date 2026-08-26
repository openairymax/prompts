# Prompts — 提示词模板库 + 评估调优框架

> 为 Airymax 平台提供系统化的提示词模板管理、版本控制、评估与 A/B 调优。
> 隶属于 [Airymax ecosystem](https://atomgit.com/openairymax/ecosystem) 的叶子仓。

**语言:** [English](README.md) | 简体中文

[![Version](https://img.shields.io/badge/version-0.1.1-5a6b7e)](https://atomgit.com/openairymax/prompts)
[![License](https://img.shields.io/badge/license-AGPL--3.0+Apache--2.0-4a90d9)](LICENSE)
[![Branch](https://img.shields.io/badge/branch-feature%2Fofficial--hubs--01-6f7b8e)](https://atomgit.com/openairymax/prompts)

**仓库:** `git@atomgit.com:openairymax/prompts.git` · **分支:** `feature/official-hubs-01`

---

## 概述

`ecosystem/prompts/` 是 Airymax AI Agent 运行时平台的**提示词模板库与评估 / 调优框架**，提供驱动 Agent 行为所需的提示词版本管理、评估与持续优化能力——即生态中每个 Agent 所执行的认知、记忆、安全与系统提示词。

本仓提供精选的 **14 个官方提示词模板**，覆盖 4 大类别（Cognition / Memory / Security / System）；一个**注册表**（`registry.yaml`）追踪每个模板的版本、类别与生命周期状态（`stable` / `testing` / `deprecated`）；一个**评估框架**（`tuner/`）在 JSONL 数据集上运行提示词，产出精确率 / 召回率 / 幻觉率 / 延迟报告；以及一个**A/B 测试框架**，在相同数据集上对比两个版本，使用配对 t 检验判定显著性。模板为纯 YAML，包含 `system`、`user_template`、`output_schema` 与 `metrics` 字段。

在生态层中，`prompts/` 是自包含的模板库，**不依赖任何上游 Airymax 仓**。下游被 Agent 应用（通过 Airymax SDK）、AgentRT 运行时（读取 `registry.yaml` 解析提示词名/版本，提供 `/v1/prompt/execute` 端点）、CI/CD 流水线（在将提示词从 `testing` 提升为 `stable` 前运行评估器作为质量门禁）以及提示词作者（使用 A/B 测试器验证候选版本）消费。

## 目录结构

```
prompts/
├── registry.yaml                       # 提示词注册表（版本 / 类别 / 状态）
├── templates/                          # 提示词模板库（14 个模板）
│   ├── cognition/                      # 认知类提示词（4）
│   │   ├── intent_classify.yaml        # 意图分类
│   │   ├── entity_extract.yaml         # 命名实体提取
│   │   ├── plan_generate.yaml          # 计划生成
│   │   └── reflection.yaml             # 反思
│   ├── memory/                         # 记忆类提示词（4）
│   │   ├── extract_facts.yaml          # 原子事实提取
│   │   ├── dedup_decision.yaml         # 去重决策
│   │   ├── summarize.yaml              # 迭代摘要
│   │   └── rule_generate.yaml          # L4 规则归纳
│   ├── security/                       # 安全类提示词（3）
│   │   ├── code_review.yaml            # 代码安全审查
│   │   ├── security_scan.yaml          # 系统安全扫描
│   │   └── input_validate.yaml         # 输入校验
│   └── system/                         # 系统类提示词（3）
│       ├── default_agent.yaml          # 默认 Agent
│       ├── coding_agent.yaml           # 编码 Agent
│       └── research_agent.yaml         # 研究 Agent
├── datasets/                           # 评估数据集（JSONL）
│   ├── cognition/                      # 3 个数据集版本 + 生成器
│   │   ├── dataset_v1.jsonl
│   │   ├── dataset_v2.jsonl
│   │   ├── dataset_v3.jsonl
│   │   ├── gen_v3_p1.py … gen_v3_p10.py # 数据集生成脚本
│   │   ├── gen_v3_combine.py
│   │   └── merge_v3.py
│   ├── memory/                         # dataset_v1、dataset_v2
│   ├── security/                       # dataset_v1
│   └── system/                         # dataset_v1
├── tuner/                              # 评估与调优框架
│   ├── src/
│   │   ├── scorer.py                   # 字段级精确率 / 召回率 / 幻觉检测
│   │   ├── evaluate.py                 # 数据集驱动评估器 + 报告生成
│   │   └── ab_test.py                  # 配对 t 检验 A/B 对比
│   └── tests/
│       └── test_tuner.py
├── .github/workflows/ci.yml            # CI 流水线
├── .gitignore
└── README.md                           # 本文件
```

## 核心组件

### 提示词目录（14 个模板）

| 类别 | 数量 | 模板 | 说明 |
|------|:----:|------|------|
| **Cognition** | 4 | `intent_classify`、`entity_extract`、`plan_generate`、`reflection` | 认知任务：分类、提取、规划、反思 |
| **Memory** | 4 | `extract_facts`、`dedup_decision`、`summarize`、`rule_generate` | 记忆操作：事实提取、去重、摘要、规则归纳 |
| **Security** | 3 | `code_review`、`security_scan`、`input_validate` | 安全：代码审查、安全扫描、输入校验 |
| **System** | 3 | `default_agent`、`coding_agent`、`research_agent` | 不同 Agent 角色的系统提示词 |

每个模板为 YAML 文件，含 `name`、`version`、`description`、`model_family`、`temperature`、`max_tokens`、`system` 块、`user_template`（含 `{占位符}`）、`output_schema`（JSON Schema）以及 `metrics` 块（声明评估器校验的质量门禁：`target_precision`、`target_recall`、`max_hallucination_rate`）。

### 注册表（`registry.yaml`）

所有提示词元信息的唯一真相源——名称、版本、类别、路径、描述、`model_family` 与 `status`（`stable` / `testing` / `deprecated`）。当前 14 个模板均为 `stable`。运行时通过此注册表解析提示词名/版本。

### 评估与调优框架（`tuner/`）

- **`scorer.py`** — 针对 `output_schema` 的字段级精确率 / 召回率 / 幻觉检测。
- **`evaluate.py`** — 数据集驱动评估器，在 JSONL 数据集上运行某个提示词版本，产出聚合报告（平均精确率、平均召回率、幻觉率、延迟）。网关不可达时支持离线模式。
- **`ab_test.py`** — 在相同数据集上对基线版本与候选版本进行配对 t 检验 A/B 对比，返回 `ABTestReport`（含各指标 `significant` / `p_value` 与 `recommendation` 推荐结论）。

### 评估数据集（`datasets/`）

按类别组织的 JSONL 数据集。cognition 类别提供 3 个版本，外加 10 个分区生成器（`gen_v3_p1.py` … `gen_v3_p10.py`）、一个合并器与一个归并器，演示可复现的数据集构建方式。

## 上游依赖

**无——`prompts/` 是自包含的模板库。** 不依赖任何其他 Airymax 仓，仅依赖标准工具链来渲染和评估模板：

| 依赖 | 用途 |
|------|------|
| Python ≥ 3.10 | Tuner 运行时 |
| `PyYAML` | 模板与注册表解析 |
| `requests`（可选） | 在线评估时调用 Gateway；不可达时进入离线模式 |
| `pytest` | Tuner 测试 |

## 下游消费方

| 消费方 | 使用方式 |
|--------|----------|
| **Agent 应用** | 通过 Airymax SDK（`sdk-python` / `sdk-go` / `sdk-rust` / `sdk-typescript`）加载模板并用运行时上下文渲染 |
| **AgentRT 运行时** | 读取 `registry.yaml` 解析提示词名与版本；提供 `/v1/prompt/execute` 端点 |
| **CI / CD 流水线** | 在将提示词从 `testing` 提升为 `stable` 前，运行 `tuner/src/evaluate.py` 作为质量门禁 |
| **提示词作者** | 合并前使用 `tuner/src/ab_test.py` 验证候选版本优于基线 |
| **示例（`ecosystem/examples`）** | `prompt-tuner-demo` 消费 tuner 框架与数据集格式 |

## 使用说明 / 快速开始

### 编程式评估

```python
from tuner.src.evaluate import PromptEvaluator

evaluator = PromptEvaluator(
    prompts_dir="ecosystem/prompts",
    gateway_url="http://localhost:8080",   # 可选，不可达时进入离线模式
)
report = evaluator.evaluate(
    prompt_name="extract_facts",
    version="1.0.0",
    dataset_path="datasets/memory/dataset_v1.jsonl",
)
print(report.avg_precision, report.avg_recall, report.hallucination_rate)
```

### A/B 测试

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
print(report.significance_tests)  # 各指标的 significant / p_value
```

### CLI

```bash
# 在数据集上评估提示词
python -m tuner.src.evaluate intent_classify \
    --version 1.0.0 \
    --dataset datasets/cognition/dataset_v1.jsonl \
    --output report.json

# 运行 Tuner 测试
python -m pytest tuner/tests/ -v
```

### 添加新提示词

1. 在对应的 `templates/<category>/` 目录下创建 YAML 模板文件。
2. 在 `registry.yaml` 中注册，状态设为 `testing`。
3. （可选）在 `datasets/<category>/` 下添加评估数据集。
4. 用评估器校验：`python -m tuner.src.evaluate <name> --dataset <path>`。
5. 质量门禁通过后，将 `status` 改为 `stable`。

## 构建

`prompts/` 是纯 YAML + Python 库，无编译产物。安装 tuner 依赖并运行测试套件：

```bash
# Tuner 运行时依赖
pip install pyyaml requests pytest

# 运行 tuner 测试套件
python -m pytest tuner/tests/ -v
```

CI 定义在 `.github/workflows/ci.yml`，每次推送时运行 tuner 测试。

## 分支策略

本叶子仓位于 **`feature/official-hubs-01`** 分支（活跃开发）。聚合它的管理仓保持在 `main`。

## 许可证

采用 **AGPL v3 + Apache 2.0** 双许可证（SPDX: `AGPL-3.0-or-later OR Apache-2.0`）。详见 [LICENSE](LICENSE)。

Copyright (c) 2025-2026 SPHARX Ltd. All Rights Reserved.
