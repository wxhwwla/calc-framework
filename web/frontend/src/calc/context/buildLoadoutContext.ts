/** Web loadout → DAG adapter context（对齐 loader.py + web_loadout_bridge + enrich）。 */

import type { WebLoadoutPayload } from "../../api/loadout";
import { materializeCharacterEntity, materializeWeaponEntity } from "../materialize";
import { enrichLoadoutContext } from "./contextOverrides";
import { resolveEquipmentModifiers } from "./equipmentModifiers";
import {
  calculateAbilityBonusWithDetails,
  calculateAttributeZonesWithDetails,
  calculateFinalAttackWithDetails,
} from "./zones";
import { getCharAttrAtLevel, getWeaponRefinementBonus, weaponSkillKwargsFromPayload } from "./weaponUtils";

export type LoadoutContext = Record<string, unknown>;

export function buildLoadoutContext(payload: WebLoadoutPayload): LoadoutContext {
  const char = materializeCharacterEntity(payload.char_data);
  const weapon = materializeWeaponEntity(payload.weapon_data);
  const charLevel = payload.char_level;
  const weaponLevel = payload.weapon_level;
  const trustLevel = payload.trust_level;
  const kwargs = weaponSkillKwargsFromPayload(weapon, payload.weapon_skill_values);
  const refineLevel = Number(weapon.精炼等级 ?? 1);
  const refineBonus = getWeaponRefinementBonus(weapon, refineLevel);
  const equip = resolveEquipmentModifiers(payload);

  const attr = calculateAttributeZonesWithDetails(char, weapon, charLevel, kwargs, trustLevel);
  const ability = calculateAbilityBonusWithDetails(char, weapon, charLevel, kwargs, trustLevel);
  const final = calculateFinalAttackWithDetails(
    char,
    weapon,
    charLevel,
    weaponLevel,
    kwargs,
    trustLevel,
    equip.flat_stats,
    equip.attack_percent,
  );

  const ep = payload.enemy_params;
  const layoutMode = payload.calc_mode ?? payload.calculation_mode ?? "zone_snapshot";

  const ctx: LoadoutContext = {
    character: {
      基础攻击: final.char_base_attack,
      力量: attr.力量.base,
      敏捷: attr.敏捷.base,
      智识: attr.智识.base,
      意志: attr.意志.base,
      暴击率: Number(char.暴击率 ?? char.crit_rate ?? 0.05),
      暴击伤害: Number(char.暴击伤害 ?? char.crit_damage ?? 0.5),
      主能力: ability.main_attr,
      副能力: ability.sub_attr,
      基础生命值: getCharAttrAtLevel(char, "基础生命值", charLevel),
      基础防御力: getCharAttrAtLevel(char, "基础防御力", charLevel),
    },
    weapon: {
      基础攻击: final.weapon_base_attack,
      "攻击力+": final.attack_bonus_multiplier - 1,
      "附加攻击力+": final.additional_attack,
      精炼等级: refineLevel,
      "法术伤害+": 0,
      "攻击力+平值": 0,
      "最大生命值+": 0,
    },
    equipment: {
      攻击力平值: equip.flat_stats.攻击力 ?? 0,
    },
    enemy: {
      防御: ep.enemy_defense,
    },
    computed: {
      主能力平值加算: ability.main_flat,
      副能力平值加算: ability.sub_flat,
      主能力百分比: ability.main_pct,
      副能力百分比: ability.sub_pct,
      主能力: ability.main_attr,
      副能力: ability.sub_attr,
      力量基础值: attr.力量.base,
      力量加成值: attr.力量.bonus,
      力量最终值: attr.力量.total,
      敏捷基础值: attr.敏捷.base,
      敏捷加成值: attr.敏捷.bonus,
      敏捷最终值: attr.敏捷.total,
      智识基础值: attr.智识.base,
      智识加成值: attr.智识.bonus,
      智识最终值: attr.智识.total,
      意志基础值: attr.意志.base,
      意志加成值: attr.意志.bonus,
      意志最终值: attr.意志.total,
      最终攻击力: final.final_attack,
      基础攻击力合计: final.base_attack,
      角色基础攻击力: final.char_base_attack,
      武器基础攻击力: final.weapon_base_attack,
      攻击加成攻击力: final.attack_bonus_attack,
      中间攻击力: final.intermediate_attack,
      额外攻击力: final.additional_attack,
      能力值加成: final.ability_bonus,
      技能倍率: 1,
      暴击区: 1,
      伤害加成: 1,
      伤害减免: 1,
      增幅: 1,
      虚弱: 1,
      庇护: 1,
      脆弱: 1,
      易伤: 1,
      防御: 0.5,
      失衡易伤: 1,
      抗性: 1,
      非主控减伤: 1,
      连击增伤: 1,
      特殊乘区: 1,
      武器精炼主能力值加成: refineBonus.mainAbility,
      武器精炼附加攻击力加成: refineBonus.additionalAttack,
    },
    user_input: {
      skill_1_level: payload.skill_1_level,
      skill_2_level: payload.skill_2_level,
      skill_3_level: payload.skill_3_level,
      calc_mode: layoutMode,
      敌人防御: ep.enemy_defense,
      敌人抗性: ep.enemy_resistance,
      无视抗性: ep.ignore_resistance,
      失衡易伤系数: ep.imbalance_vulnerability_coeff,
      是否失衡: ep.is_unbalanced,
      是否真实伤害: ep.is_true_damage,
      连击层数: ep.combo_stacks,
      破防层数: ep.break_defense_stacks,
      附带效果倍率: ep.attached_effect_multiplier,
      "腐蚀计时(秒)": ep.corrosion_duration_seconds,
    },
  };

  return enrichLoadoutContext(ctx, payload, equip);
}
