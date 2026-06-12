# Calc Framework — Domain Context

> This document defines unified terminology for Issues, tests, and documentation.
>
> [:cn: 中文版](CONTEXT_zh.md)

---

## English Glossary

| Term | Meaning |
|------|---------|
| **Character** | A record in `characters.json`: type, star rating, level curves, four primary stats (STR/AGI/INT/WIL), base ATK/HP/DEF, skill multipliers |
| **Weapon** | A record in `weapons.json`: base ATK curve, normal skills (affixes), special skills |
| **Equipment** | A record in `equipments.json`: chest/gloves/accessory slot |
| **Level Curve** | A numeric array matching level count (typically 90), pre-baked in JSON |
| **Talent / Potential** | Weapon refinement level sequence (0–5), not character talents |
| **Trust** | Trust level (0–4) with cumulative bonuses: 0→10→25→40→60 |
| **Multiplicative Zone** | One of 15 damage formula zones (ability bonus, defense, final ATK, etc.) |
| **DAG** | Directed Acyclic Graph — the formula computation graph |
| **Inverse / Fitting** | Given level data → solve for growth formula parameters (base, growth, divisor, offset) |
| **Full Search** | Enumerate all weapon×equipment combinations, keep Top-N by damage |
| **Loadout** | A specific weapon + 4 equipment pieces combination |
| **CalcPack** | A `.calcpack` ZIP bundle: DAG + layout.json + data → self-contained calculator |
| **ComputeSheet** | Declarative UI panel auto-rendered from `layout.json` + DAG variables |
| **GrowthParams** | Typed container for `(base, growth, divisor, offset, is_decimal, special_values)` |
| **GameInverseAdapter** | ABC for game-specific inverse engine — declare schemas, auto-fit |
| **JsonDataLoader[T]** | Generic lazy JSON loader with in-memory cache |
| **CalcWorker** | Generic QThread+QObject wrapper for background computation |
| **ThemeManager** | Multi-theme QSS manager (dark/light/high_contrast) |
| **DataContextLoader** | ABC for building the context dict that feeds DAG evaluation |

---

## Growth Formula

The core growth formula used by most attributes and skills:

```
value(lv) = base + floor((growth × (lv − 1) + offset) / divisor)
```

- **Base**: value at level 1
- **Growth**: increment coefficient
- **Divisor**: controls growth speed
- **Offset**: fine-tuning

For decimal data (e.g., percentages), values are scaled `×10 → integer floor → ÷10` to preserve precision.

---

## File Naming Conventions

| Pattern | Meaning |
|---------|---------|
| `_xxx.py` | Internal/private module |
| `xxx_zh.md` | Chinese documentation |
| `test_xxx.py` | Test file |
| `*.dag.json` | DAG formula definition |
| `layout.json` | UI layout declaration |
| `meta.json` | Adapter package metadata |
