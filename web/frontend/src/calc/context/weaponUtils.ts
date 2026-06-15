/** 武器/角色数值读取与曲线采样（对齐 Python multiplicative_zones 辅助函数）。 */

export const TRUST_ADD = [0, 10, 25, 40, 60];

export function getWeaponBonus(bonusData: unknown, level = 1): number {
  if (Array.isArray(bonusData)) {
    const idx = level - 1;
    if (idx >= 0 && idx < bonusData.length) {
      const v = bonusData[idx];
      if (typeof v === "number") return v;
    }
    return 0;
  }
  if (typeof bonusData === "number") return bonusData;
  return 0;
}

export function getCharAttrAtLevel(char: Record<string, unknown>, key: string, level: number): number {
  const values = char[key];
  if (!Array.isArray(values)) return 0;
  const idx = Math.min(level - 1, values.length - 1);
  if (idx < 0) return 0;
  return Number(values[idx]);
}

export function getWeaponRefinementBonus(
  weapon: Record<string, unknown> | null | undefined,
  refineLevel: number,
): { mainAbility: number; additionalAttack: number } {
  const out = { mainAbility: 0, additionalAttack: 0 };
  if (!weapon) return out;
  const skills = weapon.normal_skills;
  if (!Array.isArray(skills)) return out;
  const idx = Math.max(0, Math.min(refineLevel - 1, 8));
  for (const skill of skills) {
    if (!skill || typeof skill !== "object") continue;
    const effect = String((skill as Record<string, unknown>).effect ?? "");
    const curve = (skill as Record<string, unknown>).curve;
    const val = getWeaponBonus(curve, idx + 1);
    if (effect === "主能力值+") out.mainAbility = val;
    else if (effect === "附加攻击力+") out.additionalAttack = val;
  }
  return out;
}

export interface SkillKwargs {
  normal_skill_1_name: string;
  normal_skill_1_level: number;
  normal_skill_2_name: string;
  normal_skill_2_level: number;
  normal_skill_3_name: string;
  normal_skill_3_level: number;
  special_skill_1_name: string;
  special_skill_1_level: number;
  special_skill_1_stack: number;
  special_skill_2_name: string;
  special_skill_2_level: number;
  special_skill_2_stack: number;
}

export function emptySkillKwargs(): SkillKwargs {
  return {
    normal_skill_1_name: "",
    normal_skill_1_level: 0,
    normal_skill_2_name: "",
    normal_skill_2_level: 0,
    normal_skill_3_name: "",
    normal_skill_3_level: 0,
    special_skill_1_name: "",
    special_skill_1_level: 0,
    special_skill_1_stack: 0,
    special_skill_2_name: "",
    special_skill_2_level: 0,
    special_skill_2_stack: 0,
  };
}

function readWeaponSkillsSchema(weapon: Record<string, unknown>): {
  normal: { effect: string }[];
  special: { name: string }[];
} {
  const normal: { effect: string }[] = [];
  const ns = weapon.normal_skills;
  for (let i = 0; i < 3; i += 1) {
    if (Array.isArray(ns) && ns[i] && typeof ns[i] === "object") {
      normal.push({ effect: String((ns[i] as Record<string, unknown>).effect ?? "").trim() });
    } else {
      normal.push({ effect: "" });
    }
  }
  const special: { name: string }[] = [];
  const specialRaw = weapon.special_skills;
  for (let i = 0; i < 2; i += 1) {
    if (Array.isArray(specialRaw) && specialRaw[i] && typeof specialRaw[i] === "object") {
      special.push({ name: String((specialRaw[i] as Record<string, unknown>).name ?? "").trim() });
    } else {
      special.push({ name: "" });
    }
  }
  return { normal, special };
}

/** 从 Web payload 的 weapon_skill_values 构建乘区 kwargs（对齐 web_loadout_bridge）。 */
export function weaponSkillKwargsFromPayload(
  weapon: Record<string, unknown>,
  weaponSkillValues: Record<string, unknown> | undefined,
): SkillKwargs {
  const wsv = weaponSkillValues ?? {};
  const schema = readWeaponSkillsSchema(weapon);
  const kwargs = emptySkillKwargs();
  const normalLevels = [1, 2, 3].map((i) => Math.max(0, Number(wsv[`normal_skill_${i}_level`] ?? 0)));
  let normalIdx = 0;
  for (let i = 0; i < 3; i += 1) {
    const effect = schema.normal[i]?.effect ?? "";
    if (effect) {
      const level = normalLevels[normalIdx] ?? 0;
      normalIdx += 1;
      if (i === 0) {
        kwargs.normal_skill_1_name = effect;
        kwargs.normal_skill_1_level = level;
      } else if (i === 1) {
        kwargs.normal_skill_2_name = effect;
        kwargs.normal_skill_2_level = level;
      } else {
        kwargs.normal_skill_3_name = effect;
        kwargs.normal_skill_3_level = level;
      }
    }
  }
  const specialStates: { level: number; stack: number }[] = [];
  for (let i = 1; i <= 2; i += 1) {
    const level = Math.max(0, Number(wsv[`special_skill_${i}_level`] ?? 0));
    if (level > 0) {
      specialStates.push({
        level,
        stack: Math.max(0, Number(wsv[`special_skill_${i}_stack`] ?? 0)),
      });
    }
  }
  for (let i = 0; i < 2; i += 1) {
    const name = schema.special[i]?.name ?? "";
    if (name && specialStates[i]) {
      const st = specialStates[i];
      if (i === 0) {
        kwargs.special_skill_1_name = name;
        kwargs.special_skill_1_level = st.level;
        kwargs.special_skill_1_stack = st.stack;
      } else {
        kwargs.special_skill_2_name = name;
        kwargs.special_skill_2_level = st.level;
        kwargs.special_skill_2_stack = st.stack;
      }
    }
  }
  return kwargs;
}
