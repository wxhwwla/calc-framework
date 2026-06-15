/** 武器特殊能力选用加成（对齐 runtime_bonus.py）。 */

type SpecialSlot = [boolean, string, number[], number];

function readWeaponSpecialSlots(weapon: Record<string, unknown>): SpecialSlot[] {
  const specialRaw = weapon.special_skills;
  const slots: SpecialSlot[] = [];
  if (Array.isArray(specialRaw)) {
    for (let idx = 0; idx < 2; idx += 1) {
      if (idx >= specialRaw.length || typeof specialRaw[idx] !== "object") {
        slots.push([false, "", [], 1]);
        continue;
      }
      const item = specialRaw[idx] as Record<string, unknown>;
      const name = String(item.name ?? "").trim();
      const curveRaw = item.curve;
      const maxStack = Math.max(1, Number(item.max_stack ?? 1));
      if (!Array.isArray(curveRaw) || curveRaw.length === 0) {
        slots.push([false, "", [], 1]);
        continue;
      }
      slots.push([true, name, curveRaw.map(Number), maxStack]);
    }
    return slots;
  }
  return [
    [false, "", [], 1],
    [false, "", [], 1],
  ];
}

function specialNameMatches(pickName: string, slotName: string): boolean {
  return pickName === slotName || slotName.includes(pickName) || pickName.includes(slotName);
}

function specialPickBonus(curve: number[], maxStack: number, skillLevel: number, stackCount: number): number {
  if (skillLevel <= 0 || curve.length === 0) return 0;
  const effectiveStack = maxStack <= 1 ? 1 : Math.max(0, stackCount);
  if (effectiveStack <= 0) return 0;
  const idx = Math.max(0, Math.min(skillLevel - 1, curve.length - 1));
  return curve[idx] * effectiveStack;
}

function applyConditionalSpecial(
  weapon: Record<string, unknown>,
  kwargs: {
    ws_name: string;
    ws_level: number;
    ws_stack: number;
    ws2_name: string;
    ws2_level: number;
    ws2_stack: number;
    main_attr: string;
    sub_attr: string;
  },
): [number, number, number, number] {
  let mainFlat = 0;
  let subFlat = 0;
  let mainPct = 0;
  let subPct = 0;
  const slots = readWeaponSpecialSlots(weapon);
  const picks: [string, number, number][] = [
    [kwargs.ws_name, kwargs.ws_level, kwargs.ws_stack],
    [kwargs.ws2_name, kwargs.ws2_level, kwargs.ws2_stack],
  ];
  for (let slotIdx = 0; slotIdx < picks.length; slotIdx += 1) {
    const [pickName, pickLevel, pickStack] = picks[slotIdx];
    if (pickLevel <= 0 || !pickName) continue;
    const [enabled, saName, curve, maxStack] = slots[slotIdx];
    if (!enabled || !specialNameMatches(pickName, saName) || curve.length === 0) continue;
    const value = specialPickBonus(curve, maxStack, pickLevel, pickStack);
    if (saName === "主能力值+") mainFlat += value;
    else if (saName === "副能力值+") subFlat += value;
    else if (saName === `${kwargs.main_attr}+`) mainFlat += value;
    else if (saName === `${kwargs.sub_attr}+`) subFlat += value;
    else if (saName === "主能力+") mainPct += value;
    else if (saName === "副能力+") subPct += value;
    else if (saName === "全能力+") {
      mainPct += value;
      subPct += value;
    }
  }
  return [mainFlat, subFlat, mainPct, subPct];
}

export function addSpecialPicksToMainSubBonus(
  weapon: Record<string, unknown>,
  kwargs: {
    ws_name: string;
    ws_level: number;
    ws_stack: number;
    ws2_name: string;
    ws2_level: number;
    ws2_stack: number;
    main_attr: string;
    sub_attr: string;
  },
): [number, number] {
  const [mf, sf] = applyConditionalSpecial(weapon, kwargs);
  return [mf, sf];
}

export function addSpecialPicksToAbilityPct(
  weapon: Record<string, unknown>,
  kwargs: {
    ws_name: string;
    ws_level: number;
    ws_stack: number;
    ws2_name: string;
    ws2_level: number;
    ws2_stack: number;
    main_attr: string;
    sub_attr: string;
  },
): [number, number] {
  const [, , mp, sp] = applyConditionalSpecial(weapon, kwargs);
  return [mp, sp];
}

export function addSpecialPicksAttackPercent(
  weapon: Record<string, unknown>,
  kwargs: {
    ws_name: string;
    ws_level: number;
    ws_stack: number;
    ws2_name: string;
    ws2_level: number;
    ws2_stack: number;
    target_name: string;
  },
): number {
  const slots = readWeaponSpecialSlots(weapon);
  const picks: [string, number, number][] = [
    [kwargs.ws_name, kwargs.ws_level, kwargs.ws_stack],
    [kwargs.ws2_name, kwargs.ws2_level, kwargs.ws2_stack],
  ];
  let total = 0;
  for (let slotIdx = 0; slotIdx < picks.length; slotIdx += 1) {
    const [pickName, pickLevel, pickStack] = picks[slotIdx];
    if (pickLevel <= 0 || !pickName) continue;
    const [enabled, saName, curve, maxStack] = slots[slotIdx];
    if (!enabled || !specialNameMatches(pickName, saName) || saName !== kwargs.target_name) continue;
    total += specialPickBonus(curve, maxStack, pickLevel, pickStack);
  }
  return total;
}

export function resolveSkillLevel(effect: string, kwargs: Record<string, string | number>): number {
  if (effect === kwargs.normal_skill_1_name) return Number(kwargs.normal_skill_1_level);
  if (effect === kwargs.normal_skill_2_name) return Number(kwargs.normal_skill_2_level);
  if (effect === kwargs.normal_skill_3_name) return Number(kwargs.normal_skill_3_level);
  return 1;
}

export function shouldSkipSa3(effect: string, kwargs: Record<string, string | number>): boolean {
  return effect === kwargs.normal_skill_3_name && Boolean(kwargs.normal_skill_3_name) && Number(kwargs.normal_skill_3_level) === 0;
}
