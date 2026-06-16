/** 根据技能滑块解析技能倍率（对齐 skill_resolve.py）。 */

import { materializeCharacterEntity } from "../materialize";
import { valueAtLevel } from "../formula";

export function resolveSkillMultiplier(
  charData: Record<string, unknown>,
  skill1: number,
  skill2: number,
  skill3: number,
): number {
  const char = materializeCharacterEntity(charData);
  const picks: [string, number][] = [
    ["战技倍率", skill1],
    ["连携技倍率", skill2],
    ["终结技倍率", skill3],
  ];
  for (const [field, level] of picks) {
    if (level <= 0) continue;
    const segments = char[field];
    if (!Array.isArray(segments) || segments.length === 0) continue;
    const firstSegment = segments[0];
    if (!Array.isArray(firstSegment) || firstSegment.length === 0) continue;
    const value = valueAtLevel(firstSegment as number[], level);
    if (value != null) return value / 100;
  }
  return 1;
}
