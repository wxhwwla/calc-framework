# -*- coding: utf-8 -*-
"""演示：DAG + 数据 = 计算（无需 layout，无需 calcpack）。

运行方式：cd 到仓库根目录后执行
    python framework/examples/demo_compute.py
"""

import importlib.util
import sys
from pathlib import Path

# 确保仓库根目录在 sys.path
_REPO = Path(__file__).resolve().parent.parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from calc_framework.dag.serializer import load_dag
from calc_framework.dag.service import DAGService

# 加载终末地自定义函数（动态导入，避免修改 sys.path）
_functions_path = _REPO / "framework" / "adapters" / "endfield" / "functions.py"
_spec = importlib.util.spec_from_file_location("endfield_functions", _functions_path)
ef_funcs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ef_funcs)

# 1. 加载 DAG + 注册自定义函数
dag = load_dag("framework/adapters/endfield/dag/endfield_full.dag.json")
service = DAGService(dag)

for name in dir(ef_funcs):
    obj = getattr(ef_funcs, name)
    if callable(obj) and not name.startswith("_"):
        service.register_function(name, obj)

print(f"公式: {dag.name}")
print(f"变量数: {len(dag.variables)}")
print(f"节点数: {len(dag.nodes)}")
print(f"输出数: {len(dag.outputs)}")

# 打印变量名（调试用，写文件避免 PowerShell 编码问题）
with open(_REPO / "framework" / "examples" / "_debug_vars.txt", "w", encoding="utf-8") as f:
    for k in dag.variables:
        f.write(f"{k}\n")
print("变量名已写入 _debug_vars.txt")
print()

# 2. 构造输入数据（嵌套格式：按 source 分组）
#    _apply_defaults 会自动填充有 default 的变量，这里只需设置关键值
data = {
    "character": {
        "基础攻击": 500.0,
        "暴击伤害": 1.0,
        "暴击率": 0.05,
    },
    "weapon": {
        "基础攻击": 300.0,
        "攻击力+": 0.0,
        "附加攻击力+": 0.0,
    },
    "equipment": {
        "攻击力平值": 0.0,
    },
    "enemy": {
        "防御": 100.0,
    },
    "computed": {
        "技能倍率": 2.0,
        "暴击率": 0.5,
        "暴击伤害": 1.0,
        "主能力平值加算": 0.0,
        "副能力平值加算": 0.0,
        "主能力百分比": 0.0,
        "副能力百分比": 0.0,
        "伤害加成": 0.0,
        "伤害减免": 0.0,
        "增幅": 0.0,
        "虚弱": 0.0,
        "庇护": 0.0,
        "脆弱": 0.0,
        "易伤": 0.0,
        "失衡易伤": 0.0,
        "抗性": 0.0,
        "非主控减伤": 0.0,
        "连击增伤": 0.0,
        "特殊乘区": 1.0,
    },
    "user_input": {},
}

print("输入:")
print(f"  角色基础攻击 = {data['character']['基础攻击']}")
print(f"  武器基础攻击 = {data['weapon']['基础攻击']}")
print(f"  技能倍率 = {data['computed']['技能倍率']}")
print(f"  敌人防御 = {data['enemy']['防御']}")
print(f"  暴击率 = {data['computed']['暴击率']}")
print(f"  暴击伤害 = {data['computed']['暴击伤害']}")
print()

# 3. 求值
result = service.evaluate(data)
print("输出:")
for k, v in result.outputs.items():
    if isinstance(v, float):
        print(f"  {k} = {v:.2f}")
    else:
        print(f"  {k} = {v}")
