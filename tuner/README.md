# Tuner — 提示词调优器

> 属于 `ecosystem/prompts`（提示词仓库）的 `tuner` 子模块。

## 定位

`tuner/` 是提示词的离线调优工具：对模板变体执行 A/B 评估，基于
`datasets/` 数据集量化输出质量，辅助择优发布。不参与运行时路径，
仅供研发与评测使用。

## 目录结构

```
tuner/
├── __init__.py        # 包入口
├── src/
│   ├── __init__.py
│   ├── evaluate.py    # 评估器（对数据集批量评估模板变体）
│   ├── ab_test.py     # A/B 测试（对比两版模板）
│   └── scorer.py      # 评分器（量化输出质量）
└── tests/
    ├── __init__.py
    └── test_tuner.py  # 单元测试
```

## 使用方式

```bash
# 在 prompts 仓库根目录执行
python -m tuner.src.evaluate --dataset datasets/cognition/dataset_v3.jsonl
python -m tuner.src.ab_test --base templates/cognition/plan_generate.yaml \
                            --variant my_plan_v2.yaml \
                            --dataset datasets/cognition/dataset_v3.jsonl
```

- `evaluate.py`：对单一模板变体在数据集上的整体质量评分；
- `ab_test.py`：对比基准模板与候选模板，输出差异统计；
- `scorer.py`：内部评分函数（被 evaluate/ab_test 复用）。

## 测试

```bash
python -m pytest tuner/tests -v
```

## 与其余模块的关系

- 输入：`templates/` 模板变体 + `datasets/` 数据集；
- 输出：评分报告（无运行时副作用），供人工择优后落盘到 `templates/`。
