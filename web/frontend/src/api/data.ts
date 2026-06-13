import i18n from "../i18n/config";

const BASE = "/api/data";

export interface CharacterSummary {
  名称: string;
  类型: string;
  星级: number;
  武器: string;
  主能力: string;
  副能力: string;
}

export interface WeaponSummary {
  名称: string;
  类型: string;
  星级: number;
  附加属性?: Record<string, number>;
  武器技能?: string;
  普通技能?: string;
  特殊技能?: string;
}

export interface EquipmentSummary {
  名称: string;
  装备种类: string;
  部位: string;
  稀有度: string;
  所属套组: string;
  属性词条: string[];
  三件套效果: string[];
}

export interface DataSummary {
  characters_count: number;
  weapons_count: number;
  equipments_count: number;
  equipment_sets: string[];
  character_types: string[];
  weapon_types: string[];
}

// ── 角色 ──

export async function fetchCharacters(): Promise<CharacterSummary[]> {
  const r = await fetch(`${BASE}/characters`);
  if (!r.ok) throw new Error(`${i18n.t("api.charactersListGetFailed")}: ${r.statusText}`);
  return r.json();
}

export async function fetchCharacter(name: string): Promise<Record<string, unknown>> {
  const r = await fetch(`${BASE}/characters/${encodeURIComponent(name)}`);
  if (!r.ok) throw new Error(`${i18n.t("api.characterDetailGetFailed")}: ${r.statusText}`);
  return r.json();
}

export async function fetchCharactersFull(): Promise<Record<string, unknown>[]> {
  const r = await fetch(`${BASE}/characters/detail/all`);
  if (!r.ok) throw new Error(`${i18n.t("api.charactersFullGetFailed")}: ${r.statusText}`);
  return r.json();
}

// ── 武器 ──

export async function fetchWeapons(): Promise<WeaponSummary[]> {
  const r = await fetch(`${BASE}/weapons`);
  if (!r.ok) throw new Error(`${i18n.t("api.weaponsListGetFailed")}: ${r.statusText}`);
  return r.json();
}

export async function fetchWeapon(name: string): Promise<Record<string, unknown>> {
  const r = await fetch(`${BASE}/weapons/${encodeURIComponent(name)}`);
  if (!r.ok) throw new Error(`${i18n.t("api.weaponDetailGetFailed")}: ${r.statusText}`);
  return r.json();
}

export async function fetchWeaponsFull(): Promise<Record<string, unknown>[]> {
  const r = await fetch(`${BASE}/weapons/detail/all`);
  if (!r.ok) throw new Error(`${i18n.t("api.weaponsFullGetFailed")}: ${r.statusText}`);
  return r.json();
}

// ── 装备 ──

export async function fetchEquipments(): Promise<EquipmentSummary[]> {
  const r = await fetch(`${BASE}/equipments`);
  if (!r.ok) throw new Error(`${i18n.t("api.equipmentsListGetFailed")}: ${r.statusText}`);
  return r.json();
}

export async function fetchEquipment(name: string): Promise<Record<string, unknown>> {
  const r = await fetch(`${BASE}/equipments/${encodeURIComponent(name)}`);
  if (!r.ok) throw new Error(`${i18n.t("api.equipmentDetailGetFailed")}: ${r.statusText}`);
  return r.json();
}

export async function fetchEquipmentsFull(): Promise<Record<string, unknown>[]> {
  const r = await fetch(`${BASE}/equipments/detail/all`);
  if (!r.ok) throw new Error(`${i18n.t("api.equipmentsFullGetFailed")}: ${r.statusText}`);
  return r.json();
}

export async function fetchEquipmentsBySet(setName: string): Promise<Record<string, unknown>[]> {
  const r = await fetch(`${BASE}/equipments/set/${encodeURIComponent(setName)}`);
  if (!r.ok) throw new Error(`${i18n.t("api.equipmentsFilterBySetFailed")}: ${r.statusText}`);
  return r.json();
}

export async function fetchEquipmentsBySlot(slot: string): Promise<Record<string, unknown>[]> {
  const r = await fetch(`${BASE}/equipments/slot/${encodeURIComponent(slot)}`);
  if (!r.ok) throw new Error(`${i18n.t("api.equipmentsFilterBySlotFailed")}: ${r.statusText}`);
  return r.json();
}

// ── 统计 ──

export async function fetchDataSummary(): Promise<DataSummary> {
  const r = await fetch(`${BASE}/summary`);
  if (!r.ok) throw new Error(`${i18n.t("api.dataSummaryGetFailed")}: ${r.statusText}`);
  return r.json();
}
