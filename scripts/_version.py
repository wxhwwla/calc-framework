#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
项目版本号与上传元数据 — 版本信息唯一源头。

此文件是 `_VERSION` 和 `_EXE_VERSION` 的唯一定义处。
`scripts/please_read_me.py` / `upload_meta.py` / `version.py` 均从此模块导入。
"""

from __future__ import annotations

import re
from pathlib import Path

# ==================== 版本常量（唯一源头） ====================

_VERSION = "3.29.13"
"""项目与 pip 包版本（pyproject.toml 通过 dynamic 读取）。

上传脚本在有「业务改动」并 push 成功时自动递增（默认第三位 +1）。
第一位 MAJOR 永远只在下方手动修改，脚本不会动。"""

_EXE_VERSION = "0.7.0-beta"
"""窗口标题与 dist/*.exe 用户可见版本。

仅手动修改；改后须重新打包（main_build.py）。"""

# ==============================================================

_SUMMARY_MARKER_BEGIN = ""
_UPLOAD_SUMMARY_BEGIN = _SUMMARY_MARKER_BEGIN
_UPLOAD_SUMMARY_END = _SUMMARY_MARKER_END
SUMMARY_BEGIN = _UPLOAD_SUMMARY_BEGIN
SUMMARY_END = _UPLOAD_SUMMARY_END
_VERSION_PATTERN = re.compile(
    r'^(_VERSION\s*=\s*["\'])([^"\']+)(["\'])',
    re.MULTILINE,
)

_EXE_VERSION_PATTERN = re.compile(
    r'^(_EXE_VERSION\s*=\s*["\'])([^"\']+)(["\'])',
    re.MULTILINE,
)

# 标记区尾部锚点：匹配标记区之后的首行内容
_MARKER_SECTION_ANCHOR_TAIL = re.compile(r"^_VERSION_PATTERN", re.MULTILINE)

__all__ = [
    "SUMMARY_BEGIN",
    "SUMMARY_END",
    "_EXE_VERSION",
    "_EXE_VERSION_PATTERN",
    "_VERSION",
    "_VERSION_PATTERN",
    "build_commit_message",
    "bump_minor",
    "bump_patch",
    "classify_changed_paths",
    "ensure_summary_marker_assignments",
    "format_semver",
    "get_exe_version",
    "get_version",
    "parse_semver",
    "please_read_me_path",
    "read_exe_version",
    "read_summary_for_commit",
    "read_version",
    "remove_summary_block",
    "strip_summary_block",
    "summarize_changes",
    "write_summary_block",
    "write_version",
]


def please_read_me_path(repo_root: Path | None = None) -> Path:
    """返回 _version.py 的路径（版本唯一源头）。

    历史说明：旧名为 `please_read_me_path`，因版本常量原在
    `please_read_me.py` 中。现常量已迁移到此文件，但函数名
    保留以保持调用兼容。
    """
    root = repo_root or Path(__file__).resolve().parent
    return root / "_version.py"


def parse_semver(version: str) -> tuple[int, int, int]:
    """解析语义化版本字符串为三元组。"""
    parts = version.strip().split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"无效语义化版本: {version!r}（需要 MAJOR.MINOR.PATCH）")
    return int(parts[0]), int(parts[1]), int(parts[2])


def format_semver(major: int, minor: int, patch: int) -> str:
    """将整数三元组格式化为语义化版本字符串。"""
    return f"{major}.{minor}.{patch}"


def read_version(path: Path | None = None) -> str:
    """从 _version.py 读取 _VERSION。"""
    path = path or please_read_me_path()
    text = path.read_text(encoding="utf-8")
    match = _VERSION_PATTERN.search(text)
    if not match:
        raise ValueError(f"未在 {path} 中找到 _VERSION")
    return match.group(2)


def read_exe_version(path: Path | None = None) -> str:
    """从 _version.py 读取 _EXE_VERSION。"""
    path = path or please_read_me_path()
    text = path.read_text(encoding="utf-8")
    match = _EXE_VERSION_PATTERN.search(text)
    if not match:
        raise ValueError(f"未在 {path} 中找到 _EXE_VERSION")
    return match.group(2)


def write_version(path: Path | None, new_version: str) -> None:
    """将新版本号写入 _version.py 的 _VERSION。"""
    path = path or please_read_me_path()
    text = path.read_text(encoding="utf-8")
    if not _VERSION_PATTERN.search(text):
        raise ValueError(f"未在 {path} 中找到 _VERSION")
    updated = _VERSION_PATTERN.sub(
        rf"\g<1>{new_version}\g<3>",
        text,
        count=1,
    )
    path.write_text(updated, encoding="utf-8")
    ensure_summary_marker_assignments(path)


def bump_patch(version: str) -> str:
    """版本号第三位 +1。"""
    major, minor, patch = parse_semver(version)
    return format_semver(major, minor, patch + 1)


def bump_minor(version: str) -> str:
    """版本号第二位 +1，第三位置零。"""
    major, minor, _patch = parse_semver(version)
    return format_semver(major, minor + 1, 0)


def _canonical_marker_header() -> str:
    """返回 _version.py 顶部 UPLOAD_SUMMARY 标记区 canonical 文本。

    注意：此处使用硬编码字面量而非模块级变量 ``_SUMMARY_MARKER_BEGIN`` /
    ``_SUMMARY_MARKER_END``，因为当标记区损坏时这些模块变量可能是
    空字符串或未定义，使用它们会导致"修复"后仍然损坏。
    """
    return (
        '_SUMMARY_MARKER_BEGIN = ""\n'
        "_UPLOAD_SUMMARY_BEGIN = _SUMMARY_MARKER_BEGIN\n"
        "_UPLOAD_SUMMARY_END = _SUMMARY_MARKER_END\n"
        "SUMMARY_BEGIN = _UPLOAD_SUMMARY_BEGIN\n"
        "SUMMARY_END = _UPLOAD_SUMMARY_END\n"
    )


def _markers_section_ok(text: str) -> bool:
    """判断磁盘上的标记区是否完整且标记值非空字符串。

    使用硬编码值判断，避免模块变量为 ``""`` 时误判。
    """
    required_lines = (
        '_SUMMARY_MARKER_BEGIN = ""',
        "_UPLOAD_SUMMARY_BEGIN = _SUMMARY_MARKER_BEGIN",
        "_UPLOAD_SUMMARY_END = _SUMMARY_MARKER_END",
        "SUMMARY_BEGIN = _UPLOAD_SUMMARY_BEGIN",
        "SUMMARY_END = _UPLOAD_SUMMARY_END",
    )
    if any(line not in text for line in required_lines):
        return False
    # 确认标记值不是空字符串
    return (
        re.search(
            r'^_(?:UPLOAD_SUMMARY|SUMMARY_MARKER)_(?:BEGIN|END)\s*=\s*""\s*(?:\r)?$',
            text,
            re.MULTILINE,
        )
        is None
        and "_SUMMARY_MARKER_BEGIN" in text
        and "_SUMMARY_MARKER_END" in text
    )


def ensure_summary_marker_assignments(path: Path | None = None) -> bool:
    """修正 _version.py 顶部 UPLOAD_SUMMARY 标记区（防止空字符串或缺行）。"""
    path = path or please_read_me_path()
    text = path.read_text(encoding="utf-8")
    if _markers_section_ok(text):
        return False
    anchor = "# ==============================================================\n\n"
    idx = text.find(anchor)
    if idx == -1:
        return False
    head_end = idx + len(anchor)
    tail = text[head_end:]
    cut = _MARKER_SECTION_ANCHOR_TAIL.search(tail)
    if not cut:
        return False
    updated = text[:head_end] + _canonical_marker_header() + tail[cut.start() :]
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def strip_summary_block(text: str) -> str:
    """从文本中移除 UPLOAD_SUMMARY 标记块。"""
    begin_marker = _SUMMARY_MARKER_BEGIN
    end_marker = _SUMMARY_MARKER_END
    begin = text.rfind(begin_marker)
    if begin == -1:
        return text.rstrip() + "\n"
    end = text.find(end_marker, begin)
    if end == -1:
        return text.rstrip() + "\n"
    end += len(end_marker)
    return (text[:begin] + text[end:]).rstrip() + "\n"


def write_summary_block(path: Path, title: str, bullets: list[str]) -> None:
    """将上传总结写入 _version.py 底部。"""
    ensure_summary_marker_assignments(path)
    text = strip_summary_block(path.read_text(encoding="utf-8"))
    lines = [
        "",
        _SUMMARY_MARKER_BEGIN,
        f"# TITLE: {title}",
        "# BODY:",
    ]
    for item in bullets:
        lines.append(f"# - {item}")
    lines.append(_SUMMARY_MARKER_END)
    lines.append("")
    path.write_text(text + "\n".join(lines), encoding="utf-8")


def remove_summary_block(path: Path) -> None:
    """从 _version.py 中移除 UPLOAD_SUMMARY 标记块。"""
    text = path.read_text(encoding="utf-8")
    path.write_text(strip_summary_block(text), encoding="utf-8")


def read_summary_for_commit(path: Path) -> tuple[str, list[str]]:
    """从 _version.py 解析 UPLOAD_SUMMARY 块的内容。"""
    text = path.read_text(encoding="utf-8")
    begin = text.rfind(_UPLOAD_SUMMARY_BEGIN)
    end = text.find(_UPLOAD_SUMMARY_END, begin)
    if begin == -1 or end == -1:
        raise ValueError("_version.py 中缺少 UPLOAD_SUMMARY 标记块")
    block = text[begin:end]
    title = "Update"
    bullets: list[str] = []
    in_body = False
    for raw in block.splitlines():
        line = raw.strip()
        if line.startswith("# TITLE:"):
            title = line[len("# TITLE:") :].strip()
        elif line.startswith("# BODY:"):
            in_body = True
        elif in_body and line.startswith("# -"):
            bullets.append(line[3:].strip())
        elif in_body and line.startswith("#") and not line.startswith("# ---"):
            bullets.append(line.lstrip("# ").strip())
    return title, bullets


def build_commit_message(version: str, title: str, bullets: list[str]) -> str:
    """构建 git commit 消息字符串。"""
    first = f"v{version}: {title}"
    if not bullets:
        return first
    return first + "\n\n" + "\n".join(f"- {b}" for b in bullets)


def classify_changed_paths(paths: list[str], package_dir_name: str = "games/endfield") -> bool:
    """判断变更路径列表中是否包含业务代码改动（非 _version.py 自身）。"""
    prefix = f"{package_dir_name}/"
    readme_names = {
        f"{prefix}_version.py",
        "_version.py",
        "scripts/_version.py",
        f"{prefix}please_read_me.py",
        "please_read_me.py",
        "scripts/please_read_me.py",
        "scripts/upload_meta.py",
        "scripts/version.py",
    }
    for raw in paths:
        norm = raw.replace("\\", "/").strip()
        if " -> " in norm:
            norm = norm.split(" -> ")[-1].strip()
        if norm in readme_names:
            continue
        if norm and norm != prefix.rstrip("/"):
            return True
    return False


def summarize_changes(paths: list[str]) -> tuple[str, list[str]]:
    """生成变更摘要信息（标题 + 更改列表）。"""
    unique = sorted({p.replace("\\", "/") for p in paths if p.strip()})
    if not unique:
        return "维护性更新", ["无文件列表（请检查 git status）"]

    bullets: list[str] = []
    for p in unique:
        if p.endswith("weapons.json"):
            bullets.append("更新 weapons.json 武器数据")
        elif p.endswith("characters.json"):
            bullets.append("更新 characters.json 角色数据")
        elif "multiplicative_zones" in p:
            bullets.append(f"调整乘区逻辑 {p}")
        elif p.endswith(".py"):
            bullets.append(f"修改 {p}")
        elif p.endswith(".md"):
            bullets.append(f"更新文档 {p}")
        else:
            bullets.append(f"变更 {p}")

    title = bullets[0] if len(bullets) == 1 else f"更新 {len(unique)} 处文件"
    return title, bullets


def get_version() -> str:
    """获取项目版本号。"""
    return _VERSION


def get_exe_version() -> str:
    """获取 EXE 版本号。"""
    return _EXE_VERSION


# TITLE: 更新 57 处文件
# BODY:
# - 变更 .gitignore
# - 修改 framework/src/calc_framework/ui/viewer_plugin_manager.py
# - 修改 games/arknights/tests/test_compact_apply_skip.py
# - 修改 games/arknights/tests/test_growth_compact.py
# - 修改 games/endfield/calc/dag_adapter/adapter.py
# - 修改 games/endfield/gui/endfield_app.py
# - 修改 games/endfield/gui/endfield_shell.py
# - 修改 games/endfield/main.py
# - 变更 games/endfield/tests/gui/manual/
# - 修改 games/endfield/tests/tools/test_migrate_weapon_skills_schema_tool.py
# - 修改 scripts/_version.py
# - 修改 scripts/tools/devtool.py
# - 修改 tools/check_code_origin.py
# - 修改 tools/check_layout.py
# - 修改 tools/check_optional_deps.py
# - 修改 tools/check_pyside6_coupling.py
# - 修改 tools/compact_arknights_operators.py
# - 修改 tools/compact_game_json.py
# - 修改 tools/data_pipeline/compact_arknights_operators.py
# - 修改 tools/data_pipeline/compact_game_json.py
# - 修改 tools/data_pipeline/sync_adapter_snapshots.py
# - 修改 tools/designer/validate_layout_sync.py
# - 修改 tools/export_sample_calcpacks.py
# - 修改 tools/framework_publish.py
# - 修改 tools/gen_architecture_review_html.py
# - 修改 tools/generate_secrets_baseline.py
# - 修改 tools/migrate_weapon_skills_schema.py
# - 修改 tools/plugin_pack.py
# - 修改 tools/publish/export_sample_calcpacks.py
# - 修改 tools/publish/framework_publish.py
# - 修改 tools/publish/plugin_pack.py
# - 修改 tools/quality/check_code_origin.py
# - 修改 tools/quality/check_pyside6_coupling.py
# - 修改 tools/quality/generate_secrets_baseline.py
# - 修改 tools/quality/sync_hub_catalog.py
# - 修改 tools/rename_pkg.py
# - 修改 tools/replace_adapters_imports.py
# - 修改 tools/replace_docs.py
# - 修改 tools/replace_paths.py
# - 修改 tools/run_scancode.py
# - 修改 tools/sync_adapter_snapshots.py
# - 修改 tools/sync_hub_catalog.py
# - 修改 tools/tests/test_compact_game_json.py
# - 修改 tools/tests/test_sync_adapter_snapshots.py
# - 修改 tools/validate_layout_sync.py
# - 修改 web/backend/api/adapter_lib/assets.py
# - 修改 web/backend/api/admin.py
# - 修改 web/backend/api/data.py
# - 变更 web/backend/api/data/search_history.json
# - 修改 web/backend/api/entity/inverse_payloads.py
# - 修改 web/backend/api/entity/profiles.py
# - 修改 web/backend/api/generator.py
# - 修改 web/backend/api/packaging/contribute.py
# - 修改 web/backend/api/packaging/pack.py
# - 修改 web/backend/api/plugins.py
# - 修改 web/backend/api/search.py
# - 修改 web/backend/tests/test_data_compact_api.py


# TITLE: 更新 40 处文件
# BODY:
# - 变更 .gitignore
# - 修改 framework/src/calc_framework/ui/viewer_plugin_manager.py
# - 修改 games/arknights/tests/test_compact_apply_skip.py
# - 修改 games/arknights/tests/test_growth_compact.py
# - 修改 games/endfield/calc/dag_adapter/adapter.py
# - 修改 games/endfield/gui/endfield_app.py
# - 修改 games/endfield/gui/endfield_shell.py
# - 修改 games/endfield/main.py
# - 修改 games/endfield/tests/gui/manual/test_gui_app.py
# - 修改 games/endfield/tests/gui/manual/test_gui_app2.py
# - 修改 games/endfield/tests/gui/manual/test_gui_controls.py
# - 修改 games/endfield/tests/gui/manual/test_gui_interactions.py
# - 修改 games/endfield/tests/tools/test_migrate_weapon_skills_schema_tool.py
# - 修改 scripts/_version.py
# - 修改 scripts/tools/devtool.py
# - 修改 tools/data_pipeline/compact_arknights_operators.py
# - 修改 tools/data_pipeline/compact_game_json.py
# - 修改 tools/data_pipeline/sync_adapter_snapshots.py
# - 修改 tools/designer/validate_layout_sync.py
# - 修改 tools/publish/export_sample_calcpacks.py
# - 修改 tools/publish/framework_publish.py
# - 修改 tools/publish/plugin_pack.py
# - 修改 tools/quality/check_code_origin.py
# - 修改 tools/quality/check_pyside6_coupling.py
# - 修改 tools/quality/generate_secrets_baseline.py
# - 修改 tools/quality/sync_hub_catalog.py
# - 修改 tools/tests/test_compact_game_json.py
# - 修改 tools/tests/test_sync_adapter_snapshots.py
# - 修改 web/backend/api/adapter_lib/assets.py
# - 修改 web/backend/api/admin.py
# - 修改 web/backend/api/data.py
# - 变更 web/backend/api/data/search_history.json
# - 修改 web/backend/api/entity/inverse_payloads.py
# - 修改 web/backend/api/entity/profiles.py
# - 修改 web/backend/api/generator.py
# - 修改 web/backend/api/packaging/contribute.py
# - 修改 web/backend/api/packaging/pack.py
# - 修改 web/backend/api/plugins.py
# - 修改 web/backend/api/search.py
# - 修改 web/backend/tests/test_data_compact_api.py


# TITLE: 更新 37 处文件
# BODY:
# - 变更 .gitignore
# - 修改 framework/src/calc_framework/ui/viewer_plugin_manager.py
# - 修改 games/arknights/tests/test_compact_apply_skip.py
# - 修改 games/arknights/tests/test_growth_compact.py
# - 修改 games/endfield/calc/dag_adapter/adapter.py
# - 修改 games/endfield/main.py
# - 修改 games/endfield/tests/gui/manual/test_gui_app.py
# - 修改 games/endfield/tests/gui/manual/test_gui_app2.py
# - 修改 games/endfield/tests/gui/manual/test_gui_controls.py
# - 修改 games/endfield/tests/gui/manual/test_gui_interactions.py
# - 修改 games/endfield/tests/tools/test_migrate_weapon_skills_schema_tool.py
# - 修改 scripts/_version.py
# - 修改 scripts/tools/devtool.py
# - 修改 tools/data_pipeline/compact_arknights_operators.py
# - 修改 tools/data_pipeline/compact_game_json.py
# - 修改 tools/data_pipeline/sync_adapter_snapshots.py
# - 修改 tools/designer/validate_layout_sync.py
# - 修改 tools/publish/export_sample_calcpacks.py
# - 修改 tools/publish/framework_publish.py
# - 修改 tools/publish/plugin_pack.py
# - 修改 tools/quality/check_code_origin.py
# - 修改 tools/quality/check_pyside6_coupling.py
# - 修改 tools/quality/generate_secrets_baseline.py
# - 修改 tools/quality/sync_hub_catalog.py
# - 修改 tools/tests/test_compact_game_json.py
# - 修改 tools/tests/test_sync_adapter_snapshots.py
# - 修改 web/backend/api/adapter_lib/assets.py
# - 修改 web/backend/api/admin.py
# - 修改 web/backend/api/data.py
# - 修改 web/backend/api/entity/inverse_payloads.py
# - 修改 web/backend/api/entity/profiles.py
# - 修改 web/backend/api/generator.py
# - 修改 web/backend/api/packaging/contribute.py
# - 修改 web/backend/api/packaging/pack.py
# - 修改 web/backend/api/plugins.py
# - 修改 web/backend/api/search.py
# - 修改 web/backend/tests/test_data_compact_api.py


# TITLE: 更新 477 处文件
# BODY:
# - 更新文档 docs/会话接续手册.md
# - 修改 framework/src/calc_framework/__init__.py
# - 修改 framework/src/calc_framework/config/__init__.py
# - 修改 framework/src/calc_framework/config/adapter.py
# - 修改 framework/src/calc_framework/dag/__init__.py
# - 修改 framework/src/calc_framework/dag/block_cache.py
# - 修改 framework/src/calc_framework/dag/engine.py
# - 修改 framework/src/calc_framework/dag/errors.py
# - 修改 framework/src/calc_framework/dag/graph.py
# - 修改 framework/src/calc_framework/dag/graph_types.py
# - 修改 framework/src/calc_framework/dag/node_types.py
# - 修改 framework/src/calc_framework/dag/sandbox.py
# - 修改 framework/src/calc_framework/dag/sandbox_config.py
# - 修改 framework/src/calc_framework/dag/schema.py
# - 修改 framework/src/calc_framework/dag/serializer.py
# - 修改 framework/src/calc_framework/dag/service.py
# - 修改 framework/src/calc_framework/dag/subgraph.py
# - 修改 framework/src/calc_framework/data/__init__.py
# - 修改 framework/src/calc_framework/data/attr_schema.py
# - 修改 framework/src/calc_framework/data/context.py
# - 修改 framework/src/calc_framework/data/loader.py
# - 修改 framework/src/calc_framework/data/schema.py
# - 修改 framework/src/calc_framework/errors.py
# - 修改 framework/src/calc_framework/graph_editor/__main__.py
# - 修改 games/__init__.py
# - 修改 games/arknights/gui/operator_combo.py
# - 修改 games/arknights/tests/test_compact_apply_skip.py
# - 修改 games/arknights/tests/test_operator_catalog.py
# - 修改 games/arknights/tests/test_operator_catalog_extended.py
# - 修改 games/endfield/calc/__init__.py
# - 修改 games/endfield/calc/core/__init__.py
# - 修改 games/endfield/calc/core/config.py
# - 修改 games/endfield/calc/core/curve_baker.py
# - 修改 games/endfield/calc/core/data_generator.py
# - 修改 games/endfield/calc/core/parallel_evaluate.py
# - 修改 games/endfield/calc/core/preview_cache.py
# - 修改 games/endfield/calc/core/result_cache.py
# - 修改 games/endfield/calc/core/result_export.py
# - 修改 games/endfield/calc/core/top_n_tracker.py
# - 修改 games/endfield/calc/dag_adapter/__init__.py
# - 修改 games/endfield/calc/dag_adapter/__main__.py
# - 修改 games/endfield/calc/dag_adapter/_subgraph_builders.py
# - 修改 games/endfield/calc/dag_adapter/adapter.py
# - 修改 games/endfield/calc/dag_adapter/config.py
# - 修改 games/endfield/calc/dag_adapter/loader.py
# - 修改 games/endfield/calc/dag_adapter/search_evaluate.py
# - 修改 games/endfield/calc/damage/__init__.py
# - 修改 games/endfield/calc/damage/engine/__init__.py
# - 修改 games/endfield/calc/damage/engine/calculate.py
# - 修改 games/endfield/calc/damage/engine/helpers.py
# - 修改 games/endfield/calc/damage/engine/types.py
# - 修改 games/endfield/calc/damage/formula.py
# - 修改 games/endfield/calc/damage/inverse/__init__.py
# - 修改 games/endfield/calc/damage/inverse/api.py
# - 修改 games/endfield/calc/damage/inverse/attribute.py
# - 修改 games/endfield/calc/damage/inverse/skill.py
# - 修改 games/endfield/calc/damage/types.py
# - 修改 games/endfield/calc/equipment/__init__.py
# - 修改 games/endfield/calc/equipment/affix.py
# - 修改 games/endfield/calc/equipment/prune.py
# - 修改 games/endfield/calc/equipment/system.py
# - 修改 games/endfield/calc/loadout/__init__.py
# - 修改 games/endfield/calc/loadout/attack_eval.py
# - 修改 games/endfield/calc/loadout/in_memory_optimizer.py
# - 修改 games/endfield/calc/loadout/optimizer/__init__.py
# - 修改 games/endfield/calc/loadout/optimizer/catalog.py
# - 修改 games/endfield/calc/loadout/optimizer/evaluate.py
# - 修改 games/endfield/calc/loadout/optimizer/plan.py
# - 修改 games/endfield/calc/loadout/optimizer/search.py
# - 修改 games/endfield/calc/loadout/optimizer/tasks.py
# - 修改 games/endfield/calc/loadout/optimizer/types.py
# - 修改 games/endfield/calc/loadout/slot_search.py
# - 修改 games/endfield/calc/manual_buff/__init__.py
# - 修改 games/endfield/calc/manual_buff/model.py
# - 修改 games/endfield/calc/manual_buff/physical.py
# - 修改 games/endfield/calc/manual_buff/spell.py
# - 修改 games/endfield/calc/manual_buff/spell_params.py
# - 修改 games/endfield/calc/multi_skill/__init__.py
# - 修改 games/endfield/calc/multi_skill/optimizer/__init__.py
# - 修改 games/endfield/calc/multi_skill/optimizer/search.py
# - 修改 games/endfield/calc/multi_skill/optimizer/types.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/__init__.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/_attribute_zone_bonus.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/ability_bonus_calc.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/ability_bonus_details.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/attribute_zone.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/base_zone.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/final_attack_zone.py
# - 调整乘区逻辑 games/endfield/calc/multiplicative_zones/zone_manager.py
# - 修改 games/endfield/calc/search/__init__.py
# - 修改 games/endfield/calc/search/evaluate/__init__.py
# - 修改 games/endfield/calc/search/evaluate/batch_score.py
# - 修改 games/endfield/calc/search/evaluate/context.py
# - 修改 games/endfield/calc/search/evaluate/multi_skill.py
# - 修改 games/endfield/calc/search/evaluate/process_worker.py
# - 修改 games/endfield/calc/search/evaluate/task.py
# - 修改 games/endfield/calc/search/evaluate/task_batch.py
# - 修改 games/endfield/calc/search/persist/__init__.py
# - 修改 games/endfield/calc/search/persist/schema.py
# - 修改 games/endfield/calc/search/persist/store.py
# - 修改 games/endfield/calc/search/plan/__init__.py
# - 修改 games/endfield/calc/search/plan/controller.py
# - 修改 games/endfield/calc/search/plan/estimate.py
# - 修改 games/endfield/calc/search/plan/job.py
# - 修改 games/endfield/calc/search/run/__init__.py
# - 修改 games/endfield/calc/search/run/cancel.py
# - 修改 games/endfield/calc/search/run/mvp.py
# - 修改 games/endfield/calc/search/run/parallel.py
# - 修改 games/endfield/calc/search/run/runner.py
# - 修改 games/endfield/calc/search/run/single_skill.py
# - 修改 games/endfield/calc/skills/__init__.py
# - 修改 games/endfield/calc/skills/segments.py
# - 修改 games/endfield/calc/skills/special_fields/__init__.py
# - 修改 games/endfield/calc/skills/special_fields/codec.py
# - 修改 games/endfield/calc/skills/special_fields/name_utils.py
# - 修改 games/endfield/calc/skills/special_fields/runtime_bonus.py
# - 修改 games/endfield/calc/skills/special_fields/skills_schema.py
# - 修改 games/endfield/calc/skills/special_fields/slots_io.py
# - 修改 games/endfield/calc/skills/weapon_selection.py
# - 修改 games/endfield/calc/zone_snapshot/__init__.py
# - 修改 games/endfield/calc/zone_snapshot/compute.py
# - 修改 games/endfield/calc/zone_snapshot/types.py
# - 修改 games/endfield/data_loading/curve_materialize.py
# - 修改 games/endfield/data_loading/enemy_params.py
# - 修改 games/endfield/data_loading/equipment_catalog.py
# - 修改 games/endfield/data_loading/equipment_filters.py
# - 修改 games/endfield/data_loading/game_data_facade.py
# - 修改 games/endfield/data_loading/loader.py
# - 修改 games/endfield/data_loading/loader_crud.py
# - 修改 games/endfield/data_loading/plugin_registry.py
# - 修改 games/endfield/data_loading/web_context_enrich.py
# - 修改 games/endfield/gui/app/__init__.py
# - 修改 games/endfield/gui/app/confirm_refresh.py
# - 修改 games/endfield/gui/app/display_request.py
# - 修改 games/endfield/gui/app/loadout_evaluation.py
# - 修改 games/endfield/gui/app/loadout_preset.py
# - 修改 games/endfield/gui/app/loadout_serialize.py
# - 修改 games/endfield/gui/app/loadout_state.py
# - 修改 games/endfield/gui/controls/__init__.py
# - 修改 games/endfield/gui/controls/enemy/__init__.py
# - 修改 games/endfield/gui/controls/enemy/qt_enemy_panel.py
# - 修改 games/endfield/gui/controls/enhancement/__init__.py
# - 修改 games/endfield/gui/controls/enhancement/qt_dialogs.py
# - 修改 games/endfield/gui/controls/manual_buff/__init__.py
# - 修改 games/endfield/gui/controls/manual_buff/qt_window.py
# - 修改 games/endfield/gui/controls/multi_skill/__init__.py
# - 修改 games/endfield/gui/controls/ocr/__init__.py
# - 修改 games/endfield/gui/controls/ocr/detection_dialog.py
# - 修改 games/endfield/gui/controls/ocr/ocr_detect.py
# - 修改 games/endfield/gui/controls/search/__init__.py
# - 修改 games/endfield/gui/controls/search/qt_actions.py
# - 修改 games/endfield/gui/controls/search/qt_search_browser.py
# - 修改 games/endfield/gui/controls/search/search_estimate_message.py
# - 修改 games/endfield/gui/controls/search/search_settings.py
# - 修改 games/endfield/gui/controls/survival/qt_survival_dialog.py
# - 修改 games/endfield/gui/designer/data_browser_tab.py
# - 修改 games/endfield/gui/designer/data_editor_tab.py
# - 修改 games/endfield/gui/designer/designer_main.py
# - 修改 games/endfield/gui/designer/inverse_tab.py
# - 修改 games/endfield/gui/layout/__init__.py
# - 修改 games/endfield/gui/layout/gui_layout.py
# - 修改 games/endfield/gui/legal/attribution_content.py
# - 修改 games/endfield/gui/panels/__init__.py
# - 修改 games/endfield/gui/panels/selection/__init__.py
# - 修改 games/endfield/gui/panels/selection/qt_ability_panel.py
# - 修改 games/endfield/gui/panels/selection/qt_panel.py
# - 修改 games/endfield/gui/panels/selection/qt_panel_getters_mixin.py
# - 修改 games/endfield/gui/panels/selection/qt_subpanels.py
# - 修改 games/endfield/gui/panels/special_ability/__init__.py
# - 修改 games/endfield/gui/presentation/__init__.py
# - 修改 games/endfield/gui/presentation/damage_snapshot.py
# - 修改 games/endfield/gui/presentation/display/__init__.py
# - 修改 games/endfield/gui/presentation/display/character.py
# - 修改 games/endfield/gui/presentation/display/format.py
# - 修改 games/endfield/gui/presentation/display/single_hit.py
# - 修改 games/endfield/gui/presentation/display/skill_resolve.py
# - 修改 games/endfield/gui/presentation/display_lines.py
# - 修改 games/endfield/gui/presentation/preview/__init__.py
# - 修改 games/endfield/gui/presentation/preview/multi_skill.py
# - 修改 games/endfield/gui/presentation/preview/single_skill.py
# - 修改 games/endfield/gui/presentation/preview_lines.py
# - 修改 games/endfield/gui/presentation/search_results_lines.py
# - 修改 games/endfield/gui/shared/__init__.py
# - 修改 games/endfield/gui/shared/calc_history.py
# - 修改 games/endfield/gui/shared/calc_mode_labels.py
# - 修改 games/endfield/gui/shared/damage_visualization.py
# - 修改 games/endfield/gui/shared/display_view/qt_columns.py
# - 修改 games/endfield/gui/shared/preset_batch_compare.py
# - 修改 games/endfield/gui/shared/ui_preferences.py
# - 修改 games/endfield/gui/shared/weapon_display_text.py
# - 修改 games/endfield/gui/shell/__init__.py
# - 修改 games/endfield/gui/shell/qt_control_dock.py
# - 修改 games/endfield/gui/shell/qt_factory.py
# - 修改 games/endfield/gui/shell/qt_worker.py
# - 修改 games/endfield/main.py
# - 修改 games/endfield/please_read_me.py
# - 修改 games/endfield/tests/calculation/core/test_result_cache.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_calculation.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_damage_engine.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_damage_types.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_damage_visualization.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_decimal_scaling.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_manual_buff.py
# - 修改 games/endfield/tests/calculation/damage/engine/test_scaling_mode.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_calc_chain_naming_compat.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_curve_baker.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_dag_adapter.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_damage_snapshot.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_damage_snapshot_manual_buff.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_inverse_refactored.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_result_export.py
# - 修改 games/endfield/tests/calculation/damage/zones/test_zone_snapshot.py
# - 修改 games/endfield/tests/calculation/equipment/test_equipment_affix.py
# - 修改 games/endfield/tests/calculation/equipment/test_equipment_catalog.py
# - 修改 games/endfield/tests/calculation/equipment/test_equipment_filters.py
# - 修改 games/endfield/tests/calculation/equipment/test_equipment_prune.py
# - 修改 games/endfield/tests/calculation/equipment/test_equipment_sync.py
# - 修改 games/endfield/tests/calculation/equipment/test_equipment_system.py
# - 修改 games/endfield/tests/calculation/loadout/optimizer/test_fixed_loadout_selection.py
# - 修改 games/endfield/tests/calculation/loadout/optimizer/test_loadout_optimizer.py
# - 修改 games/endfield/tests/calculation/loadout/optimizer/test_loadout_varying_slots.py
# - 修改 games/endfield/tests/calculation/loadout/optimizer/test_streaming_optimizer.py
# - 修改 games/endfield/tests/calculation/loadout/state/test_loadout_attack_eval.py
# - 修改 games/endfield/tests/calculation/loadout/state/test_loadout_evaluation.py
# - 修改 games/endfield/tests/calculation/loadout/state/test_loadout_preset.py
# - 修改 games/endfield/tests/calculation/loadout/state/test_loadout_state.py
# - 修改 games/endfield/tests/calculation/loadout/state/test_weapon_skill_selection.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_abnormal_manual_buff.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_abnormal_matrix.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_manual_buff_model.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_nga_batch10.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_nga_batch11.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_nga_batch13.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_nga_batch3.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_nga_batch4.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_nga_batch6.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_nga_batch7.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_nga_batch8.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_nga_batch9.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_nga_mechanics.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_spell_abnormal.py
# - 修改 games/endfield/tests/calculation/manual_buff/test_spell_abnormal_params.py
# - 修改 games/endfield/tests/calculation/multi_skill/test_multi_skill_counts.py
# - 修改 games/endfield/tests/calculation/multi_skill/test_multi_skill_optimizer.py
# - 修改 games/endfield/tests/calculation/search/evaluate/test_task_batch.py
# - 修改 games/endfield/tests/calculation/search/plan/single_skill/test_search_settings.py
# - 修改 games/endfield/tests/calculation/search/plan/single_skill/test_single_skill_search_job.py
# - 修改 games/endfield/tests/calculation/search/plan/single_skill/test_single_skill_search_preview.py
# - 修改 games/endfield/tests/calculation/search/plan/test_search_controller.py
# - 修改 games/endfield/tests/calculation/search/plan/test_search_controls.py
# - 修改 games/endfield/tests/calculation/search/plan/test_search_error_binding.py
# - 修改 games/endfield/tests/calculation/search/plan/test_search_estimate.py
# - 修改 games/endfield/tests/calculation/search/plan/test_search_export_paths.py
# - 修改 games/endfield/tests/calculation/search/plan/test_search_format.py
# - 修改 games/endfield/tests/calculation/search/run/test_bounded_parallel.py
# - 修改 games/endfield/tests/calculation/search/run/test_multi_skill_full_search.py
# - 修改 games/endfield/tests/calculation/search/run/test_mvp_pipeline.py
# - 修改 games/endfield/tests/calculation/search/run/test_parallel_evaluate.py
# - 修改 games/endfield/tests/calculation/search/run/test_process_parallel.py
# - 修改 games/endfield/tests/calculation/search/run/test_search_persistence.py
# - 修改 games/endfield/tests/calculation/search/run/test_search_results_view.py
# - 修改 games/endfield/tests/calculation/search/run/test_search_runner.py
# - 修改 games/endfield/tests/calculation/search/run/test_search_session.py
# - 修改 games/endfield/tests/calculation/search/run/test_single_skill_search_runner.py
# - 修改 games/endfield/tests/calculation/search/run/test_top_n_tracker.py
# - 修改 games/endfield/tests/calculation/skills/test_skill_segments.py
# - 修改 games/endfield/tests/calculation/skills/test_skill_tables_damage_type.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_add_character.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_add_weapon.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_weapon_dual_special.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_weapon_property_display.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_weapon_special_fields.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_weapon_special_level.py
# - 修改 games/endfield/tests/character_weapon_equipment/test_weapon_special_stack_layers.py
# - 修改 games/endfield/tests/conftest.py
# - 修改 games/endfield/tests/data/test_curve_materialize.py
# - 修改 games/endfield/tests/data/test_enemy_params.py
# - 修改 games/endfield/tests/data/test_game_data_contract.py
# - 修改 games/endfield/tests/data/test_game_data_facade.py
# - 修改 games/endfield/tests/data/test_gui_data_load.py
# - 修改 games/endfield/tests/data/test_loader_errors.py
# - 修改 games/endfield/tests/data/test_pack_data_paths.py
# - 修改 games/endfield/tests/data/test_plugin_registry.py
# - 修改 games/endfield/tests/data/test_unified_data_generator.py
# - 修改 games/endfield/tests/data_loading/test_web_context_enrich.py
# - 修改 games/endfield/tests/framework/test_endfield_dag_integration.py
# - 修改 games/endfield/tests/gui_design/app/test_confirm_orchestrator.py
# - 修改 games/endfield/tests/gui_design/app/test_confirm_refresh.py
# - 修改 games/endfield/tests/gui_design/app/test_confirm_selection_skill_levels.py
# - 修改 games/endfield/tests/gui_design/app/test_confirm_selection_state.py
# - 修改 games/endfield/tests/gui_design/app/test_loadout_evaluation_orchestration.py
# - 修改 games/endfield/tests/gui_design/controls/__init__.py
# - 修改 games/endfield/tests/gui_design/controls/enemy/__init__.py
# - 修改 games/endfield/tests/gui_design/controls/enemy/test_qt_enemy_panel.py
# - 修改 games/endfield/tests/gui_design/controls/enhancement/__init__.py
# - 修改 games/endfield/tests/gui_design/controls/enhancement/test_qt_dialogs.py
# - 修改 games/endfield/tests/gui_design/controls/search/__init__.py
# - 修改 games/endfield/tests/gui_design/controls/test_frozen_search_export_paths.py
# - 修改 games/endfield/tests/gui_design/layout/__init__.py
# - 修改 games/endfield/tests/gui_design/layout/test_gui_layout.py
# - 修改 games/endfield/tests/gui_design/legal/test_donation_qt.py
# - 修改 games/endfield/tests/gui_design/panels/selection/__init__.py
# - 修改 games/endfield/tests/gui_design/panels/selection/test_qt_subpanels.py
# - 修改 games/endfield/tests/gui_design/presentation/display/test_display_lines_module.py
# - 修改 games/endfield/tests/gui_design/presentation/display/test_property_display_lines.py
# - 修改 games/endfield/tests/gui_design/presentation/preview/test_multi_skill_search_preview.py
# - 修改 games/endfield/tests/gui_design/presentation/preview/test_preview_cache.py
# - 修改 games/endfield/tests/gui_design/presentation/preview/test_single_hit_preview.py
# - 修改 games/endfield/tests/gui_design/presentation/test_property_display_cache.py
# - 修改 games/endfield/tests/gui_design/presentation/test_total_damage_panel.py
# - 修改 games/endfield/tests/gui_design/shared/test_operation_log.py
# - 修改 games/endfield/tests/gui_design/shared/ui/test_ui_preferences.py
# - 修改 games/endfield/tests/gui_design/shell/test_gui_layout_contract.py
# - 修改 games/endfield/tests/gui_design/shell/test_qt_control_dock_widgets.py
# - 修改 games/endfield/tests/gui_design/shell/test_qt_factory.py
# - 修改 games/endfield/tests/gui_design/shell/test_shell_init.py
# - 修改 games/endfield/tests/gui_design/shell/test_weapon_panel_layout.py
# - 修改 games/endfield/tests/repo/test_build_watchdog.py
# - 修改 games/endfield/tests/repo/test_config.py
# - 修改 games/endfield/tests/repo/test_coverage_boost_misc.py
# - 修改 games/endfield/tests/repo/test_gitignore_contract.py
# - 修改 games/endfield/tests/repo/test_legal_attribution.py
# - 修改 games/endfield/tests/repo/test_optional_deps.py
# - 修改 games/endfield/tests/repo/test_readme_layers.py
# - 修改 games/endfield/tests/repo/test_release_layout.py
# - 修改 games/endfield/tests/repo/test_repo_layout.py
# - 修改 games/endfield/tests/repo/test_repo_release_layout.py
# - 修改 games/endfield/tests/test_qt_imports.py
# - 修改 games/endfield/tests/tools/test_bwiki_scout.py
# - 修改 games/endfield/tests/tools/test_git_backup.py
# - 修改 games/endfield/tests/tools/test_github_upload_signing.py
# - 修改 games/endfield/tests/tools/test_import_targets.py
# - 修改 games/endfield/tests/tools/test_migrate_weapon_skills_schema_tool.py
# - 修改 games/endfield/tests/tools/test_upload_meta.py
# - 修改 games/endfield/tests/tools/test_wiki_sync.py
# - 修改 games/endfield/tests/utils/test_donation_paths.py
# - 修改 games/endfield/tests/utils/test_platform_win32_patch.py
# - 修改 games/endfield/tests/utils/test_replace_imports.py
# - 修改 scripts/deploy_pythonanywhere.py
# - 修改 scripts/devtool.py
# - 修改 scripts/github_download_module.py
# - 修改 scripts/github_upload_module.py
# - 修改 scripts/import_calcpack.py
# - 修改 scripts/main_build.py
# - 修改 scripts/main_launcher.py
# - 修改 scripts/please_read_me.py
# - 修改 scripts/tools/batch_export_calcpack.py
# - 修改 scripts/tools/deploy_pythonanywhere.py
# - 修改 scripts/tools/devtool.py
# - 修改 scripts/tools/git_backup.py
# - 修改 scripts/tools/github_download_module.py
# - 修改 scripts/tools/github_upload_module.py
# - 修改 scripts/tools/import_calcpack.py
# - 修改 scripts/upload_meta.py
# - 修改 scripts/version.py
# - 修改 tools/__init__.py
# - 修改 tools/arknights_scout/__init__.py
# - 修改 tools/bwiki_scout/__init__.py
# - 修改 tools/bwiki_scout/__main__.py
# - 修改 tools/bwiki_scout/api.py
# - 修改 tools/bwiki_scout/backfill_weapon_max_stack.py
# - 修改 tools/bwiki_scout/bump_data_version.py
# - 修改 tools/bwiki_scout/compare_stats.py
# - 修改 tools/bwiki_scout/config.py
# - 修改 tools/bwiki_scout/detail_levels.py
# - 修改 tools/bwiki_scout/equipment_sync.py
# - 修改 tools/bwiki_scout/equipment_wiki.py
# - 修改 tools/bwiki_scout/gallery.py
# - 修改 tools/bwiki_scout/import_targets.py
# - 修改 tools/bwiki_scout/incremental_sync.py
# - 修改 tools/bwiki_scout/json_scan.py
# - 修改 tools/bwiki_scout/local_schema.py
# - 修改 tools/bwiki_scout/migrate_weapon_special_json.py
# - 修改 tools/bwiki_scout/names.py
# - 修改 tools/bwiki_scout/parse_draft.py
# - 修改 tools/bwiki_scout/pkg_bootstrap.py
# - 修改 tools/bwiki_scout/report.py
# - 修改 tools/bwiki_scout/scout.py
# - 修改 tools/bwiki_scout/seed_persist.py
# - 修改 tools/bwiki_scout/skill_tables.py
# - 修改 tools/bwiki_scout/storage.py
# - 修改 tools/bwiki_scout/sync_all.py
# - 修改 tools/bwiki_scout/sync_equipments.py
# - 修改 tools/bwiki_scout/sync_operators.py
# - 修改 tools/bwiki_scout/sync_weapons.py
# - 修改 tools/bwiki_scout/weapon_wiki.py
# - 修改 tools/bwiki_scout/wiki_sync.py
# - 修改 tools/data_pipeline/__init__.py
# - 修改 tools/data_pipeline/__main__.py
# - 修改 tools/data_pipeline/cli.py
# - 修改 tools/data_pipeline/compact_arknights_operators.py
# - 修改 tools/data_pipeline/compact_game_json.py
# - 修改 tools/data_pipeline/diff.py
# - 修改 tools/data_pipeline/readers/__init__.py
# - 修改 tools/data_pipeline/readers/csv_reader.py
# - 修改 tools/data_pipeline/readers/json_reader.py
# - 修改 tools/data_pipeline/schema.py
# - 修改 tools/data_pipeline/sync_adapter_snapshots.py
# - 修改 tools/data_pipeline/transformers/__init__.py
# - 修改 tools/data_pipeline/transformers/from_arknights_scout.py
# - 修改 tools/data_pipeline/transformers/from_legacy_endfield.py
# - 修改 tools/data_pipeline/transformers/to_standard.py
# - 修改 tools/data_pipeline/validators/__init__.py
# - 修改 tools/data_pipeline/validators/schema_check.py
# - 修改 tools/data_sandbox/__init__.py
# - 修改 tools/data_sandbox/reporter.py
# - 修改 tools/data_sandbox/sandbox.py
# - 修改 tools/data_sandbox/tester.py
# - 修改 tools/data_sandbox/validator.py
# - 修改 tools/designer/__init__.py
# - 修改 tools/designer/__main__.py
# - 修改 tools/designer/data_editor/__init__.py
# - 修改 tools/designer/exporter.py
# - 修改 tools/designer/layout_editor/__init__.py
# - 修改 tools/designer/layout_editor/collision.py
# - 修改 tools/designer/theme_editor/__init__.py
# - 修改 tools/designer/theme_editor/panel.py
# - 修改 tools/designer/validate_layout_sync.py
# - 修改 tools/endfield_designer/__init__.py
# - 修改 tools/endfield_designer/__main__.py
# - 修改 tools/endfield_designer/data_browser_tab.py
# - 修改 tools/endfield_designer/designer_main.py
# - 修改 tools/endfield_designer/inverse_tab.py
# - 修改 tools/endfield_scripts/__init__.py
# - 修改 tools/endfield_scripts/add_character.py
# - 修改 tools/endfield_scripts/add_weapon.py
# - 修改 tools/endfield_scripts/inverse_cli.py
# - 修改 tools/endfield_scripts/seed_characters.py
# - 修改 tools/endfield_scripts/seed_weapons.py
# - 修改 tools/generate_endfield_zone_package.py
# - 修改 tools/migration/__init__.py
# - 修改 tools/migration/migrate_weapon_skills_schema.py
# - 修改 tools/migration/rename_pkg.py
# - 修改 tools/migration/replace_adapters_imports.py
# - 修改 tools/migration/replace_docs.py
# - 修改 tools/migration/replace_paths.py
# - 修改 tools/ocr/cli.py
# - 修改 tools/ocr/collector.py
# - 修改 tools/ocr/download_models.py
# - 修改 tools/ocr/label.py
# - 修改 tools/ocr/mapper.py
# - 修改 tools/ocr/recognizer.py
# - 修改 tools/ocr/train.py
# - 修改 tools/publish/__init__.py
# - 修改 tools/publish/export_sample_calcpacks.py
# - 修改 tools/publish/framework_publish.py
# - 修改 tools/publish/generate_endfield_zone_package.py
# - 修改 tools/publish/sync_hub_catalog.py
# - 修改 tools/quality/__init__.py
# - 修改 tools/quality/add_encoding_declaration.py
# - 修改 tools/quality/check_code_origin.py
# - 修改 tools/quality/check_layout.py
# - 修改 tools/quality/check_optional_deps.py
# - 修改 tools/quality/check_pyside6_coupling.py
# - 修改 tools/quality/gen_architecture_review_html.py
# - 修改 tools/quality/generate_secrets_baseline.py
# - 修改 tools/quality/run_scancode.py
# - 修改 tools/quality/sync_hub_catalog.py
# - 修改 tools/quality/validate_layout_sync.py
# - 修改 tools/scaffold.py
# - 修改 tools/tests/test_arknights_data_pipeline.py
# - 修改 tools/tests/test_compact_game_json.py
# - 修改 web/backend/tests/test_api_integration.py
# - 修改 web/backend/tests/test_arknights_data_fallback.py
# - 修改 web/backend/tests/test_data_compact_api.py
# - 修改 web/backend/tests/test_enemy_choices_api.py
# - 修改 web/backend/tests/test_inverse_api.py
# - 修改 web/backend/tests/test_search_score_batch.py
# - 修改 web/backend/tests/test_search_slim_api.py
# - 修改 web/backend/tests/test_wasm_golden.py
# - 变更 web/frontend/src/components/calculator/AiRecommendDialog.tsx
# - 变更 web/frontend/src/components/dag/DagEditorCanvas.tsx
# - 变更 web/frontend/src/pages/AIFormulaDialog.tsx
# - 变更 web/frontend/src/pages/ArknightsComputePage.tsx
# - 变更 web/frontend/src/pages/ComputePage.tsx
# - 变更 web/frontend/src/pages/EditorPage.tsx
# - 变更 web/frontend/src/pages/GeneratorPage.tsx
