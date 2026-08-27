# Templates — 提示词模板库

> 属于 `ecosystem/prompts`（提示词仓库）的 `templates` 子模块。

## 定位

`templates/` 是 AgentRT 的提示词模板库：按领域组织（system/cognition/
memory/security），供运行时各 daemon（如 think_d/llm_d/mem_d）加载，
是提示词逻辑的单一真相源。

## 与其他模块的边界（SSoT 分工）

| 领域 | 本目录职责 | 相邻模块 | 边界约定 |
|------|-----------|----------|----------|
| `system/*` | 通用系统提示词模板（default_agent / coding_agent / research_agent），供运行时 `prompt_loader` 按需加载 | `ecosystem/agents/airymax_agents/*/prompts/system.md` | 后者是各角色 Agent 执行体实际加载的**角色专属提示词**（更具体、含工具收敛守则），以角色实现为准；本目录模板用于通用场景与降级路径 |
| `security/*` | 安全审查提示词模板（code_review / security_scan / input_validate），作为内容资产供组装 | `ecosystem/skills`（code_review / security_audit 技能，Python 与 C 插件实现） | skills 是**可执行能力封装**（含契约与执行入口），本目录是**提示词内容库**；两者互不硬依赖，skills 可内嵌自带提示词 |

> 约定：涉及具体角色执行时，以 `ecosystem/agents/airymax_agents` 的角色
> system.md 与 `ecosystem/skills` 的技能实现为权威；本目录模板面向通用
> 组装与评估回归。

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
