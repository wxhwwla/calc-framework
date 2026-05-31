# SPDX-License-Identifier: AGPL-3.0
"""NSIS 安装包构建器。



用法::



    python build_installer.py                          # 从 dist/ 构建安装包

    python build_installer.py --dist-dir path/to/dist   # 指定构建产物目录

    python build_installer.py --version 1.0.0           # 覆盖版本号

    python build_installer.py --dry-run                 # 仅打印命令，不执行

    python build_installer.py --check                   # 仅检查依赖，不执行构建

"""



from __future__ import annotations



import argparse

import shutil

import subprocess

import sys

from pathlib import Path



_INSTALLER_DIR = Path(__file__).resolve().parent

_PROJECT_ROOT = _INSTALLER_DIR.parent

_NSI_SCRIPT = _INSTALLER_DIR / "endfield_calculator_setup.nsi"





def _get_version() -> str:

    sys.path.insert(0, str(_PROJECT_ROOT))

    try:

        from please_read_me import _EXE_VERSION

        return _EXE_VERSION

    except ImportError:

        return "0.0.0"





def _ensure_nsis() -> str | None:

    """检查 NSIS 编译器是否可用。"""

    makensis = shutil.which("makensis")

    if makensis:

        return makensis

    alt_paths = [

        r"C:\Program Files (x86)\NSIS\makensis.exe",

        r"C:\Program Files\NSIS\makensis.exe",

    ]

    for p in alt_paths:

        if Path(p).is_file():

            return p

    return None





def _validate_dist(dist_dir: Path) -> list[str]:

    """验证构建产物目录是否完整。"""

    issues: list[str] = []

    expected_apps = [

        ("终末地伤害计算器", "终末地伤害计算器.exe"),

        ("数据设计器", "数据设计器.exe"),

        ("配置包设计器", "配置包设计器.exe"),

    ]

    for app_name, exe_name in expected_apps:

        app_dir = dist_dir / app_name

        exe_path = app_dir / exe_name

        if not exe_path.exists():

            issues.append(f"缺少 {exe_name}（预期位置: {exe_path})")

        elif not app_dir.is_dir():

            issues.append(f"目录不存在: {app_dir}")

    return issues





def build_installer(

    dist_dir: Path,

    version: str,

    *,

    dry_run: bool = False,

) -> int:

    """执行安装包构建。



    Returns:

        成功返回 0，失败返回 1。

    """

    makensis = _ensure_nsis()

    if not makensis:

        print("错误: 未找到 NSIS 编译器 (makensis)。", file=sys.stderr)

        print("请安装 NSIS: https://nsis.sourceforge.io/Download", file=sys.stderr)

        print("或确保 makensis.exe 在 PATH 中。", file=sys.stderr)

        return 1



    if not _NSI_SCRIPT.is_file():

        print(f"错误: NSIS 脚本不存在: {_NSI_SCRIPT}", file=sys.stderr)

        return 1



    issues = _validate_dist(dist_dir)

    if issues:

        print("警告: 构建产物不完整:", file=sys.stderr)

        for issue in issues:

            print(f"  - {issue}", file=sys.stderr)

        print("安装包可能缺少部分组件。\n", file=sys.stderr)



    cmd = [

        makensis,

        f"/DVERSION={version}",

        f"/DAPP_ROOT={dist_dir}",

        str(_NSI_SCRIPT),

    ]



    print(f"NSIS: {makensis}")

    print(f"版本: {version}")

    print(f"产物: {dist_dir}")

    print(f"脚本: {_NSI_SCRIPT}")

    print(f"输出: {dist_dir / f'GameCalcPlatform_Setup_v{version}.exe'}")

    print(f"命令: {' '.join(cmd)}\n")



    if dry_run:

        print("[dry-run] 未执行构建。")

        return 0



    result = subprocess.run(cmd, cwd=str(_INSTALLER_DIR))

    if result.returncode != 0:

        print(f"错误: NSIS 构建失败 (exit={result.returncode})", file=sys.stderr)

        return 1



    output_path = dist_dir / f"GameCalcPlatform_Setup_v{version}.exe"

    if output_path.exists():

        size_mb = output_path.stat().st_size / 1024 / 1024

        print(f"\n安装包已生成: {output_path} ({size_mb:.1f} MB)")

    else:

        print(f"\n警告: 未找到输出文件 {output_path}", file=sys.stderr)



    return 0





def check_environment() -> int:

    """检查构建环境是否就绪。"""

    makensis = _ensure_nsis()

    if makensis:

        print(f"[OK] NSIS: {makensis}")

    else:

        print("[FAIL] NSIS: 未找到 (makensis)")

        print("       请从 https://nsis.sourceforge.io/Download 安装")



    if _NSI_SCRIPT.is_file():

        print(f"[OK] 脚本: {_NSI_SCRIPT}")

    else:

        print(f"[FAIL] 脚本: {_NSI_SCRIPT} 不存在")



    _add_path()

    try:

        from scripts.please_read_me import _EXE_VERSION, _VERSION

        print(f"[OK] 版本: exe={_EXE_VERSION}, src={_VERSION}")

    except ImportError:

        print("[FAIL] 版本: 无法读取 please_read_me.py")



    return 0 if makensis and _NSI_SCRIPT.is_file() else 1





def _add_path() -> None:

    if str(_PROJECT_ROOT) not in sys.path:

        sys.path.insert(0, str(_PROJECT_ROOT))





def main() -> int:

    parser = argparse.ArgumentParser(description="NSIS 安装包构建器")

    parser.add_argument(

        "--dist-dir",

        type=Path,

        default=_PROJECT_ROOT / "dist",

        help="构建产物目录（默认: dist/）",

    )

    parser.add_argument(

        "--version",

        type=str,

        default=None,

        help="版本号（默认: please_read_me._EXE_VERSION）",

    )

    parser.add_argument(

        "--dry-run",

        action="store_true",

        help="仅打印构建命令，不执行",

    )

    parser.add_argument(

        "--check",

        action="store_true",

        help="仅检查构建环境，不执行构建",

    )



    args = parser.parse_args()



    if args.check:

        return check_environment()



    version = args.version or _get_version()

    return build_installer(

        dist_dir=args.dist_dir.resolve(),

        version=version,

        dry_run=args.dry_run,

    )





if __name__ == "__main__":

    sys.exit(main())

