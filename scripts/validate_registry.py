#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025-2026 SPHARX Ltd.
# SPDX-License-Identifier: AGPL-3.0-or-later OR Apache-2.0
"""validate_registry.py — prompts 规则库管线「编译环节」校验器（0.1.6 P1-5）。

对每个模板做字段级校验 + registry.yaml ↔ templates/ 双向一致性检查
（编译环节质量门禁：索引与模板一一对应、字段完整、无悬空引用）。

校验项：
  1. 模板字段级：name/version/description 必填；system 或 user_template
     至少一个；status ∈ {stable, testing, deprecated}；version 为
     x.y.z 语义化版本。
  2. 模板质量门禁契约：metrics 块必含 target_precision / target_recall /
     max_hallucination_rate 且均为 [0,1] 数值；temperature ∈ [0,2]；
     max_tokens 为正整数；cognition/memory/security 类别模板须含
     output_schema（system 人设模板允许省略）。
  3. 双向一致性：templates/*.yaml 全量登记于 registry；registry 中每个
     path 必须存在；name/version/category 与模板文件头一致。
  4. 唯一性：registry 中无重复 name / 重复 path。
  5. stats 聚合一致：registry.stats（total_prompts / categories / status）
     须等于由条目集合派生的聚合（条目集合是唯一真相源）。
  6. 数据集一致：datasets/<category> 目录属于已知模板类别、文件命名匹配
     dataset_vN.jsonl、逐行合法 JSON 且含 input（字符串）与 expected_output
     （对象/数组），行内 category（若有）须为已注册模板名。

任何校验失败退出码非 0（CI 门禁 fail-closed）。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
REGISTRY = ROOT / "registry.yaml"
DATASETS = ROOT / "datasets"
VALID_STATUS = {"stable", "testing", "deprecated"}
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
DATASET_RE = re.compile(r"^dataset_v\d+\.jsonl$")
METRIC_KEYS = ("target_precision", "target_recall", "max_hallucination_rate")
STRUCT_CATS = ("cognition", "memory", "security")

errors: list[str] = []


def _err(msg: str) -> None:
    errors.append(msg)
    print(f"  [FAIL] {msg}", file=sys.stderr)


def _is_num(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _unit(v: object) -> bool:
    return _is_num(v) and 0.0 <= float(v) <= 1.0


def check_metrics(data: dict, rel: str) -> None:
    """质量门禁契约：metrics 块是评估器消费的门禁声明（SSoT）。"""
    m = data.get("metrics")
    if not isinstance(m, dict):
        _err(f"{rel}: 缺 metrics 质量门禁块")
        return
    for key in METRIC_KEYS:
        if key not in m:
            _err(f"{rel}: metrics 缺 {key}")
        elif not _unit(m[key]):
            _err(f"{rel}: metrics.{key} 非法（应为 [0,1] 数值，实际 {m[key]!r}）")


def check_sample(data: dict, rel: str) -> None:
    """采样参数契约：temperature / max_tokens 必须合法。"""
    t = data.get("temperature")
    if not _is_num(t) or not 0.0 <= float(t) <= 2.0:
        _err(f"{rel}: temperature 非法（应为 [0,2] 数值，实际 {t!r}）")
    mt = data.get("max_tokens")
    if not isinstance(mt, int) or isinstance(mt, bool) or mt <= 0:
        _err(f"{rel}: max_tokens 非法（应为正整数，实际 {mt!r}）")


def check_schema(data: dict, rel: str, cat: str) -> None:
    """输出契约：结构化类别须声明 output_schema，system 允许省略。"""
    schema = data.get("output_schema")
    if schema is None and cat in STRUCT_CATS:
        _err(f"{rel}: 类别 {cat} 的模板须含 output_schema")
    elif schema is not None and not isinstance(schema, dict):
        _err(f"{rel}: output_schema 应为映射，实际 {type(schema).__name__}")


def check_template_fields(tmpl_path: Path) -> dict:
    """字段级校验单个模板文件，返回其元数据。"""
    with tmpl_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    rel = f"templates/{tmpl_path.parent.name}/{tmpl_path.name}"
    name = data.get("name")
    if not name:
        _err(f"{rel}: 缺必填字段 name")
    if not data.get("version"):
        _err(f"{rel}: 缺必填字段 version")
    elif not VERSION_RE.match(str(data["version"])):
        _err(f"{rel}: version 非法（应为 x.y.z，实际 {data['version']!r}）")
    if not data.get("description"):
        _err(f"{rel}: 缺必填字段 description")
    if not data.get("system") and not data.get("user_template"):
        _err(f"{rel}: system 与 user_template 至少需要一个")
    status = str(data.get("status", "stable"))
    if status not in VALID_STATUS:
        _err(f"{rel}: status 非法（{status!r}，应为 {sorted(VALID_STATUS)}）")
    cat = str(data.get("category", tmpl_path.parent.name))
    check_metrics(data, rel)
    check_sample(data, rel)
    check_schema(data, rel, cat)
    return {
        "name": str(name) if name else tmpl_path.stem,
        "version": str(data.get("version", "1.0.0")),
        "category": cat,
    }


def check_stats(reg: dict, entries: list) -> None:
    """stats 聚合一致：由条目集合派生的聚合是唯一真相源。"""
    stats = reg.get("stats") or {}
    cats: dict[str, int] = {}
    sts: dict[str, int] = {}
    for e in entries:
        c = str(e.get("category"))
        s = str(e.get("status", "stable"))
        cats[c] = cats.get(c, 0) + 1
        sts[s] = sts.get(s, 0) + 1
    if stats.get("total_prompts") != len(entries):
        _err(f"registry.stats.total_prompts {stats.get('total_prompts')!r} != 派生 {len(entries)}")
    if (stats.get("categories") or {}) != cats:
        _err(f"registry.stats.categories 不一致：{stats.get('categories')!r} != {cats!r}")
    if (stats.get("status") or {}) != sts:
        _err(f"registry.stats.status 不一致：{stats.get('status')!r} != {sts!r}")


def check_ds_row(obj: object, rel: str, ln: int, names: set) -> None:
    """校验单条数据集样本的行内契约。"""
    if not isinstance(obj, dict):
        _err(f"{rel}:{ln}: 行应为 JSON 对象")
        return
    if not isinstance(obj.get("input"), str):
        _err(f"{rel}:{ln}: 缺 input 字符串")
    if not isinstance(obj.get("expected_output"), (dict, list)):
        _err(f"{rel}:{ln}: expected_output 应为对象或数组")
    cat = obj.get("category")
    if cat is not None and cat not in names:
        _err(f"{rel}:{ln}: category {cat!r} 非已注册模板名")


def check_ds_file(path: Path, cat: str, names: set) -> None:
    """逐行校验单个 JSONL 数据集文件。"""
    rel = f"datasets/{cat}/{path.name}"
    rows = 0
    with path.open(encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            rows += 1
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                _err(f"{rel}:{ln}: 非法 JSON")
                continue
            check_ds_row(obj, rel, ln, names)
    if rows == 0:
        _err(f"{rel}: 数据集无有效样本")


def check_datasets(cats: set, names: set) -> None:
    """数据集一致性：目录类别 / 文件命名 / 行格式均须符合契约。"""
    if not DATASETS.is_dir():
        _err("datasets/ 目录不存在")
        return
    for cat_dir in sorted(DATASETS.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue
        if cat_dir.name not in cats:
            _err(f"datasets/{cat_dir.name}: 未知类别（不在模板类别内）")
        files = sorted(cat_dir.glob("*.jsonl"))
        if not files:
            _err(f"datasets/{cat_dir.name}: 无 *.jsonl 数据集")
        for jf in files:
            if not DATASET_RE.match(jf.name):
                _err(f"datasets/{cat_dir.name}/{jf.name}: 命名非法（应为 dataset_vN.jsonl）")
            check_ds_file(jf, cat_dir.name, names)


def main() -> int:
    if not REGISTRY.exists():
        print("[FAIL] registry.yaml 不存在", file=sys.stderr)
        return 1
    with REGISTRY.open(encoding="utf-8") as f:
        reg = yaml.safe_load(f) or {}
    reg_entries = reg.get("prompts", [])

    # 1. registry 内部唯一性
    seen_names: set[str] = set()
    seen_paths: set[str] = set()
    for e in reg_entries:
        if e.get("name") in seen_names:
            _err(f"registry 重复 name: {e.get('name')}")
        seen_names.add(e.get("name", ""))
        if e.get("path") in seen_paths:
            _err(f"registry 重复 path: {e.get('path')}")
        seen_paths.add(e.get("path", ""))

    # 2. registry → 模板：path 必须存在
    for e in reg_entries:
        p = ROOT / e.get("path", "")
        if not p.is_file():
            _err(f"registry 悬空 path: {e.get('path')}")

    # 3. 模板 → registry：全量登记且字段一致
    reg_by_path = {e.get("path"): e for e in reg_entries}
    for cat_dir in sorted(TEMPLATES.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue
        for tmpl in sorted(cat_dir.glob("*.yaml")):
            if tmpl.name == ".gitkeep":
                continue
            meta = check_template_fields(tmpl)
            rel = f"templates/{cat_dir.name}/{tmpl.name}"
            if rel not in reg_by_path:
                _err(f"模板未登记于 registry: {rel}")
                continue
            re_ = reg_by_path[rel]
            if re_.get("name") != meta["name"]:
                _err(f"{rel}: registry name {re_.get('name')!r} != 模板 name {meta['name']!r}")
            if re_.get("version") != meta["version"]:
                _err(f"{rel}: registry version {re_.get('version')!r} != 模板 version {meta['version']!r}")
            if re_.get("category") != meta["category"]:
                _err(f"{rel}: registry category {re_.get('category')!r} != 模板 category {meta['category']!r}")

    # 4. stats 聚合一致 + 5. 数据集一致
    cats = {str(e.get("category")) for e in reg_entries if e.get("category")}
    names = {str(e.get("name")) for e in reg_entries if e.get("name")}
    check_stats(reg, reg_entries)
    check_datasets(cats, names)

    if errors:
        print(f"[FAIL] prompts 校验未通过（{len(errors)} 项）", file=sys.stderr)
        return 1
    print(f"[ OK ] prompts 校验通过（registry {len(reg_entries)} 条，templates/datasets 全量一致）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
