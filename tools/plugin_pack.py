"""
.calcplugin 打包/安装工具。

.calcplugin 格式：ZIP 包，包含:
  - plugin.json       — 插件元数据（必需）
  - variables.json    — 变量声明（可选）
  - templates.json    — DAG 模板定义（可选）
  - functions/        — Python 函数模块（可选）
  - README.md         — 使用说明（可选）

用法::

    # 打包插件目录
    python tools/plugin_pack.py build path/to/plugin_dir -o output.calcplugin

    # 安装插件
    python tools/plugin_pack.py install path/to/plugin.calcplugin
"""

from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path


def build_plugin(plugin_dir: str | Path, output: str | Path | None = None) -> Path:
    """将插件目录打包为 .calcplugin ZIP 文件。

    Args:
        plugin_dir: 插件源码目录（必须包含 plugin.json）
        output: 输出路径，为 None 时输出到当前目录

    Returns:
        生成的 .calcplugin 文件路径
    """
    src = Path(plugin_dir).resolve()
    meta_path = src / "plugin.json"
    if not meta_path.is_file():
        raise FileNotFoundError(f"插件目录缺少 plugin.json: {meta_path}")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    name = meta.get("name", src.name)
    version = meta.get("version", "1.0.0")

    if output is None:
        output = Path(f"{name}-{version}.calcplugin")
    else:
        output = Path(output)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath in src.rglob("*"):
            if fpath.is_file() and fpath.name != ".gitkeep":
                arcname = str(fpath.relative_to(src))
                zf.write(fpath, arcname)

    print(f"✓ 插件已打包: {output} ({output.stat().st_size / 1024:.1f} KB)")
    return output


def install_plugin(plugin_file: str | Path, target_dir: str | Path) -> Path:
    """安装 .calcplugin 文件到目标目录。

    Args:
        plugin_file: .calcplugin 文件路径
        target_dir: 插件安装目标目录（如 web/hub/plugins/）

    Returns:
        安装的插件目录路径
    """
    src = Path(plugin_file).resolve()
    if not src.is_file():
        raise FileNotFoundError(f"插件文件未找到: {src}")

    dst = Path(target_dir).resolve()
    dst.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(src, "r") as zf:
        meta = json.loads(zf.read("plugin.json").decode("utf-8"))
        name = meta.get("name", src.stem)
        version = meta.get("version", "1.0.0")
        plugin_dst = dst / f"{name}-{version}"
        if plugin_dst.exists():
            shutil.rmtree(plugin_dst)
        zf.extractall(str(plugin_dst))

    print(f"✓ 插件已安装: {plugin_dst}")
    return plugin_dst


def _demo_build(args: list[str]) -> int:
    if len(args) < 1:
        print("用法: python devtool.py plugin build <plugin_dir> [-o output]")
        return 1
    plugin_dir = args[0]
    output = args[2] if len(args) > 2 and args[1] == "-o" else None
    try:
        build_plugin(plugin_dir, output)
        return 0
    except Exception as e:
        print(f"✗ 打包失败: {e}", file=sys.stderr)
        return 1


def _demo_install(args: list[str]) -> int:
    if len(args) < 1:
        print("用法: python devtool.py plugin install <plugin.calcplugin>")
        return 1
    plugin_file = args[0]
    repo = Path(__file__).resolve().parents[1]
    target = repo / "web" / "hub" / "plugins"
    try:
        install_plugin(plugin_file, target)
        return 0
    except Exception as e:
        print(f"✗ 安装失败: {e}", file=sys.stderr)
        return 1
