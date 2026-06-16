/** 武器 scope 过滤（对齐 api/search_catalog.filter_weapons_by_scope）。 */

export function filterWeaponsByScope(
  allWeapons: Record<string, unknown>[],
  charData: Record<string, unknown>,
  currentWeapon: Record<string, unknown>,
  weaponScopeLabel: string,
  weaponCandidateNames?: string[] | null,
): Record<string, unknown>[] {
  const scope = (weaponScopeLabel || "").trim();
  const weaponType = String(charData.武器 ?? "");
  const currentStar = currentWeapon.星级;
  const currentName = currentWeapon.名称;
  const nameFilter =
    weaponCandidateNames && weaponCandidateNames.length > 0
      ? new Set(weaponCandidateNames.map((n) => String(n).trim()).filter(Boolean))
      : null;

  const out: Record<string, unknown>[] = [];
  for (const weapon of allWeapons) {
    const name = String(weapon.名称 ?? "");
    if (nameFilter && !nameFilter.has(name)) continue;
    if (weapon.类型 !== weaponType) continue;
    if (scope === "同类型同星级" && weapon.星级 !== currentStar) continue;
    if (scope === "当前武器" && name !== currentName) continue;
    out.push(weapon);
  }
  return out;
}
