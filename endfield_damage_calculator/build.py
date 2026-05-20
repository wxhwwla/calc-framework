#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终末地伤害计算器 - 打包脚本

使用PyInstaller将程序打包为Windows可执行文件
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到路径，确保能导入 please_read_me
sys.path.insert(0, str(Path(__file__).parent))

from please_read_me import get_version, get_exe_version  # 版本号


def check_pyinstaller() -> bool:
    """检查PyInstaller是否已安装"""
    try:
        import PyInstaller
        print(f"PyInstaller 已安装: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("PyInstaller 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True


def build_exe():
    """使用PyInstaller构建可执行文件"""
    project_root = Path(__file__).parent
    
    # 定义PyInstaller参数
    chars_json = str(project_root / 'character_weapon_equipment' / 'character_data' / 'characters.json')
    weapons_json = str(project_root / 'character_weapon_equipment' / 'weapon_data' / 'weapons.json')

    # 定义要排除的模块/文件
    excludes = [
        'tests',           # 测试文件
        'scripts',         # 脚本文件（如 inverse_cli.py）
        'build',           # 打包脚本模块
        'add_character',   # 数据添加脚本
        'add_weapon',      # 数据添加脚本
        'test_',           # 测试相关
    ]
    
    # 构建排除参数
    exclude_args = []
    for item in excludes:
        exclude_args.extend(['--exclude-module', item])
    
    args = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--name=终末地伤害计算器",
        "--add-data", f"{chars_json}{os.pathsep}character_weapon_equipment/character_data/",
        "--add-data", f"{weapons_json}{os.pathsep}character_weapon_equipment/weapon_data/",
        "--clean",
        *exclude_args,
        str(project_root / "main.py")
    ]
    
    print("=" * 60)
    print("开始打包...")
    print("=" * 60)
    
    # 执行打包命令
    try:
        subprocess.check_call(args, cwd=project_root)
        print("\n" + "=" * 60)
        print(f"打包完成！EXE v{get_exe_version()}")
        print(f"可执行文件位置: {project_root / 'dist' / '终末地伤害计算器.exe'}")
        print("=" * 60)
        
        # 将可执行文件移动到根目录
        exe_source = project_root / "dist" / "终末地伤害计算器.exe"
        exe_target = project_root / "终末地伤害计算器.exe"
        
        if exe_source.exists():
            import shutil
            shutil.copy2(exe_source, exe_target)
            print(f"\n已将可执行文件复制到: {exe_target}")
            
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        sys.exit(1)


def main():
    print("=" * 60)
    print(f"终末地伤害计算器 v{get_version()} - 打包工具")
    print("=" * 60)
    
    # 检查PyInstaller
    if not check_pyinstaller():
        sys.exit(1)
    
    # 执行打包
    build_exe()


if __name__ == "__main__":
    main()
