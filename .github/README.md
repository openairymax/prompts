<!-- SPDX-License-Identifier: AGPL-3.0-or-later OR Apache-2.0 -->
<!-- Copyright (c) 2025-2026 SPHARX Ltd. All Rights Reserved. -->

# `.github/` — Ecosystem Prompts 仓库自动化

> GitHub Actions 工作流与 CI 模板，服务于
> [Prompts](https://atomgit.com/openairymax/prompts) 叶子仓库。

---

## 定位

Prompts 是 Airymax AI Agent 运行时平台的**提示词模板库与评估调优框架**——
提供 14 个官方提示词模板（认知 / 记忆 / 安全 / 系统四大类）、版本注册表、
JSONL 数据集驱动的评估器和 A/B 对比测试框架。
本目录承载该仓库的 GitHub 级自动化配置。

## 目录内容

```
.github/
├── README.md              # 本文件
└── workflows/
    └── ci.yml             # CI 流水线（Tuner 测试套件）
```

## CI 流水线

| 工作流 | 触发条件 | 职责 |
|--------|----------|------|
| `ci.yml` | PR / push | Tuner 测试套件（scorer / evaluator / A/B test） |

## 相关链接

| 资源 | 链接 |
|------|------|
| **主 README** | [prompts/README.md](../README.md) |
| **伞仓** | [airymaxhub](https://atomgit.com/openairymax/airymaxhub) |
| **Ecosystem 管理仓** | [ecosystem/](../../) |

## 许可证

双许可证：**AGPL v3 + Apache 2.0**（SPDX: `AGPL-3.0-or-later OR Apache-2.0`）。
详见仓库根目录 [LICENSE](../LICENSE) 与 [NOTICE](../NOTICE)。

Copyright (c) 2025-2026 SPHARX Ltd. All Rights Reserved.
