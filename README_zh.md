# Prompts — 提示词模板库 + 评估调优框架

> 为 Airymax 平台提供系统化的提示词模板管理、版本控制、评估与 A/B 调优。
> 隶属于 [Airymax ecosystem](https://atomgit.com/openairymax/ecosystem) 的叶子仓。

**语言:** [English](README.md) | 简体中文

[![Version](https://img.shields.io/badge/version-0.1.1-5a6b7e)](https://atomgit.com/openairymax/prompts)
[![License](https://img.shields.io/badge/license-AGPL--3.0+Apache--2.0-4a90d9)](LICENSE)
[![Branch](https://img.shields.io/badge/branch-feature%2Fofficial--hubs--01-6f7b8e)](https://atomgit.com/openairymax/prompts)

---

## 模块定位

`ecosystem/prompts/` 是 Airymax AI Agent 运行时平台的**提示词模板库与评估 / 调优框架**，提供驱动 Agent 行为所需的提示词版本管理、评估与持续优化能力：

- 精选 **14 个官方提示词模板**，覆盖 4 大类别（Cognition / Memory / Security / System）
- **注册表**（`registry.yaml`）追踪每个模板的版本、类别与生命周期状态（`stable` / `testing` / `deprecated`）
- **评估框架**（`tuner/`）在 JSONL 数据集上运行提示词，产出精确率 / 召回率 / 幻觉率 / 延迟报告
- **A/B 测试框架**在相同数据集上对比两个版本，使用配对 t 检验判定显著性

模板为纯 YAML，包含 `system`、`user_template`、`output_schema` 与 `metrics` 字段，可直接被 AgentRT 运行时或任意支持 Airymax 提示词格式的 SDK 消费。

## 目录结构

```
prompts/
├── registry.yaml                       # 提示词注册表（版本 / 类别 / 状态）
├── templates/                          # 提示词模板库（14 个模板）
│   ├── cognition/                      # 认知类提示词
│   │   ├── intent_classify.yaml        # 意图分类
│   │   ├── entity_extract.yaml         # 命名实体提取
│   │   ├── plan_generate.yaml          # 计划生成
│   │   └── reflection.yaml             # 反思
│   ├── memory/                         # 记忆类提示词
│   │   ├── extract_facts.yaml          # 原子事实提取
│   │   ├── dedup_decision.yaml         # 去重决策
│   │   ├── summarize.yaml              # 迭代摘要
│   │   └── rule_generate.yaml          # L4 规则归纳
│   ├── security/                       # 安全类提示词
│   │   ├── code_review.yaml            # 代码安全审查
│   │   ├── security_scan.yaml          # 系统安全扫描
│   │   └── input_validate.yaml         # 输入校验
│   └── system/                         # 系统类提示词
│       ├── default_agent.yaml          # 默认 Agent
│       ├── coding_agent.yaml           # 编码 Agent
│       └── research_agent.yaml         # 研究 Agent
├── datasets/                           # 评估数据集（JSONL）
│   ├── cognition/                      # 3 个数据集版本 + 生成器
│   │   ├── dataset_v1.jsonl
│   │   ├── dataset_v2.jsonl
│   │   ├── dataset_v3.jsonl
│   │   ├── gen_v3_*.py                 # 数据集生成脚本
│   │   └── merge_v3.py
│   ├── memory/
│   │   ├── dataset_v1.jsonl
│   │   └── dataset_v2.jsonl
│   ├── security/
│   │   └── dataset_v1.jsonl
│   └── system/
│       └── dataset_v1.jsonl
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

## 提示词分类

| 类别 | 数量 | 模板 | 说明 |
|------|:----:|------|------|
| **Cognition** | 4 | `intent_classify`、`entity_extract`、`plan_generate`、`reflection` | 认知任务：分类、提取、规划、反思 |
| **Memory** | 4 | `extract_facts`、`dedup_decision`、`summarize`、`rule_generate` | 记忆操作：事实提取、去重、摘要、规则归纳 |
| **Security** | 3 | `code_review`、`security_scan`、`input_validate` | 安全：代码审查、安全扫描、输入校验 |
| **System** | 3 | `default_agent`、`coding_agent`、`research_agent` | 不同 Agent 角色的系统提示词 |

## 模板结构

每个模板为 YAML 文件，包含以下字段：

```yaml
name: intent_classify
version: "1.0.0"
description: "将用户输入分类为预定义的意图类别"
model_family: any
temperature: 0.1
max_tokens: 256

system: |
  You are an intent classification system. ...

user_template: |
  {conversation_history}
  User input: "{user_input}"
  Classify the intent.

output_schema:
  type: object
  properties:
    intent: {type: string, enum: [question, task, chat, analysis, creative, command, ambiguous]}
    confidence: {type: number, minimum: 0, maximum: 1}
  required: [intent, confidence]

metrics:
  target_precision: 0.92
  target_recall: 0.90
  max_hallucination_rate: 0.01
```

`metrics` 块声明了评估器所校验的质量门禁。

## 注册表

`registry.yaml` 是所有提示词元信息的唯一真相源：

```yaml
prompts:
  - name: "intent_classify"
    version: "1.0.0"
    category: "cognition"
    path: "templates/cognition/intent_classify.yaml"
    description: "..."
    model_family: "any"
    status: "stable"   # stable | testing | deprecated
```

| 状态 | 含义 |
|------|------|
| `stable` | 生产可用，经过充分测试 |
| `testing` | 测试中，可能变更 |
| `deprecated` | 已弃用，计划移除 |

## 上游 / 下游依赖关系

### 上游

**无。** `prompts/` 是自包含的模板库，不依赖任何其他 Airymax 仓，仅依赖标准工具链来渲染和评估模板：

| 依赖 | 用途 |
|------|------|
| Python ≥ 3.10 | Tuner 运行时 |
| `PyYAML` | 模板与注册表解析 |
| `requests`（可选） | 在线评估时调用 Gateway；不可达时进入离线模式 |
| `pytest` | Tuner 测试 |

### 下游

| 消费方 | 使用方式 |
|--------|----------|
| **Agent 应用** | 通过 Airymax SDK（`sdk-python` / `sdk-go` / `sdk-rust` / `sdk-typescript`）加载模板并用运行时上下文渲染 |
| **AgentRT 运行时** | 读取 `registry.yaml` 解析提示词名与版本；提供 `/v1/prompt/execute` 端点 |
| **CI / CD 流水线** | 在将提示词从 `testing` 提升为 `stable` 前，运行 `tuner/src/evaluate.py` 作为质量门禁 |
| **提示词作者** | 合并前使用 `tuner/src/ab_test.py` 验证候选版本优于基线 |

## 使用说明

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
from tuner.src.ab_test import ABTest

ab = ABTest(
    prompts_dir="ecosystem/prompts",
    gateway_url="http://localhost:8080",
)
result = ab.compare(
    prompt_name="intent_classify",
    baseline_version="1.0.0",
    candidate_version="1.1.0",
    dataset_path="datasets/cognition/dataset_v1.jsonl",
)
print(result.significant, result.p_value)
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

## 分支策略

本叶子仓位于 **`feature/official-hubs-01`** 分支（活跃开发）。聚合它的管理仓保持在 `main`。

## 许可证

采用 **AGPL v3 + Apache 2.0** 双许可证（SPDX: `AGPL-3.0-or-later OR Apache-2.0`）。详见 [LICENSE](LICENSE)。

Copyright (c) 2025-2026 **SPHARX Ltd.** All Rights Reserved.
