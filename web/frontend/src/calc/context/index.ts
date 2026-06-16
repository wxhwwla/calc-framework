export { buildLoadoutContext } from "./buildLoadoutContext";
export type { LoadoutContext } from "./buildLoadoutContext";

// 区域/乘区计算
export {
  calculateAttributeZonesWithDetails,
  calculateAbilityBonusWithDetails,
  calculateFinalAttackWithDetails,
} from "./zones";
export type {
  AttrZoneDetail,
  AbilityBonusDetail,
  FinalAttackDetail,
} from "./zones";

// 装备词条解析
export { resolveEquipmentModifiers } from "./equipmentModifiers";
export type { EquipmentEffect, EquipmentModifiers } from "./equipmentModifiers";

// 技能倍率
export { resolveSkillMultiplier } from "./skillResolve";

// 武器特殊能力
export {
  addSpecialPicksToMainSubBonus,
  addSpecialPicksToAbilityPct,
  addSpecialPicksAttackPercent,
  resolveSkillLevel,
  shouldSkipSa3,
} from "./specialSkills";

// 武器工具函数
export {
  getWeaponBonus,
  getCharAttrAtLevel,
  getWeaponRefinementBonus,
  weaponSkillKwargsFromPayload,
  emptySkillKwargs,
  TRUST_ADD,
} from "./weaponUtils";
export type { SkillKwargs } from "./weaponUtils";

// context 富化
export { enrichLoadoutContext } from "./contextOverrides";
