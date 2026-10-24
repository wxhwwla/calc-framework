# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

raw = Path(".tmp-npm-audit.json").read_text(encoding="utf-8-sig")
start = raw.find("{")
d = json.loads(raw[start:])
vulns = d.get("vulnerabilities") or {}
print("count", len(vulns))
for name, meta in sorted(vulns.items()):
    via = meta.get("via") or []
    titles: list[str] = []
    ranges: list[str] = []
    for v in via:
        if isinstance(v, dict):
            titles.append(str(v.get("title") or "")[:80])
            ranges.append(str(v.get("range") or ""))
        else:
            titles.append(str(v))
    print(f"{meta.get('severity'):8} {name:28} fixAvailable={meta.get('fixAvailable')} ranges={ranges[:2]}")
    for t in titles[:3]:
        print("   ", t)
