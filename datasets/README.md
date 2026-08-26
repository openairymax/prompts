# Datasets — 提示词数据集

> 属于 `ecosystem/prompts`（提示词仓库）的 `datasets` 子模块。

## 定位

`datasets/` 存放用于提示词研发、回归与评估的结构化数据集（JSONL）。
每个数据集对应一个领域（system/cognition/memory/security），是提示词
模板效果的可复现评估基准。

## 目录结构

```
datasets/
├── system/        # 系统级提示词数据集
├── cognition/     # 认知层数据集（意图分类/规划/反思等）
├── memory/        # 记忆层数据集（事实抽取/摘要/去重等）
└── security/      # 安全层数据集（输入校验/安全扫描等）
```

每个领域目录内含 `dataset_vN.jsonl`（N 为版本号），cognition 领域另含
`gen_v3_p*.py` / `merge_v3.py` 等**数据集生成脚本**（自动合成大规模
样本，见文件头说明）。

## 数据格式

`dataset_vN.jsonl` 每行一个 JSON 对象，为单条「输入-期望输出」样本。
字段以各领域实际生成脚本（如 `gen_v3_p1.py`）定义为准，生成脚本是
数据集格式的单一真相源。

## 使用方式

- **提示词调优器**（`tuner/`）消费数据集进行 A/B 评估与评分；
- **回归测试**：修改提示词模板后，用数据集回归验证输出质量不退化；
- **生成脚本**：`python gen_v3_p1.py` 生成对应子集，`merge_v3.py`
  合并全部子集为完整数据集。
