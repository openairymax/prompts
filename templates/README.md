# Templates — 提示词模板库

> 属于 `ecosystem/prompts`（提示词仓库）的 `templates` 子模块。

## 定位

`templates/` 是 AgentRT 的提示词模板库：按领域组织（system/cognition/
memory/security），供运行时各 daemon（如 think_d/llm_d/mem_d）加载，
是提示词逻辑的单一真相源。

## 目录结构

```
templates/
├── system/     # 系统级模板（default_agent / coding_agent / research_agent）
├── cognition/  # 认知层模板（intent_classify / plan_generate / reflection / entity_extract）
├── memory/     # 记忆层模板（extract_facts / summarize / dedup_decision / rule_generate）
└── security/   # 安全层模板（code_review / security_scan / input_validate）
```

## 格式

模板为 YAML 文件，包含提示词内容与元数据（名称、版本、用途、参数
占位符）。实际字段结构以各文件与 `prompt_loader`（agentrt commons）的
解析约定为准。

## 使用方式

- **运行时**：`prompt_loader` 按领域+名称加载模板，渲染后注入 LLM 请求；
- **评估**：与 `datasets/` 配对使用——同一领域数据集回归对应模板；
- **调优**：`tuner/` 对模板变体做 A/B 评分，择优发布。

## 维护约定

新增提示词模板时，请同步：

1. 放入对应领域目录（勿新建顶层领域，除非架构文档同步更新）；
2. 在 `datasets/` 对应领域补充回归样本；
3. 更新本 README 的目录树（如新增文件模式）。
