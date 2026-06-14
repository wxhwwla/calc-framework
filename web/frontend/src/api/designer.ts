import i18n from "../i18n/config";

const BASE = "/api/data";

export interface InverseResponse {
  base: number;
  growth: number;
  divisor: number;
  offset: number;
  special: number | null;
  formula: string;
  valid: boolean;
  details: string;
}

export async function inverseFormula(
  type: "attribute" | "skill",
  values: number[],
): Promise<InverseResponse> {
  const r = await fetch(`${BASE}/inverse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type, values }),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`${i18n.t("api.inverseFailed")}: ${text}`);
  }
  return r.json();
}

export async function createCharacter(data: Record<string, unknown>): Promise<void> {
  const r = await fetch(`${BASE}/characters`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`${i18n.t("api.createCharFailed")}: ${r.statusText}`);
}

export async function updateCharacter(name: string, data: Record<string, unknown>): Promise<void> {
  const r = await fetch(`${BASE}/characters/${encodeURIComponent(name)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`${i18n.t("api.updateCharFailed")}: ${r.statusText}`);
}

export async function deleteCharacter(name: string): Promise<void> {
  const r = await fetch(`${BASE}/characters/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
  if (!r.ok) throw new Error(`${i18n.t("api.deleteCharFailed")}: ${r.statusText}`);
}

export async function createWeapon(data: Record<string, unknown>): Promise<void> {
  const r = await fetch(`${BASE}/weapons`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`${i18n.t("api.createWeaponFailed")}: ${r.statusText}`);
}

export async function updateWeapon(name: string, data: Record<string, unknown>): Promise<void> {
  const r = await fetch(`${BASE}/weapons/${encodeURIComponent(name)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`${i18n.t("api.updateWeaponFailed")}: ${r.statusText}`);
}

export async function deleteWeapon(name: string): Promise<void> {
  const r = await fetch(`${BASE}/weapons/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
  if (!r.ok) throw new Error(`${i18n.t("api.deleteWeaponFailed")}: ${r.statusText}`);
}

export async function createEquipment(data: Record<string, unknown>): Promise<void> {
  const r = await fetch(`${BASE}/equipments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`${i18n.t("api.createEquipFailed")}: ${r.statusText}`);
}

export async function updateEquipment(name: string, data: Record<string, unknown>): Promise<void> {
  const r = await fetch(`${BASE}/equipments/${encodeURIComponent(name)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`${i18n.t("api.updateEquipFailed")}: ${r.statusText}`);
}

export async function deleteEquipment(name: string): Promise<void> {
  const r = await fetch(`${BASE}/equipments/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
  if (!r.ok) throw new Error(`${i18n.t("api.deleteEquipFailed")}: ${r.statusText}`);
}
