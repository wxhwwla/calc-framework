#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""新游戏适配脚手架生成器。

从 ``docs/game-template/`` 复制骨架模板，执行占位符替换，
为新游戏快速搭建适配器骨架代码。
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path


_TEMPLATE_DIR_NAME = "_template"
_TEMPLATE_SNAKE = re.compile(r"_template")
_TEMPLATE_PASCAL = re.compile(r"TEMPLATE")


def _repo_root() -> Path:
    """_repo_root 实现。"""
    return Path(__file__).resolve().parent.parent


def _find_template_root() -> Path:
    """_find_template_root 实现。"""
    return _repo_root() / "docs" / "game-template"


def _validate_game_name(name: str) -> str:
    """验证游戏名称并返回 snake_case 格式。"""
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        raise ValueError(
            f"游戏名称必须是小写字母、数字和下划线，以字母开头。"
            f" 收到: {name!r}"
        )
    return name


def to_pascal_case(snake: str) -> str:
    """snake_case → PascalCase。"""
    return "".join(word.capitalize() for word in snake.split("_"))


def scaffold_game(game_name: str, *, force: bool = False) -> dict[str, Path]:
    """为新游戏创建适配器骨架。

    从 ``docs/game-template/`` 复制模板文件到两个目标位置：

    - ``games/{game_name}/`` — 游戏包 Python 源码
    - ``framework/adapters/{game_name}/`` — 框架适配器配置

    Args:
        game_name: 游戏名称（snake_case 小写字母+数字+下划线）
        force: 是否覆盖已存在的目录

    Returns:
        {位置说明: 目标路径} 映射

    Raises:
        ValueError: 游戏名称格式无效
        FileExistsError: 目标目录已存在且 force=False
    """
    validated = _validate_game_name(game_name)
    pascal = to_pascal_case(validated)
    repo = _repo_root()
    template_root = _find_template_root()

    targets = {
        "框架适配器": repo / "framework" / "adapters" / validated,
        "游戏包源码": repo / "games" / validated,
    }

    for label, target in targets.items():
        if target.exists() and not force:
            raise FileExistsError(
                f"{label} 目录已存在: {target}\n"
                f"如需覆盖，请添加 --force 参数"
            )

    os.makedirs(targets["框架适配器"], exist_ok=True)
    os.makedirs(targets["游戏包源码"], exist_ok=True)

    _copy_template_tree(
        template_root / "framework" / "adapters" / _TEMPLATE_DIR_NAME,
        targets["框架适配器"],
        validated,
        pascal,
    )
    _copy_template_tree(
        template_root / "games" / _TEMPLATE_DIR_NAME,
        targets["游戏包源码"],
        validated,
        pascal,
    )

    return targets


def _copy_template_tree(
    src: Path,
    dst: Path,
    game_snake: str,
    game_pascal: str,
) -> None:
    """递归复制模板目录树并替换占位符。"""
    if not src.is_dir():
        raise FileNotFoundError(f"模板目录不存在: {src}")

    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        target_dir = dst / rel
        os.makedirs(target_dir, exist_ok=True)

        for fname in files:
            src_file = Path(root) / fname
            new_fname = _replace_in_name(fname, game_snake)
            dst_file = target_dir / new_fname

            content = src_file.read_text(encoding="utf-8")
            content = _replace_in_content(content, game_snake, game_pascal)
            dst_file.write_text(content, encoding="utf-8")


def _replace_in_name(name: str, game_snake: str) -> str:
    """将文件名中的 _template 占位符替换为游戏名称。

    Args:
        name: 原始文件名
        game_snake: 游戏名称 snake_case

    Returns:
        替换后的文件名
    """
    return name.replace(_TEMPLATE_DIR_NAME, game_snake)


def _replace_in_content(content: str, game_snake: str, game_pascal: str) -> str:
    """将文件内容中的模板占位符替换为游戏名称。

    替换 _template（snake_case）、TEMPLATE（PascalCase）和 DISPLAY_NAME 占位符。

    Args:
        content: 文件内容
        game_snake: 游戏名称 snake_case
        game_pascal: 游戏名称 PascalCase

    Returns:
        替换后的文件内容
    """
    content = _TEMPLATE_SNAKE.sub(game_snake, content)
    content = _TEMPLATE_PASCAL.sub(game_pascal, content)
    content = content.replace("DISPLAY_NAME", game_pascal)
    return content


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(
        description="新游戏适配脚手架 — 从 game-template 生成骨架代码",
    )
    parser.add_argument("game_name", help="游戏名称（snake_case，如 'my_game'）")
    parser.add_argument(
        "--force",
        action="store_true",
        help="覆盖已存在的目录",
    )

    args = parser.parse_args(argv)

    try:
        targets = scaffold_game(args.game_name, force=args.force)
    except (ValueError, FileExistsError, FileNotFoundError) as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1

    print(f"✅ 已为新游戏 {args.game_name!r} 创建适配器骨架：")
    for label, path in targets.items():
        print(f"   {label}: {path}")

    pascal = to_pascal_case(args.game_name)
    print(f"\n📋 下一步：")
    print(f"   1. 创建 DAG 公式: framework/adapters/{args.game_name}/{args.game_name}.dag.json")
    print(f"   2. 实现数据加载器: games/{args.game_name}/calc/dag_adapter/loader.py")
    print(f"   3. 注册自定义函数: framework/adapters/{args.game_name}/functions.py")
    print(f"   4. 配置 UI 布局: framework/adapters/{args.game_name}/ui/layout.json")
    print(f"   5. 运行测试: python -m pytest games/{args.game_name}/tests/ -v")
    return 0


if __name__ == "__main__":
    sys.exit(main())
