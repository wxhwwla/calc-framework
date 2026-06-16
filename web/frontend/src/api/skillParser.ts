/** 技能解析器（TypeScript 版）— 匹配 Python skill_parser 行为。 */

/** 用 DOM 解析器安全剥离 HTML 标签，防止正则 bypass。 */
function stripHtmlTags(html: string): string {
  if (typeof DOMParser !== "undefined") {
    const doc = new DOMParser().parseFromString(
      html.replace(/<BR\s*\/?>/gi, "\n"),
      "text/html",
    );
    return doc.body.textContent || "";
  }
  // 回退：在无 DOM 环境（测试）下用更严格的正则
  // 注意：输出仅用作 textContent，不用于 setHTML/innerHTML，XSS 风险可控
  return (
    html
      // 先处理 BR 换行
      .replace(/<BR\s*\/?>/gi, "\n")
      // 移除所有 HTML 标签（含自闭合、注释）
      .replace(/<!--[\s\S]*?-->/g, "")
      .replace(/<[^>]*>/g, "")
      // 移除 HTML 实体编码
      .replace(/&[^;]+;/g, " ")
      // 移除零宽字符和符号
      .replace(/[​-‍﻿]/g, "")
  );
}

export interface ParsedSkill {
  name: string;
  spType: string;
  trigger: string;
  effectiveMultiplier: number;
  atkBuffHint: number;
  hitCount: number;
  hasConditional: boolean;
  conditionalMult: number;
  damageType: "physical" | "magical" | "true";
  isHealing: boolean;
  spCost: number;
  initSp: number;
  duration: number;
  description: string;
  totalMult: number;
  _directAtkMult?: number;
  _equivDamageMult?: number;
}

export function parseSkill(skill: ArknightsSkill, level: number): ParsedSkill {
  const info: ParsedSkill = {
    name: skill.name ?? "",
    spType: skill.sp_type ?? "",
    trigger: skill.trigger ?? "",
    effectiveMultiplier: 1.0,
    atkBuffHint: 0,
    hitCount: 1,
    hasConditional: false,
    conditionalMult: 1.0,
    damageType: "physical",
    isHealing: false,
    spCost: 0,
    initSp: 0,
    duration: 0,
    description: "",
    totalMult: 1.0,
  };

  const levels = skill.levels ?? [];
  if (levels.length === 0) return info;

  const idx = Math.min(Math.max(level - 1, 0), levels.length - 1);
  const lv = levels[idx];
  const rawDesc = lv.description ?? "";
  const desc = stripWikiMarkup(rawDesc);
  info.description = desc;
  info.spCost = lv.sp_cost ?? 0;
  info.initSp = lv.init_sp ?? 0;
  try {
    info.duration = parseInt(String(lv.duration), 10) || 0;
  } catch {
    info.duration = 0;
  }

  // healing
  if (desc.includes("治疗") && desc.includes("攻击力")) {
    info.isHealing = true;
  }
  if (/相当于攻击力[\d.]+%的.*?(?:生命|血量)/.test(desc)) {
    info.isHealing = true;
  }

  // damage type
  if (desc.includes("真实")) info.damageType = "true";
  else if (desc.includes("法术")) info.damageType = "magical";
  else if (desc.includes("物理")) info.damageType = "physical";

  // conditional
  const condMatch = desc.match(/仅攻击到(?:一个|1个)敌人时.*?攻击力提升至(\d+(?:\.\d+)?)%/);
  if (condMatch) {
    info.hasConditional = true;
    info.conditionalMult = parseFloat(condMatch[1]) / 100;
  }

  // pure ASPD
  if (desc.includes("攻击速度") && !desc.includes("攻击力") && !desc.includes("相当于")) {
    info.effectiveMultiplier = 1.0;
    extractHitCount(info, desc);
    info.totalMult = info.effectiveMultiplier * info.hitCount;
    return info;
  }

  // ATK buff: 攻击力+XX%
  const buffMatch = desc.match(/攻击力\+(\d+(?:\.\d+)?)%/);
  if (buffMatch) {
    info.atkBuffHint = parseFloat(buffMatch[1]) / 100;
  }

  // direct ATK set: 攻击力提升至XX% (exclude conditional context)
  const beforeCond = desc.split(/仅攻击到/)[0];
  const directMatch = beforeCond.match(/攻击力提升至(\d+(?:\.\d+)?)%/);
  if (directMatch) {
    info._directAtkMult = parseFloat(directMatch[1]) / 100;
  }

  // equiv damage: 相当于攻击力XX%
  const eqMatch = desc.match(/相当于攻击力(\d+(?:\.\d+)?)%/);
  if (eqMatch) {
    info._equivDamageMult = parseFloat(eqMatch[1]) / 100;
  }

  // variant: 攻击力XX%的
  if (info._equivDamageMult === undefined) {
    const pctOfMatch = desc.match(/攻击力(\d+(?:\.\d+)?)%的/);
    if (pctOfMatch) {
      info._equivDamageMult = parseFloat(pctOfMatch[1]) / 100;
    }
  }

  extractHitCount(info, desc);
  resolveEffective(info);
  info.totalMult = info.effectiveMultiplier * info.hitCount;

  return info;
}

function resolveEffective(info: ParsedSkill) {
  const hasBuff = info.atkBuffHint > 0;
  const hasDirect = (info._directAtkMult ?? 1) > 1.0;
  const _equiv = info._equivDamageMult;
  const hasEquiv = _equiv !== undefined && (_equiv > 1.0 || (_equiv < 1.0 && _equiv !== 1.0));

  if (hasEquiv && _equiv !== undefined) {
    info.effectiveMultiplier = _equiv;
    return;
  }
  if (hasDirect && info._directAtkMult !== undefined) {
    info.effectiveMultiplier = info._directAtkMult;
    return;
  }
  if (hasBuff) {
    info.effectiveMultiplier = 1.0;
    return;
  }
  info.effectiveMultiplier = 1.0;
}

function extractHitCount(info: ParsedSkill, desc: string) {
  const hitMatch = desc.match(/(\d+)连发/) || desc.match(/(\d+)次射击/) || desc.match(/连续攻击(\d+)次/);
  if (hitMatch) {
    info.hitCount = parseInt(hitMatch[1], 10);
  }
}

function stripWikiMarkup(text: string): string {
  // 递归剥离所有 {{...}} wiki 标记（含嵌套）
  // 用深度计数器逐字符处理，确保正确处理任意深度嵌套
  let depth = 0;
  let result = "";
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '{' && text[i + 1] === '{') {
      depth++;
      i++; // 跳过第二个 {
      continue;
    }
    if (ch === '}' && text[i + 1] === '}') {
      depth--;
      i++; // 跳过第二个 }
      continue;
    }
    if (depth === 0) {
      result += ch;
    }
  }
  // 用 DOM 解析器安全剥离 HTML 标签（比正则更完整，防止 bypass）
  const cleaned = stripHtmlTags(result);
  return cleaned.replace(/\s+/g, " ").trim();
}

export function parseAutoAttack(): ParsedSkill {
  return {
    name: "普攻",
    spType: "",
    trigger: "",
    effectiveMultiplier: 1.0,
    atkBuffHint: 0,
    hitCount: 1,
    hasConditional: false,
    conditionalMult: 1.0,
    damageType: "physical",
    isHealing: false,
    spCost: 0,
    initSp: 0,
    duration: 0,
    description: "普通攻击",
    totalMult: 1.0,
  };
}

export interface ArknightsSkillLevel {
  description: string;
  sp_cost: number;
  init_sp: number;
  duration: string;
}

export interface ArknightsSkill {
  name: string;
  sp_type: string;
  trigger: string;
  levels: ArknightsSkillLevel[];
}
