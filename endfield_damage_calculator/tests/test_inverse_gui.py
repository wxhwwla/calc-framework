#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用反推公式 GUI

此GUI仅用于内部测试，不用于打包发布。
功能：通过输入数据反推成长公式参数
"""

import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path

# 添加路径以便导入 calculation 模块
# 使用脚本所在目录的父目录（项目根目录）
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from calculation.inverse import (
    fit_attribute_formula,
    fit_skill_formula,
    fit_skill_formula_no_special,
    fit_formula,
    validate_attribute_formula,
    validate_skill_formula,
    remove_duplicates
)

from calculation.formula import (
    calculate_growth_curve,
    calculate_skill_curve
)


class InverseFormulaGUI:
    """反推公式测试 GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("公式反推测试工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置样式
        style = ttk.Style()
        style.configure('Title.TLabel', font=('微软雅黑', 14, 'bold'))
        style.configure('Header.TLabel', font=('微软雅黑', 10, 'bold'))
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="数值反推公式工具", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # 数据类型选择
        type_frame = ttk.LabelFrame(main_frame, text="数据类型", padding="10")
        type_frame.pack(fill=tk.X, pady=5)
        
        self.data_type = tk.StringVar(value="attribute")
        
        ttk.Radiobutton(type_frame, text="属性数据（90级）", variable=self.data_type, 
                       value="attribute", command=self.update_hint).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="技能倍率（9/12级）", variable=self.data_type, 
                       value="skill", command=self.update_hint).pack(side=tk.LEFT, padx=10)
        
        # 输入区域
        input_frame = ttk.LabelFrame(main_frame, text="数据输入", padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 提示标签
        self.hint_label = ttk.Label(input_frame, text=self.get_hint(), foreground='gray')
        self.hint_label.pack(anchor=tk.W, pady=2)
        
        # 输入文本框
        self.input_text = scrolledtext.ScrolledText(input_frame, height=8, width=80)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 快捷操作按钮
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="清除输入", command=self.clear_input).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="示例数据", command=self.load_sample_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="去重处理", command=self.handle_duplicates).pack(side=tk.LEFT, padx=5)
        
        # 操作按钮
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="开始反推", command=self.calculate, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="验证公式", command=self.validate).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="生成曲线", command=self.generate_curve).pack(side=tk.LEFT, padx=5)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="计算结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=12, width=80, state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    def get_hint(self):
        """获取输入提示"""
        if self.data_type.get() == "attribute":
            return "提示：请输入90个属性数据（空格或换行分隔），支持整数和小数百分比格式（如 8.9%）"
        else:
            return "提示：请输入9或12个技能倍率数据（空格或换行分隔），支持整数和小数百分比格式"
    
    def update_hint(self):
        """更新输入提示"""
        self.hint_label.config(text=self.get_hint())
    
    def clear_input(self):
        """清除输入"""
        self.input_text.delete(1.0, tk.END)
        self.clear_result()
    
    def clear_result(self):
        """清除结果"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
    
    def load_sample_data(self):
        """加载示例数据"""
        self.clear_input()
        if self.data_type.get() == "attribute":
            # 荧光雷羽攻击力示例（前20个）
            sample = "34 38 41 45 48 52 55 59 62 65 69 72 76 79 83 86 90 93 96 100"
        else:
            # 技能倍率示例（12级）
            sample = "100 102 104 106 108 110 112 114 116 150 160 170"
        self.input_text.insert(tk.END, sample)
    
    def handle_duplicates(self):
        """处理重复数据（94→90）"""
        try:
            data = self.parse_input()
            if len(data) == 94:
                data = remove_duplicates(data)
                self.clear_input()
                self.input_text.insert(tk.END, ' '.join(map(str, data)))
                self.show_result(f"已去重处理：94个数据 → 90个数据")
            else:
                messagebox.showinfo("提示", f"当前数据长度为 {len(data)}，只有94个数据需要去重")
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def parse_input(self):
        """解析输入数据"""
        text = self.input_text.get(1.0, tk.END).strip()
        if not text:
            raise ValueError("请输入数据")
        
        # 支持空格、换行、逗号分隔
        import re
        tokens = re.split(r'[\s,，]+', text)
        tokens = [t.strip() for t in tokens if t.strip()]
        
        if not tokens:
            raise ValueError("未找到有效数据")
        
        # 解析百分比格式
        data = []
        for token in tokens:
            token = token.strip()
            if token.endswith('%'):
                # 百分比格式
                try:
                    value = float(token[:-1])
                    data.append(value)
                except ValueError:
                    raise ValueError(f"无效的百分比值: {token}")
            else:
                # 普通数值
                try:
                    data.append(float(token))
                except ValueError:
                    raise ValueError(f"无效的数值: {token}")
        
        return data
    
    def calculate(self):
        """执行反推计算"""
        try:
            self.clear_result()
            data = self.parse_input()
            
            result = ""
            result += f"输入数据长度: {len(data)}\n"
            result += f"数据类型: {'属性数据' if self.data_type.get() == 'attribute' else '技能倍率'}\n"
            result += "-" * 50 + "\n"
            
            # 根据数据类型选择反推方法
            if self.data_type.get() == "attribute":
                if len(data) == 94:
                    data = remove_duplicates(data)
                    result += f"已自动去重: 94 → 90\n"
                
                if len(data) != 90:
                    raise ValueError(f"属性数据需要90个值，当前{len(data)}个")
                
                base, growth, divisor, offset = fit_attribute_formula(data)
                result += f"计算结果:\n"
                result += f"  base = {base}\n"
                result += f"  growth = {growth}\n"
                result += f"  divisor = {divisor}\n"
                result += f"  offset = {offset}\n"
                result += "\n公式: base + floor((growth * (lv - 1) + offset) / divisor)\n"
                
            else:
                if len(data) == 12:
                    base, growth, divisor, offset, special = fit_skill_formula(data)
                    result += f"计算结果:\n"
                    result += f"  base = {base}\n"
                    result += f"  growth = {growth}\n"
                    result += f"  divisor = {divisor}\n"
                    result += f"  offset = {offset}\n"
                    result += f"  special = {special}\n"
                elif len(data) == 9:
                    base, growth, divisor, offset, special = fit_skill_formula_no_special(data)
                    result += f"计算结果:\n"
                    result += f"  base = {base}\n"
                    result += f"  growth = {growth}\n"
                    result += f"  divisor = {divisor}\n"
                    result += f"  offset = {offset}\n"
                    result += f"  special = {special}\n"
                else:
                    raise ValueError(f"技能数据需要9或12个值，当前{len(data)}个")
            
            self.show_result(result)
            
        except Exception as e:
            messagebox.showerror("计算错误", str(e))
    
    def validate(self):
        """验证公式"""
        try:
            data = self.parse_input()
            
            result = ""
            if self.data_type.get() == "attribute":
                if len(data) == 94:
                    data = remove_duplicates(data)
                
                params = fit_attribute_formula(data)
                # validate_attribute_formula 参数顺序: base, growth, divisor, offset, data
                is_valid = validate_attribute_formula(*params, data)
                result += f"验证结果: {'✓ 公式正确' if is_valid else '✗ 公式不匹配'}\n"
                result += f"参数: base={params[0]}, growth={params[1]}, divisor={params[2]}, offset={params[3]}\n"
                
            else:
                if len(data) == 12:
                    params = fit_skill_formula(data)
                    # validate_skill_formula 参数顺序: base, growth, divisor, offset, special_values, data
                    is_valid = validate_skill_formula(params[0], params[1], params[2], params[3], params[4], data)
                else:
                    params = fit_skill_formula_no_special(data)
                    is_valid = validate_skill_formula(params[0], params[1], params[2], params[3], params[4], data)
                
                result += f"验证结果: {'✓ 公式正确' if is_valid else '✗ 公式不匹配'}\n"
                result += f"参数: base={params[0]}, growth={params[1]}, divisor={params[2]}, offset={params[3]}\n"
                result += f"特殊值: {params[4]}\n"
            
            self.show_result(result)
            
        except Exception as e:
            messagebox.showerror("验证错误", str(e))
    
    def generate_curve(self):
        """生成成长曲线"""
        try:
            data = self.parse_input()
            
            result = ""
            if self.data_type.get() == "attribute":
                if len(data) == 94:
                    data = remove_duplicates(data)
                
                base, growth, divisor, offset = fit_attribute_formula(data)
                curve = calculate_growth_curve(base, growth, divisor, offset)
                
                result += f"生成属性成长曲线（90级）:\n"
                result += f"参数: base={base}, growth={growth}, divisor={divisor}, offset={offset}\n"
                result += "-" * 50 + "\n"
                
                # 显示关键等级
                key_levels = [1, 20, 40, 60, 80, 90]
                for lv in key_levels:
                    idx = lv - 1
                    result += f"等级{lv}: {curve[idx]}\n"
                
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
            
        except Exception as e:
            messagebox.showerror("生成错误", str(e))
    
    def show_result(self, text):
        """显示结果"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)


def main():
    """主函数"""
    root = tk.Tk()
    app = InverseFormulaGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
