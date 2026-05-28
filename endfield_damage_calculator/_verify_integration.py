"""ComputeSheet 集成验证脚本（临时，用完可删）"""
from pathlib import Path
from calc_framework.config.adapter import AdapterPackage
from calc_framework.ui.layout import load_layout_json
from calc_framework.ui.compute_sheet import ComputeSheet
from calculation.multiplicative_zones.dag.loader import EndfieldContextLoader
from data.loader import get_characters, get_weapons

layout_json = Path(r"e:\endfield_damage_calculator\framework\adapters\endfield\ui\layout.json")
layout = load_layout_json(layout_json.read_text(encoding="utf-8"))
print(f"Layout: {len(layout.sections)} sections")

chars = get_characters()
weapons = get_weapons()
char = chars[3]
weapon = weapons[3]
print(f"Character: {char['name']}, Weapon: {weapon['name']}")

loader = EndfieldContextLoader()
context = loader.build_context(
    character=char, weapon=weapon,
    char_level=60, weapon_level=60, trust_level=10,
)

adapter_dir = r"e:\endfield_damage_calculator\framework\adapters\endfield"
pkg = AdapterPackage(adapter_dir)
result = pkg.dag_service.evaluate(context)

for name in ["最终伤害", "最终攻击力","能力值加成","暴击区","伤害加成区","防御区","基础伤害区"]:
    val = result.outputs.get(name, "N/A")
    print(f"  {name}: {val}")

print("All outputs:")
for k, v in result.outputs.items():
    print(f"  {k}: {v}")
print("DAG evaluation OK")
