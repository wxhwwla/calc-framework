# -*- coding: utf-8 -*-
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "tools")
from designer.data_editor.profiles import PROFILES

print("所有 profile 的标签页:")
for pid in PROFILES:
    prof = PROFILES[pid]
    print(f"\n{pid} ({prof.label}):")
    if prof.entity_tabs:
        for tab_name, filename, columns in prof.entity_tabs:
            print(f"  {tab_name}: {filename} -> {columns}")
    else:
        print("  (无标签页)")
