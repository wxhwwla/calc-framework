# -*- coding: utf-8 -*-
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "tools")
from designer.data_editor.profiles import ADAPTER_NAME_TO_PROFILE, PROFILES

print("所有 profile:")
for pid in PROFILES:
    prof = PROFILES[pid]
    print(f"  {pid}: {prof.label}")

print()
print("适配器名映射:")
print(f"  终末地伤害计算 -> {ADAPTER_NAME_TO_PROFILE.get('终末地伤害计算')}")
print(f"  untitled.dag -> {ADAPTER_NAME_TO_PROFILE.get('untitled.dag')}")
