/** 搜索任务 combo_key（对齐 persist.store._task_key）。 */

export function buildComboKey(
  weaponName: string,
  chest: string,
  gloves: string,
  accessoryA: string,
  accessoryB: string,
): string {
  return [weaponName, chest, gloves, accessoryA, accessoryB].join("|");
}
