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
  2. 双向一致性：templates/*.yaml 全量登记于 registry；registry 中每个
     path 必须存在；name/version/category 与模板文件头一致。
  3. 唯一性：registry 中无重复 name / 重复 path。

任何校验失败退出码非 0（CI 门禁 fail-closed）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
REGISTRY = ROOT / "registry.yaml"
VALID_STATUS = {"stable", "testing", "deprecated"}
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")

errors: list[str] = []


def _err(msg: str) -> None:
    errors.append(msg)
    print(f"  [FAIL] {msg}", file=sys.stderr)


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
    return {
        "name": str(name) if name else tmpl_path.stem,
        "version": str(data.get("version", "1.0.0")),
        "category": str(data.get("category", tmpl_path.parent.name)),
    }


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

    if errors:
        print(f"[FAIL] prompts 校验未通过（{len(errors)} 项）", file=sys.stderr)
        return 1
    print(f"[ OK ] prompts 校验通过（registry {len(reg_entries)} 条，templates 全量一致）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
