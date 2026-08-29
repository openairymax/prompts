#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025-2026 SPHARX Ltd.
# SPDX-License-Identifier: AGPL-3.0-or-later OR Apache-2.0
"""generate_registry.py — prompts 规则库管线「模板 → 索引」生成器（0.1.6 P1-5）。

扫描 templates/<category>/<name>.yaml 自动生成 registry.yaml（索引），
消除手工维护 registry 的漂移（SSoT：模板是权威，索引是派生）。

用法：
  python3 scripts/generate_registry.py            # 覆写 registry.yaml
  python3 scripts/generate_registry.py --check    # 只比对不落盘（CI 门禁）

--check 模式忽略 last_updated（每次生成都变，不构成漂移）；
其余字段（条目集合/字段值/stats）有差异即退出码非 0。
"""

from __future__ import annotations

import argparse
import datetime
import sys
from collections import Counter, OrderedDict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
REGISTRY = ROOT / "registry.yaml"
CATEGORY_ORDER = ["cognition", "memory", "security", "system"]
REGISTRY_VERSION = "1.0.0"


def _scan_templates() -> list[dict]:
    """遍历 templates/<cat>/<name>.yaml，读取模板元数据。"""
    entries: list[dict] = []
    for cat_dir in sorted(TEMPLATES.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue
        for tmpl in sorted(cat_dir.glob("*.yaml")):
            if tmpl.name == ".gitkeep":
                continue
            with tmpl.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            name = str(data.get("name") or tmpl.stem)
            entries.append(
                {
                    "name": name,
                    "version": str(data.get("version", "1.0.0")),
                    "category": str(data.get("category", cat_dir.name)),
                    "path": f"templates/{cat_dir.name}/{tmpl.name}",
                    "description": str(data.get("description", "")),
                    "model_family": str(data.get("model_family", "any")),
                    "status": str(data.get("status", "stable")),
                }
            )
    return entries


def _render(entries: list[dict]) -> str:
    """按现有 registry.yaml 格式渲染（含分组注释，保持可读性）。"""
    by_cat: "OrderedDict[str, list[dict]]" = OrderedDict()
    for cat in CATEGORY_ORDER:
        by_cat[cat] = [e for e in entries if e["category"] == cat]
    for e in entries:
        if e["category"] not in by_cat:
            by_cat.setdefault(e["category"], []).append(e)

    lines: list[str] = []
    lines.append("# AgentRT Prompt Registry")
    lines.append(f"# Version: {REGISTRY_VERSION}")
    lines.append("# Auto-generated registry of all prompt templates.")
    lines.append(f"# Updated: {datetime.date.today().isoformat()}")
    lines.append("")
    lines.append(f'registry_version: "{REGISTRY_VERSION}"')
    lines.append(f'last_updated: "{datetime.date.today().isoformat()}"')
    lines.append("")
    lines.append("prompts:")
    for cat, cat_entries in by_cat.items():
        cat_title = cat.capitalize()
        lines.append(f"  # ─── {cat_title} {'─' * (50 - len(cat_title))}")
        for e in cat_entries:
            lines.append(f'  - name: "{e["name"]}"')
            lines.append(f'    version: "{e["version"]}"')
            lines.append(f'    category: "{e["category"]}"')
            lines.append(f'    path: "{e["path"]}"')
            lines.append(f'    description: "{e["description"]}"')
            lines.append(f'    model_family: "{e["model_family"]}"')
            lines.append(f'    status: "{e["status"]}"')
            lines.append("")
    lines.append("")
    # stats
    total = len(entries)
    cat_count = Counter(e["category"] for e in entries)
    status_count = Counter(e["status"] for e in entries)
    lines.append("stats:")
    lines.append(f"  total_prompts: {total}")
    lines.append("  categories:")
    for cat in CATEGORY_ORDER:
        if cat_count[cat]:
            lines.append(f"    {cat}: {cat_count[cat]}")
    for cat in sorted(set(cat_count) - set(CATEGORY_ORDER)):
        lines.append(f"    {cat}: {cat_count[cat]}")
    lines.append("  status:")
    for st in ("stable", "testing", "deprecated"):
        if status_count[st]:
            lines.append(f"    {st}: {status_count[st]}")
    for st in sorted(set(status_count) - {"stable", "testing", "deprecated"}):
        lines.append(f"    {st}: {status_count[st]}")
    lines.append("")
    return "\n".join(lines)


def _field_only(entries: list[dict]) -> dict:
    """仅取比对关键字段（剔除 last_updated 与注释）。"""
    norm = []
    for e in sorted(entries, key=lambda x: x["path"]):
        norm.append({k: e[k] for k in ("name", "version", "category", "path",
                                       "description", "model_family", "status")})
    return {"entries": norm}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只比对不落盘（CI 门禁）")
    args = parser.parse_args()

    entries = _scan_templates()
    rendered = _render(entries)
    if not args.check:
        REGISTRY.write_text(rendered, encoding="utf-8")
        print(f"[ OK ] registry.yaml 已生成（{len(entries)} 个模板）")
        return 0

    if not REGISTRY.exists():
        print("[FAIL] registry.yaml 不存在（先运行生成器）", file=sys.stderr)
        return 1
    with REGISTRY.open(encoding="utf-8") as f:
        committed = yaml.safe_load(f) or {}
    committed_entries = committed.get("prompts", [])

    fresh = _field_only(entries)
    cur = _field_only(committed_entries)
    if fresh == cur:
        print(f"[ OK ] registry.yaml 与 templates/ 一致（{len(entries)} 个模板，无漂移）")
        return 0
    print("[FAIL] registry.yaml 漂移：与 templates/ 不一致，请运行生成器后提交", file=sys.stderr)
    print(f"  templates 侧条目: {len(fresh['entries'])}", file=sys.stderr)
    print(f"  registry 侧条目: {len(cur['entries'])}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
