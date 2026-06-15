/**
 * 属性/能力/攻击力预处理（对齐 Python multiplicative_zones *_with_details）。
 */

import {
  addSpecialPicksAttackPercent,
  addSpecialPicksToAbilityPct,
  addSpecialPicksToMainSubBonus,
  resolveSkillLevel,
  shouldSkipSa3,
} from "./specialSkills";
import { getWeaponBonus, TRUST_ADD, type SkillKwargs } from "./weaponUtils";

const ATTRIBUTES = ["力量", "敏捷", "智识", "意志"] as const;

export interface AttrZoneDetail {
  base: number;
  bonus: number;
  pct_bonus: number;
  total: number;
}

function classifyEffect(
  effect: string,
  attr: string,
  isMain: boolean,
  isSub: boolean,
  _mainAttr: string,
  _subAttr: string,
): string {
  if (effect === "主能力值+") return "main_flat";
  if (effect === "副能力值+") return "sub_flat";
  if (effect === `${attr}+`) return "attr_flat";
  if (isMain && effect === "主能力+") return "main_pct";
  if (isSub && effect === "副能力+") return "sub_pct";
  if ((isMain || isSub) && effect === "全能力+") return "both_pct";
  return "";
}

function computeAttrWeaponBonus(
  attr: string,
  isMain: boolean,
  isSub: boolean,
  weapon: Record<string, unknown> | null,
  kwargs: SkillKwargs,
  mainAttr: string,
  subAttr: string,
  trustLevel: number,
): [number, number] {
  let flatBonus = 0;
  let pctBonus = 0;
  if (!weapon) return [0, 0];

  const kw = kwargs as unknown as Record<string, string | number>;
  const classifyAndAdd = (effect: string, value: number) => {
    const category = classifyEffect(effect, attr, isMain, isSub, mainAttr, subAttr);
    if (
      (category === "main_flat" && isMain) ||
      (category === "sub_flat" && isSub) ||
      category === "attr_flat"
    ) {
      flatBonus += value;
    } else if (category === "main_pct" || category === "sub_pct" || category === "both_pct") {
      pctBonus += value;
    }
  };

  for (const skill of (weapon.normal_skills as unknown[]) ?? []) {
    if (!skill || typeof skill !== "object") continue;
    const effect = String((skill as Record<string, unknown>).effect ?? "");
    if (shouldSkipSa3(effect, kw)) continue;
    const value = getWeaponBonus((skill as Record<string, unknown>).curve, resolveSkillLevel(effect, kw));
    classifyAndAdd(effect, value);
  }

  for (const key of Object.keys(weapon)) {
    if (!key.endsWith("+")) continue;
    if (shouldSkipSa3(key, kw)) continue;
    const value = getWeaponBonus(weapon[key], resolveSkillLevel(key, kw));
    classifyAndAdd(key, value);
  }

  const specialKw = {
    ws_name: kwargs.special_skill_1_name,
    ws_level: kwargs.special_skill_1_level,
    ws_stack: kwargs.special_skill_1_stack,
    ws2_name: kwargs.special_skill_2_name,
    ws2_level: kwargs.special_skill_2_level,
    ws2_stack: kwargs.special_skill_2_stack,
    main_attr: mainAttr,
    sub_attr: subAttr,
  };
  const [md, sd] = addSpecialPicksToMainSubBonus(weapon, specialKw);
  const [mp, sp] = addSpecialPicksToAbilityPct(weapon, specialKw);
  if (isMain) {
    flatBonus += md;
    pctBonus += mp;
  } else if (isSub) {
    flatBonus += sd;
    pctBonus += sp;
  }
  if (isMain && trustLevel > 0 && trustLevel < TRUST_ADD.length) {
    flatBonus += TRUST_ADD[trustLevel];
  }
  return [flatBonus, pctBonus];
}

export function calculateAttributeZonesWithDetails(
  character: Record<string, unknown> | null,
  weapon: Record<string, unknown> | null,
  level: number,
  kwargs: SkillKwargs,
  trustLevel: number,
): Record<string, AttrZoneDetail> {
  const mainAttr = String(character?.主能力 ?? "");
  const subAttr = String(character?.副能力 ?? "");
  const levelIndex = level - 1;
  const result: Record<string, AttrZoneDetail> = {};

  for (const attr of ATTRIBUTES) {
    let baseValue = 0;
    const attrList = character?.[attr];
    if (Array.isArray(attrList) && levelIndex >= 0 && levelIndex < attrList.length) {
      baseValue = Number(attrList[levelIndex]);
    }
    const isMain = attr === mainAttr;
    const isSub = attr === subAttr;
    const [flatBonus, pctBonus] = computeAttrWeaponBonus(
      attr,
      isMain,
      isSub,
      weapon,
      kwargs,
      mainAttr,
      subAttr,
      trustLevel,
    );
    const total =
      isMain || isSub
        ? (baseValue + flatBonus) * (1 + pctBonus / 100)
        : baseValue + flatBonus;
    result[attr] = { base: baseValue, bonus: flatBonus, pct_bonus: pctBonus, total };
  }
  return result;
}

export interface AbilityBonusDetail {
  main_attr: string;
  main_value: number;
  main_flat: number;
  main_pct: number;
  main_base: number;
  main_bonus: number;
  sub_attr: string;
  sub_value: number;
  sub_flat: number;
  sub_pct: number;
  sub_base: number;
  sub_bonus: number;
  bonus: number;
}

export function calculateAbilityBonusWithDetails(
  character: Record<string, unknown> | null,
  weapon: Record<string, unknown> | null,
  level: number,
  kwargs: SkillKwargs,
  trustLevel: number,
): AbilityBonusDetail {
  const empty: AbilityBonusDetail = {
    main_attr: "",
    main_value: 0,
    main_flat: 0,
    main_pct: 0,
    main_base: 0,
    main_bonus: 0,
    sub_attr: "",
    sub_value: 0,
    sub_flat: 0,
    sub_pct: 0,
    sub_base: 0,
    sub_bonus: 0,
    bonus: 0,
  };
  if (!character) return empty;

  const mainAttr = String(character.主能力 ?? "");
  const subAttr = String(character.副能力 ?? "");
  const levelIndex = level - 1;
  let mainBase = 0;
  let subBase = 0;
  let mainBonus = 0;
  let subBonus = 0;
  let mainPct = 0;
  let subPct = 0;

  const mainList = character[mainAttr];
  if (mainAttr && Array.isArray(mainList) && levelIndex >= 0 && levelIndex < mainList.length) {
    mainBase = Number(mainList[levelIndex]);
  }
  const subList = character[subAttr];
  if (subAttr && Array.isArray(subList) && levelIndex >= 0 && levelIndex < subList.length) {
    subBase = Number(subList[levelIndex]);
  }

  if (weapon) {
    const kw = kwargs as unknown as Record<string, string | number>;
    const classify = (attrName: string): string => {
      if (attrName === "主能力值+") return "main_flat";
      if (attrName === "副能力值+") return "sub_flat";
      if (attrName === `${mainAttr}+`) return "main_flat";
      if (attrName === `${subAttr}+`) return "sub_flat";
      if (attrName === "主能力+") return "main_pct";
      if (attrName === "副能力+") return "sub_pct";
      if (attrName === "全能力+") return "both_pct";
      return "";
    };

    const applyBonus = (category: string, value: number) => {
      if (category === "main_flat") mainBonus += value;
      else if (category === "sub_flat") subBonus += value;
      else if (category === "main_pct") mainPct += value;
      else if (category === "sub_pct") subPct += value;
      else if (category === "both_pct") {
        mainPct += value;
        subPct += value;
      }
    };

    for (const skill of (weapon.normal_skills as unknown[]) ?? []) {
      if (!skill || typeof skill !== "object") continue;
      const effect = String((skill as Record<string, unknown>).effect ?? "");
      const category = classify(effect);
      if (!category || shouldSkipSa3(effect, kw)) continue;
      applyBonus(category, getWeaponBonus((skill as Record<string, unknown>).curve, resolveSkillLevel(effect, kw)));
    }

    for (const key of Object.keys(weapon)) {
      if (!key.endsWith("+")) continue;
      const category = classify(key);
      if (!category || shouldSkipSa3(key, kw)) continue;
      applyBonus(category, getWeaponBonus(weapon[key], resolveSkillLevel(key, kw)));
    }

    const specialKw = {
      ws_name: kwargs.special_skill_1_name,
      ws_level: kwargs.special_skill_1_level,
      ws_stack: kwargs.special_skill_1_stack,
      ws2_name: kwargs.special_skill_2_name,
      ws2_level: kwargs.special_skill_2_level,
      ws2_stack: kwargs.special_skill_2_stack,
      main_attr: mainAttr,
      sub_attr: subAttr,
    };
    const [md, sd] = addSpecialPicksToMainSubBonus(weapon, specialKw);
    const [mp, sp] = addSpecialPicksToAbilityPct(weapon, specialKw);
    mainBonus += md;
    subBonus += sd;
    mainPct += mp;
    subPct += sp;
  }

  const trustBonus = trustLevel >= 0 && trustLevel < TRUST_ADD.length ? TRUST_ADD[trustLevel] : 0;
  const mainFlat = mainBase + mainBonus + trustBonus;
  const subFlat = subBase + subBonus;
  const mainValue = mainFlat * (1 + mainPct / 100);
  const subValue = subFlat * (1 + subPct / 100);
  const bonus = Math.trunc(mainValue) * 0.005 + Math.trunc(subValue) * 0.002;

  return {
    main_attr: mainAttr,
    main_value: mainValue,
    main_flat: mainFlat,
    main_pct: mainPct,
    main_base: mainBase,
    main_bonus: mainBonus,
    sub_attr: subAttr,
    sub_value: subValue,
    sub_flat: subFlat,
    sub_pct: subPct,
    sub_base: subBase,
    sub_bonus: subBonus,
    bonus,
  };
}

export interface FinalAttackDetail {
  base_attack: number;
  char_base_attack: number;
  weapon_base_attack: number;
  attack_bonus_multiplier: number;
  attack_bonus_attack: number;
  additional_attack: number;
  intermediate_attack: number;
  ability_bonus: number;
  final_attack: number;
}

export function calculateFinalAttackWithDetails(
  character: Record<string, unknown> | null,
  weapon: Record<string, unknown> | null,
  charLevel: number,
  weaponLevel: number,
  kwargs: SkillKwargs,
  trustLevel: number,
  equipmentStatBonus: Record<string, number> = {},
  equipmentAttackPercent = 0,
): FinalAttackDetail {
  const zero: FinalAttackDetail = {
    base_attack: 0,
    char_base_attack: 0,
    weapon_base_attack: 0,
    attack_bonus_multiplier: 1,
    attack_bonus_attack: 0,
    additional_attack: 0,
    intermediate_attack: 0,
    ability_bonus: 0,
    final_attack: 0,
  };
  if (!character) return zero;

  const charIdx = charLevel - 1;
  let charBase = 0;
  const charAtk = character.基础攻击力;
  if (Array.isArray(charAtk) && charIdx >= 0 && charIdx < charAtk.length) {
    charBase = Number(charAtk[charIdx]);
  }

  let weaponBase = 0;
  if (weapon) {
    const wIdx = weaponLevel - 1;
    const wAtk = weapon.基础攻击力;
    if (Array.isArray(wAtk) && wIdx >= 0 && wIdx < wAtk.length) {
      weaponBase = Number(wAtk[wIdx]);
    }
  }

  const baseAttack = charBase + weaponBase;
  const kw = kwargs as unknown as Record<string, string | number>;
  let attackBonusPercent = 0;
  let additionalAttack = 0;

  if (weapon) {
    for (const skill of (weapon.normal_skills as unknown[]) ?? []) {
      if (!skill || typeof skill !== "object") continue;
      const effect = String((skill as Record<string, unknown>).effect ?? "");
      const level = resolveSkillLevel(effect, kw);
      if (shouldSkipSa3(effect, kw)) continue;
      const curve = (skill as Record<string, unknown>).curve;
      if (effect === "攻击力+") {
        attackBonusPercent += getWeaponBonus(curve, level);
      } else if (effect === "附加攻击力+") {
        additionalAttack += getWeaponBonus(curve, level);
      }
    }

    if (Object.prototype.hasOwnProperty.call(weapon, "攻击力+")) {
      if (!shouldSkipSa3("攻击力+", kw)) {
        attackBonusPercent += getWeaponBonus(weapon["攻击力+"], resolveSkillLevel("攻击力+", kw));
      }
    }
    if (Object.prototype.hasOwnProperty.call(weapon, "附加攻击力+")) {
      if (!shouldSkipSa3("附加攻击力+", kw)) {
        additionalAttack += getWeaponBonus(weapon["附加攻击力+"], resolveSkillLevel("附加攻击力+", kw));
      }
    }

    attackBonusPercent += addSpecialPicksAttackPercent(weapon, {
      ws_name: kwargs.special_skill_1_name,
      ws_level: kwargs.special_skill_1_level,
      ws_stack: kwargs.special_skill_1_stack,
      ws2_name: kwargs.special_skill_2_name,
      ws2_level: kwargs.special_skill_2_level,
      ws2_stack: kwargs.special_skill_2_stack,
      target_name: "攻击力+",
    });
  }

  attackBonusPercent += equipmentAttackPercent * 100;

  const attackBonusMultiplier = 1 + attackBonusPercent / 100;
  const attackBonusAttack = baseAttack * attackBonusMultiplier;
  const equipmentFlatAttack = equipmentStatBonus.攻击力 ?? 0;
  const statBonus = { ...equipmentStatBonus };
  delete statBonus.攻击力;

  const intermediateAttack = attackBonusAttack + additionalAttack + equipmentFlatAttack;
  let ability = calculateAbilityBonusWithDetails(character, weapon, charLevel, kwargs, trustLevel);
  if (Object.keys(statBonus).length > 0) {
    const mainAttr = ability.main_attr;
    const subAttr = ability.sub_attr;
    let mainValue = ability.main_value;
    let subValue = ability.sub_value;
    if (mainAttr && statBonus[mainAttr] != null) mainValue += statBonus[mainAttr];
    if (subAttr && statBonus[subAttr] != null) subValue += statBonus[subAttr];
    const bonus = Math.trunc(mainValue) * 0.005 + Math.trunc(subValue) * 0.002;
    ability = { ...ability, main_value: mainValue, sub_value: subValue, bonus };
  }
  const finalAttack = intermediateAttack * (ability.bonus + 1);

  return {
    base_attack: baseAttack,
    char_base_attack: charBase,
    weapon_base_attack: weaponBase,
    attack_bonus_multiplier: attackBonusMultiplier,
    attack_bonus_attack: attackBonusAttack,
    additional_attack: additionalAttack,
    intermediate_attack: intermediateAttack,
    ability_bonus: ability.bonus,
    final_attack: finalAttack,
  };
}
