#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""一键批量导出：将 framework/adapters/ 下所有适配器打包为 .calcpack 示例文件。

用法::

    python scripts/tools/batch_export_calcpack.py          # 导出到 output/calcpack_examples/
    python scripts/tools/batch_export_calcpack.py --hub     # 导出后上传到 Calc Hub（Web 端）

"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_ADAPTERS = _REPO / "framework" / "adapters"
_DEFAULT_OUTPUT = _REPO / "output" / "calcpack_examples"


def export_all(output_dir: Path) -> list[Path]:
    """导出所有适配器为 .calcpack 文件，返回生成的文件路径列表。"""
    from tools.designer.exporter import export_calcpack

    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []

    if not _ADAPTERS.is_dir():
        print(f"[错误] 适配器目录不存在: {_ADAPTERS}")
        return results

    for adapter_dir in sorted(_ADAPTERS.iterdir()):
        if not adapter_dir.is_dir() or adapter_dir.name.startswith("_") or adapter_dir.name.startswith("."):
            continue

        meta_fp = adapter_dir / "meta.json"
        if not meta_fp.exists():
            print(f"[跳过] {adapter_dir.name}: 缺少 meta.json")
            continue

        try:
            meta = json.loads(meta_fp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[跳过] {adapter_dir.name}: meta.json 解析失败 ({e})")
            continue

        # 读取 DAG
        entry_dag = meta.get("entry_dag", "")
        dag: dict = {}
        if entry_dag:
            dag_paths = [adapter_dir / entry_dag, adapter_dir / "dag" / entry_dag]
            for dp in dag_paths:
                if dp.exists():
                    dag = json.loads(dp.read_text(encoding="utf-8"))
                    break

        if not dag:
            print(f"[跳过] {adapter_dir.name}: 找不到 DAG 文件")
            continue

        # 读取 layout
        layout: dict = {}
        ui_layout = meta.get("ui_layout", "")
        if ui_layout:
            layout_fp = adapter_dir / ui_layout
            if layout_fp.exists():
                layout = json.loads(layout_fp.read_text(encoding="utf-8"))

        if not layout:
            # 生成一个最小 layout
            layout = {
                "schema_version": "ui-v1",
                "name": meta.get("name", adapter_dir.name),
                "sections": [],
            }

        # 读取数据文件
        data_files: dict[str, list] = {}
        data_dir = adapter_dir / "data"
        if data_dir.is_dir():
            for df in data_dir.iterdir():
                if df.suffix == ".json":
                    try:
                        data_files[df.stem] = json.loads(df.read_text(encoding="utf-8"))
                    except Exception:
                        pass

        # 导出
        output_path = output_dir / f"{adapter_dir.name}.calcpack"
        try:
            result_path = export_calcpack(
                output_path=str(output_path),
                meta=meta,
                dag=dag,
                layout=layout,
                data_files=data_files if data_files else None,
            )
            size_kb = Path(result_path).stat().st_size / 1024
            data_info = ", ".join(f"{k}={len(v)}" for k, v in data_files.items()) if data_files else "无数据"
            print(f"[✓] {adapter_dir.name} → {Path(result_path).name} ({size_kb:.1f} KB, {data_info})")
            results.append(Path(result_path))
        except Exception as e:
            print(f"[✗] {adapter_dir.name}: 导出失败 ({e})")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="批量导出适配器为 .calcpack 示例包")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=str(_DEFAULT_OUTPUT),
        help=f"输出目录 (默认: {_DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--hub",
        action="store_true",
        help="导出后尝试上传到 Calc Hub",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    print(f"输出目录: {output_dir}")
    print(f"扫描适配器: {_ADAPTERS}")
    print()

    results = export_all(output_dir)

    print()
    print(f"完成: 共导出 {len(results)} 个 .calcpack 文件")

    if args.hub and results:
        print()
        print("上传到 Calc Hub...")
        _upload_to_hub(results)


def _upload_to_hub(pack_paths: list[Path]) -> None:
    """将 .calcpack 文件上传到 Calc Hub（本地 Web 后端）。"""
    import requests

    hub_url = "http://127.0.0.1:8180/api/hub/upload"
    for fp in pack_paths:
        try:
            with open(fp, "rb") as f:
                resp = requests.post(hub_url, files={"file": (fp.name, f, "application/zip")}, timeout=30)
                if resp.status_code == 200:
                    print(f"  [✓] {fp.name} 上传成功")
                else:
                    print(f"  [✗] {fp.name}: HTTP {resp.status_code} — {resp.text[:100]}")
        except Exception as e:
            print(f"  [✗] {fp.name}: {e}")


if __name__ == "__main__":
    main()
