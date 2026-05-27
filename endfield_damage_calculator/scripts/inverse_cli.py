#!/usr/bin/env python3
"""
反向计算公式参数 CLI 工具

用于通过给定的等级数据，反向推导出属性成长公式和技能倍率公式的参数。

使用方式：
    python scripts/inverse_cli.py

支持的数据格式：
- 属性数据：90或94个数据（等级1-90，94个版本包含重复数据）
- 技能倍率：9或12个数据（等级1-9或1-12）
- 支持整数和小数百分比格式（如 "8.9%" 或 "89"）
"""

from calculation.damage.inverse import (
    fit_attribute_formula,
    fit_skill_formula,
    fit_skill_formula_no_special,
    remove_duplicates,
    validate_formula,
)


def parse_percent(value: str) -> tuple[float, bool]:
    """
    解析百分比字符串（支持整数和小数）

    数据处理规则：
    - 整数百分比：直接返回整数值
    - 小数百分比：乘10转换为整数

    参数：
        value: 百分比字符串，如 "8.9%" 或 "89"

    返回：
        (数值, 是否为小数)
    """
    value = value.strip()
    is_decimal = False
    is_percent = False

    # 移除%符号
    if value.endswith("%"):
        is_percent = True
        value = value[:-1]

    if "." in value:
        is_decimal = True
        val = float(value)
        # 小数百分比：乘10转换为整数
        if is_percent:
            val = val * 10
        return val, is_decimal
    else:
        return int(value), is_decimal


def parse_input(prompt: str) -> list[float | int]:
    """
    解析用户输入的数据列表

    参数：
        prompt: 提示信息

    返回：
        数据列表
    """
    print(f"\n{prompt}")
    print("请输入数据，使用空格或换行分隔：")

    data = []
    while True:
        line = input("> ").strip()
        if line.lower() == "done":
            break
        if line == "":
            continue

        parts = line.split()
        for part in parts:
            try:
                val, _is_decimal = parse_percent(part)
                data.append(val)
            except ValueError:
                print(f"警告：无法解析 '{part}'，已跳过")

    return data


def parse_input_with_tags() -> list[float | int]:
    """
    解析带标签的用户输入数据（用于技能倍率）

    返回：
        数据列表
    """
    print("\n请输入技能倍率数据（支持标签格式如 1-90: xxx）")
    print("或直接输入数字，使用空格或换行分隔：")
    print("输入 'done' 结束")

    data = []

    while True:
        line = input("> ").strip()
        if line.lower() == "done":
            break
        if line == "":
            continue

        # 检查是否包含标签（如 "1-90:"）
        if ":" in line:
            parts = line.split(":")
            tag = parts[0].strip()
            values = parts[1].strip()

            # 解析标签范围
            if "-" in tag:
                start_end = tag.split("-")
                if len(start_end) == 2:
                    try:
                        start = int(start_end[0].strip())
                        end = int(start_end[1].strip())
                        end - start + 1
                    except ValueError:
                        pass

            # 解析值
            for val_str in values.split():
                try:
                    val, _is_decimal = parse_percent(val_str)
                    data.append(val)
                except ValueError:
                    print(f"警告：无法解析 '{val_str}'，已跳过")
        else:
            # 直接解析数字
            for part in line.split():
                try:
                    val, _is_decimal = parse_percent(part)
                    data.append(val)
                except ValueError:
                    print(f"警告：无法解析 '{part}'，已跳过")

    # 根据数据长度判断类型
    if len(data) == 94:
        print("\n检测到94个数据点（包含重复），将自动去除重复...")
        data = remove_duplicates(data)
        print("去除重复后：90个数据点")
    elif len(data) == 90:
        print("\n检测到90个数据点（属性成长数据）")
    elif len(data) == 12:
        print("\n检测到12个数据点（技能倍率数据，含10-12级特殊值）")
    elif len(data) == 9:
        print("\n检测到9个数据点（技能倍率数据，1-8级用公式，9级为特殊值）")
    else:
        print(f"\n警告：数据点数量为 {len(data)}，可能无法正确拟合")

    return data


def main():
    """
    主函数：交互式公式参数计算器
    """
    print("=" * 60)
    print("          公式参数计算器 v1.0")
    print("=" * 60)
    print("用途：通过等级数据反向推导属性成长/技能倍率公式参数")
    print("支持：90/94个属性数据 或 9/12个技能倍率数据")
    print("=" * 60)

    while True:
        print("\n请选择数据类型：")
        print("1. 属性成长数据（90级）")
        print("2. 技能倍率数据（12级，含特殊值）")
        print("3. 技能倍率数据（9级，第9级为特殊值）")
        print("4. 退出")

        choice = input("\n请输入选择 (1-4): ").strip()

        if choice == "4":
            print("退出程序...")
            break

        if choice not in ["1", "2", "3"]:
            print("无效选择，请输入1-4")
            continue

        # 获取数据
        data = parse_input_with_tags()

        if len(data) == 0:
            print("错误：未输入任何数据")
            continue

        # 根据选择进行拟合
        try:
            if choice == "1":
                # 属性成长数据
                if len(data) == 94:
                    data = remove_duplicates(data)

                if len(data) != 90:
                    print(f"错误：属性数据需要90个点，实际{len(data)}个")
                    continue

                print("\n正在拟合属性成长公式...")
                base, growth, divisor, offset = fit_attribute_formula(data)

                print("\n拟合结果：")
                print(f"  base = {base}")
                print(f"  growth = {growth}")
                print(f"  divisor = {divisor}")
                print(f"  offset = {offset}")
                print(f"\n公式：属性值 = {base} + floor(({growth} × (等级-1) + {offset}) / {divisor})")

                # 验证
                is_valid = validate_formula(base, growth, divisor, offset, data)
                print(f"\n验证结果：{'✓ 完全匹配' if is_valid else '✗ 存在误差'}")

            elif choice == "2":
                # 技能倍率（12级）
                if len(data) != 12:
                    print(f"错误：技能数据需要12个点，实际{len(data)}个")
                    continue

                print("\n正在拟合技能倍率公式（含特殊值）...")
                base, growth, divisor, offset, special = fit_skill_formula(data)

                print("\n拟合结果：")
                print(f"  base = {base}")
                print(f"  growth = {growth}")
                print(f"  divisor = {divisor}")
                print(f"  offset = {offset}")
                print(f"  特殊值(10-12级) = {special}")
                print(f"\n公式：技能倍率 = {base} + floor(({growth} × (等级-1) + {offset}) / {divisor})")
                print("      10-12级使用特殊值")

                # 验证
                is_valid = validate_formula(base, growth, divisor, offset, data, special)
                print(f"\n验证结果：{'✓ 完全匹配' if is_valid else '✗ 存在误差'}")

            elif choice == "3":
                # 技能倍率（9级）
                if len(data) != 9:
                    print(f"错误：技能数据需要9个点，实际{len(data)}个")
                    continue

                print("\n正在拟合技能倍率公式（第9级为特殊值）...")
                base, growth, divisor, offset, special = fit_skill_formula_no_special(data)

                print("\n拟合结果：")
                print(f"  base = {base}")
                print(f"  growth = {growth}")
                print(f"  divisor = {divisor}")
                print(f"  offset = {offset}")
                print(f"  特殊值(9级) = {special}")
                print(f"\n公式：技能倍率 = {base} + floor(({growth} × (等级-1) + {offset}) / {divisor})")
                print(f"      9级使用特殊值 {special[0]}")

                # 验证
                is_valid = validate_formula(base, growth, divisor, offset, data, special)
                print(f"\n验证结果：{'✓ 完全匹配' if is_valid else '✗ 存在误差'}")

        except Exception as e:
            print(f"\n错误：{e}")
            import traceback

            traceback.print_exc()

        # 询问是否继续
        again = input("\n继续计算？(y/n): ").strip().lower()
        if again != "y":
            print("退出程序...")
            break


if __name__ == "__main__":
    main()
