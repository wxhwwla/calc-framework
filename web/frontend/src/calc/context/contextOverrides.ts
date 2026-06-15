/** context enrichment：manual_buff、额外暴击、装备效果（对齐 web_context_enrich.py）。 */

import type { WebLoadoutPayload } from "../../api/loadout";
import type { LoadoutContext } from "./buildLoadoutContext";
import type { EquipmentEffect, EquipmentModifiers } from "./equipmentModifiers";
import { resolveSkillMultiplier } from "./skillResolve";

function applyZoneEffect(
  computed: Record<string, unknown>,
  character: Record<string, unknown>,
  effectType: string,
  value: number,
): void {
  const v = Number(value);
  const et = effectType.trim();
  if (et === "暴击率") {
    character.暴击率 = Number(character.暴击率 ?? 0.05) + v;
  } else if (et === "暴击伤害") {
    character.暴击伤害 = Number(character.暴击伤害 ?? 0.5) + v;
  } else if (
    et === "伤害类型加成" ||
    et === "技能类型伤害加成" ||
    et === "技能类型加成" ||
    et === "失衡伤害加成" ||
    et === "其他伤害加成" ||
    et === "伤害加成"
  ) {
    computed.伤害加成 = Number(computed.伤害加成 ?? 1) + v;
  } else if (et === "伤害减免") {
    computed.伤害减免 = Number(computed.伤害减免 ?? 1) * (1 - v);
  } else if (et === "增幅") {
    computed.增幅 = Number(computed.增幅 ?? 1) + v;
  } else if (et === "虚弱") {
    computed.虚弱 = Number(computed.虚弱 ?? 1) * (1 - v);
  } else if (et === "庇护") {
    computed.庇护 = Math.min(Number(computed.庇护 ?? 1), 1 - v);
  } else if (et === "脆弱") {
    computed.脆弱 = Number(computed.脆弱 ?? 1) + v;
  } else if (et === "易伤") {
    computed.易伤 = Number(computed.易伤 ?? 1) + v;
  } else if (et === "连击增伤") {
    computed.连击增伤 = Number(computed.连击增伤 ?? 1) + v;
  } else if (et === "非主控减伤") {
    computed.非主控减伤 = Number(computed.非主控减伤 ?? 1) * (1 - v);
  } else if (et === "特殊乘区") {
    computed.特殊乘区 = Number(computed.特殊乘区 ?? 1) * v;
  }
}

function iterManualBuffEntries(
  manualBuffs: WebLoadoutPayload["manual_buffs"],
): { effect_type: string; value: number }[] {
  const out: { effect_type: string; value: number }[] = [];
  for (const entries of Object.values(manualBuffs ?? {})) {
    for (const entry of entries) {
      if (entry?.effect_type) out.push(entry);
    }
  }
  return out;
}

export function enrichLoadoutContext(
  ctx: LoadoutContext,
  payload: WebLoadoutPayload,
  equip: EquipmentModifiers,
): LoadoutContext {
  const computed = (ctx.computed ?? {}) as Record<string, unknown>;
  const character = (ctx.character ?? {}) as Record<string, unknown>;
  const equipment = (ctx.equipment ?? {}) as Record<string, unknown>;
  const userInput = (ctx.user_input ?? {}) as Record<string, unknown>;

  computed.技能倍率 = resolveSkillMultiplier(
    payload.char_data,
    payload.skill_1_level,
    payload.skill_2_level,
    payload.skill_3_level,
  );

  if (payload.extra_crit_rate) {
    character.暴击率 = Number(character.暴击率 ?? 0.05) + payload.extra_crit_rate;
    userInput.额外暴击率 = payload.extra_crit_rate;
  }
  if (payload.extra_crit_damage) {
    character.暴击伤害 = Number(character.暴击伤害 ?? 0.5) + payload.extra_crit_damage;
    userInput.额外暴击伤害 = payload.extra_crit_damage;
  }

  const flatStats = { ...equip.flat_stats };
  equipment.攻击力平值 = flatStats.攻击力 ?? 0;
  delete flatStats.攻击力;

  for (const entry of iterManualBuffEntries(payload.manual_buffs)) {
    applyZoneEffect(computed, character, entry.effect_type, entry.value);
  }
  for (const effect of equip.effects as EquipmentEffect[]) {
    applyZoneEffect(computed, character, effect.effect_type, effect.value);
  }

  ctx.computed = computed;
  ctx.character = character;
  ctx.equipment = equipment;
  ctx.user_input = userInput;
  return ctx;
}
