#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
公式反推 GUI（开发/维护用，不随 exe 打包）

用法（在 games/endfield 目录，且已 pip install -e .）：
    python scripts/inverse_formula_gui.py
"""

import re
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from calc_engine.endfield.calc.damage.formula import calculate_growth_curve, calculate_skill_curve
from calc_engine.endfield.calc.damage.inverse import (
    fit_attribute_formula,
    fit_skill_formula,
    fit_skill_formula_no_special,
    remove_duplicates,
    validate_attribute_formula,
    validate_skill_formula,
)


class InverseFormulaGUI:
    """反推公式维护工具 GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("公式反推工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        style = ttk.Style()
        style.configure("Title.TLabel", font=("微软雅黑", 14, "bold"))
        style.configure("Header.TLabel", font=("微软雅黑", 10, "bold"))

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="数值反推公式工具", style="Title.TLabel")
        title_label.pack(pady=10)

        type_frame = ttk.LabelFrame(main_frame, text="数据类型", padding="10")
        type_frame.pack(fill=tk.X, pady=5)

        self.data_type = tk.StringVar(value="attribute")

        ttk.Radiobutton(
            type_frame,
            text="属性数据（90级）",
            variable=self.data_type,
            value="attribute",
            command=self.update_hint,
        ).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(
            type_frame,
            text="技能倍率（9/12级）",
            variable=self.data_type,
            value="skill",
            command=self.update_hint,
        ).pack(side=tk.LEFT, padx=10)

        input_frame = ttk.LabelFrame(main_frame, text="数据输入", padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.hint_label = ttk.Label(input_frame, text=self.get_hint(), foreground="gray")
        self.hint_label.pack(anchor=tk.W, pady=2)

        self.input_text = scrolledtext.ScrolledText(input_frame, height=8, width=80)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=5)

        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="清除输入", command=self.clear_input).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="示例数据", command=self.load_sample_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="去重处理", command=self.handle_duplicates).pack(side=tk.LEFT, padx=5)

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)

        ttk.Button(action_frame, text="开始反推", command=self.calculate).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="验证公式", command=self.validate).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="生成曲线", command=self.generate_curve).pack(side=tk.LEFT, padx=5)

        result_frame = ttk.LabelFrame(main_frame, text="计算结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.result_text = scrolledtext.ScrolledText(result_frame, height=12, width=80, state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True)

    def get_hint(self):
        if self.data_type.get() == "attribute":
            return "提示：请输入90个属性数据（空格或换行分隔），支持整数和小数百分比格式（如 8.9%）"
        return "提示：请输入9或12个技能倍率数据（空格或换行分隔），支持整数和小数百分比格式"

    def update_hint(self):
        self.hint_label.config(text=self.get_hint())

    def clear_input(self):
        self.input_text.delete(1.0, tk.END)
        self.clear_result()

    def clear_result(self):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)

    def load_sample_data(self):
        self.clear_input()
        if self.data_type.get() == "attribute":
            sample = "34 38 41 45 48 52 55 59 62 65 69 72 76 79 83 86 90 93 96 100"
        else:
            sample = "100 102 104 106 108 110 112 114 116 150 160 170"
        self.input_text.insert(tk.END, sample)

    def handle_duplicates(self):
        try:
            data = self.parse_input()
            if len(data) == 94:
                data = remove_duplicates(data)
                self.clear_input()
                self.input_text.insert(tk.END, " ".join(map(str, data)))
                self.show_result("已去重处理：94个数据 → 90个数据")
            else:
                messagebox.showinfo("提示", f"当前数据长度为 {len(data)}，只有94个数据需要去重")
        except Exception as exc:
            messagebox.showerror("错误", str(exc))

    def parse_input(self):
        text = self.input_text.get(1.0, tk.END).strip()
        if not text:
            raise ValueError("请输入数据")

        tokens = re.split(r"[\s,，]+", text)
        tokens = [t.strip() for t in tokens if t.strip()]
        if not tokens:
            raise ValueError("未找到有效数据")

        data = []
        for token in tokens:
            if token.endswith("%"):
                data.append(float(token[:-1]))
            else:
                data.append(float(token))
        return data

    def calculate(self):
        try:
            self.clear_result()
            data = self.parse_input()

            result = f"输入数据长度: {len(data)}\n"
            result += f"数据类型: {'属性数据' if self.data_type.get() == 'attribute' else '技能倍率'}\n"
            result += "-" * 50 + "\n"

            if self.data_type.get() == "attribute":
                if len(data) == 94:
                    data = remove_duplicates(data)
                    result += "已自动去重: 94 → 90\n"
                if len(data) != 90:
                    raise ValueError(f"属性数据需要90个值，当前{len(data)}个")
                base, growth, divisor, offset = fit_attribute_formula(data)
                result += "计算结果:\n"
                result += f"  base = {base}\n  growth = {growth}\n  divisor = {divisor}\n  offset = {offset}\n"
                result += "\n公式: base + floor((growth * (lv - 1) + offset) / divisor)\n"
            else:
                if len(data) == 12:
                    base, growth, divisor, offset, special = fit_skill_formula(data)
                elif len(data) == 9:
                    base, growth, divisor, offset, special = fit_skill_formula_no_special(data)
                else:
                    raise ValueError(f"技能数据需要9或12个值，当前{len(data)}个")
                result += "计算结果:\n"
                result += f"  base = {base}\n  growth = {growth}\n  divisor = {divisor}\n  offset = {offset}\n"
                result += f"  special = {special}\n"

            self.show_result(result)
        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def validate(self):
        try:
            data = self.parse_input()
            result = ""
            if self.data_type.get() == "attribute":
                if len(data) == 94:
                    data = remove_duplicates(data)
                params = fit_attribute_formula(data)
                is_valid = validate_attribute_formula(*params, data)
                result += f"验证结果: {'✓ 公式正确' if is_valid else '✗ 公式不匹配'}\n"
                result += f"参数: base={params[0]}, growth={params[1]}, divisor={params[2]}, offset={params[3]}\n"
            else:
                if len(data) == 12:
                    params = fit_skill_formula(data)
                else:
                    params = fit_skill_formula_no_special(data)
                is_valid = validate_skill_formula(params[0], params[1], params[2], params[3], params[4], data)
                result += f"验证结果: {'✓ 公式正确' if is_valid else '✗ 公式不匹配'}\n"
                result += f"参数: base={params[0]}, growth={params[1]}, divisor={params[2]}, offset={params[3]}\n"
                result += f"特殊值: {params[4]}\n"
            self.show_result(result)
        except Exception as exc:
            messagebox.showerror("验证错误", str(exc))

    def generate_curve(self):
        try:
            data = self.parse_input()
            result = ""
            if self.data_type.get() == "attribute":
                if len(data) == 94:
                    data = remove_duplicates(data)
                base, growth, divisor, offset = fit_attribute_formula(data)
                curve = calculate_growth_curve(base, growth, divisor, offset)
                result += "生成属性成长曲线（90级）:\n"
                result += f"参数: base={base}, growth={growth}, divisor={divisor}, offset={offset}\n"
                result += "-" * 50 + "\n"
                for lv in (1, 20, 40, 60, 80, 90):
                    result += f"等级{lv}: {curve[lv - 1]}\n"
                result += "\n完整曲线（前10级）:\n"
                result += ", ".join(map(str, curve[:10])) + " ..."
            else:
                if len(data) == 12:
                    base, growth, divisor, offset, special = fit_skill_formula(data)
                else:
                    base, growth, divisor, offset, special = fit_skill_formula_no_special(data)
                curve = calculate_skill_curve(base, growth, divisor, offset, special)
                result += f"生成技能倍率曲线（{len(curve)}级）:\n"
                result += f"参数: base={base}, growth={growth}, divisor={divisor}, offset={offset}\n"
                result += f"特殊值: {special}\n"
                result += "-" * 50 + "\n"
                result += "完整曲线:\n"
                result += ", ".join(map(str, curve))
            self.show_result(result)
        except Exception as exc:
            messagebox.showerror("生成错误", str(exc))

    def show_result(self, text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    InverseFormulaGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
