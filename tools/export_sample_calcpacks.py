#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""从 framework/adapters 导出示例 .calcpack（fps / moba / card_rpg / simple / multi-zone）。

支持从已有适配器模板创建新的适配器包：

    python tools/export_sample_calcpacks.py --from-template simple --name "我的游戏" --output ./my_game.calcpack
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.designer.exporter import export_calcpack  # noqa: E402 — sys.path 必须优先设置

ADAPTER_ROOT = _REPO / "framework" / "adapters"
OUTPUT_DIR = _REPO / "web" / "hub" / "samples"
SAMPLE_IDS = ("fps", "moba", "card_rpg", "simple", "multi-zone")


def _load_json(path: Path) -> dict | list:
    """_load_json 实现。"""
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_dag_path(adapter_dir: Path, meta: dict) -> Path:
    """_resolve_dag_path 实现。"""
    entry = meta.get("entry_dag", "dag/formula.dag.json")
    candidates = [
        adapter_dir / entry,
        adapter_dir / "dag" / "formula.dag.json",
        adapter_dir / f"{adapter_dir.name}.dag.json",
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError(f"DAG not found for {adapter_dir.name}")


def _discover_templates() -> list[str]:
    """扫描 framework/adapters/ 下所有拥有 meta.json 的目录作为可用模板。

    Returns:
        模板 ID 列表（按字母序）。
    """
    templates: list[str] = []
    for child in sorted(ADAPTER_ROOT.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if (child / "meta.json").is_file():
            templates.append(child.name)
    return templates


def export_one(adapter_id: str) -> Path:
    """export_one 实现。

    Args:
        adapter_id: 参数描述。

    Returns:
        返回值描述。
    """
    adapter_dir = ADAPTER_ROOT / adapter_id
    meta = _load_json(adapter_dir / "meta.json")
    meta = dict(meta)
    meta["entry_dag"] = "dag/formula.dag.json"
    meta.setdefault("ui_layout", "ui/layout.json")

    dag = _load_json(_resolve_dag_path(adapter_dir, meta))
    layout_path = adapter_dir / meta.get("ui_layout", "ui/layout.json")
    layout = _load_json(layout_path)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"{adapter_id}_sample.calcpack"
    export_calcpack(
        output_path=out,
        meta=meta,
        dag=dag,
        layout=layout,
        theme=None,
        data_files=None,
    )
    return out


def _create_from_template(template_id: str, game_name: str, output_path: str) -> Path:
    """从模板目录创建新的适配器包。

    流程：
    1. 复制模板目录所有文件到临时目录
    2. 修改 meta.json 中的 name/game/entry_dag 字段
    3. 重命名 DAG 文件（从 {template_id}.dag.json → {game_name}.dag.json）
    4. 打包为 .calcpack 输出
    5. 清理临时目录

    Args:
        template_id: 模板 ID（对应 framework/adapters/<template_id>/）。
        game_name: 游戏名称，会写入 meta.json 的 name 和 game 字段。
        output_path: 输出 .calcpack 路径。

    Returns:
        实际写入的路径。

    Raises:
        FileNotFoundError: 模板目录或必要文件不存在。
    """
    src = ADAPTER_ROOT / template_id
    if not src.is_dir():
        msg = (
            f"模板 {template_id!r} 不存在于 {ADAPTER_ROOT}\n"
            f"可用模板: {', '.join(_discover_templates())}"
        )
        raise FileNotFoundError(msg)

    # 复制到临时目录
    tmp = Path(tempfile.mkdtemp(prefix=f"calcpack_{template_id}_"))
    try:
        # 复制所有文件（包括子目录）
        for item in src.rglob("*"):
            if item.is_file():
                rel = item.relative_to(src)
                dest = tmp / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(item), str(dest))
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise

    try:
        # 修改 meta.json
        meta_path = tmp / "meta.json"
        meta = _load_json(meta_path)
        orig_entry = meta.get("entry_dag", f"{template_id}.dag.json")
        meta["name"] = game_name
        meta["game"] = game_name
        meta["entry_dag"] = f"{game_name}.dag.json"
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # 重命名 DAG 文件
        old_dag = tmp / orig_entry
        new_dag = tmp / f"{game_name}.dag.json"
        if old_dag.is_file() and not new_dag.exists():
            old_dag.rename(new_dag)

        # 准备导出参数（与 export_one 逻辑一致）
        meta_for_export = dict(meta)
        meta_for_export["entry_dag"] = "dag/formula.dag.json"
        meta_for_export.setdefault("ui_layout", "ui/layout.json")

        # 加载 DAG（优先找重命名后的文件）
        dag_path = new_dag if new_dag.is_file() else tmp / orig_entry
        dag = _load_json(dag_path)

        layout_path = tmp / meta_for_export.get("ui_layout", "ui/layout.json")
        layout = _load_json(layout_path)

        out = export_calcpack(
            output_path=output_path,
            meta=meta_for_export,
            dag=dag,
            layout=layout,
            theme=None,
            data_files=None,
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return Path(out)


def _build_arg_parser() -> argparse.ArgumentParser:
    """构建 CLI 参数解析器。"""
    parser = argparse.ArgumentParser(
        description="导出示例 .calcpack 或从模板创建新的适配器包",
    )
    parser.add_argument(
        "--from-template",
        metavar="TEMPLATE_ID",
        default=None,
        help="从指定模板创建适配器包（可用模板见 --list-templates）",
    )
    parser.add_argument(
        "--name",
        default="我的游戏",
        help="游戏名称，用于 meta.json 的 name/game 字段（默认: %(default)s）",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出 .calcpack 路径（默认: {name}.calcpack）",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="列出可用的模板 ID",
    )
    return parser


def main() -> int:
    """CLI 入口。"""
    parser = _build_arg_parser()
    args = parser.parse_args()

    # --list-templates 优先
    if args.list_templates:
        templates = _discover_templates()
        print("可用模板:")
        for t in templates:
            print(f"  {t}")
        return 0

    # --from-template 模式
    if args.from_template:
        templates = _discover_templates()
        if args.from_template not in templates:
            print(
                f"错误: 模板 {args.from_template!r} 不存在。\n"
                f"可用模板: {', '.join(templates)}",
                file=sys.stderr,
            )
            return 1
        output = args.output or f"{args.name}.calcpack"
        try:
            path = _create_from_template(args.from_template, args.name, output)
        except FileNotFoundError as exc:
            print(f"错误: {exc}", file=sys.stderr)
            return 1
        print(f"OK {path}")
        return 0

    # 默认行为：导出所有示例 .calcpack
    written: list[str] = []
    for aid in SAMPLE_IDS:
        try:
            path = export_one(aid)
            written.append(str(path.relative_to(_REPO)))
            print(f"OK {path}")
        except FileNotFoundError as exc:
            print(f"跳过 {aid}: {exc}", file=sys.stderr)
    print(f"Exported {len(written)} sample calcpacks to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
