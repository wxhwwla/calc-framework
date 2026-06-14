import i18n from "../i18n/config";

const BASE = "/api/data/profiles";

export async function fetchProfileRows(profileId: string, entityKey: string): Promise<Record<string, unknown>[]> {
  const r = await fetch(`${BASE}/${encodeURIComponent(profileId)}/${encodeURIComponent(entityKey)}`);
  if (!r.ok) throw new Error(`${i18n.t("api.profileLoadFailed")}: ${r.statusText}`);
  return r.json();
}

export async function createProfileRow(
  profileId: string,
  entityKey: string,
  data: Record<string, unknown>,
): Promise<void> {
  const r = await fetch(`${BASE}/${encodeURIComponent(profileId)}/${encodeURIComponent(entityKey)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`${i18n.t("api.profileCreateFailed")}: ${await r.text()}`);
}

export async function updateProfileRow(
  profileId: string,
  entityKey: string,
  name: string,
  data: Record<string, unknown>,
): Promise<void> {
  const r = await fetch(
    `${BASE}/${encodeURIComponent(profileId)}/${encodeURIComponent(entityKey)}/${encodeURIComponent(name)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
  if (!r.ok) throw new Error(`${i18n.t("api.profileUpdateFailed")}: ${await r.text()}`);
}

export async function deleteProfileRow(
  profileId: string,
  entityKey: string,
  name: string,
): Promise<void> {
  const r = await fetch(
    `${BASE}/${encodeURIComponent(profileId)}/${encodeURIComponent(entityKey)}/${encodeURIComponent(name)}`,
    { method: "DELETE" },
  );
  if (!r.ok) throw new Error(`${i18n.t("api.profileDeleteFailed")}: ${await r.text()}`);
}

export interface DagVerifyResult {
  entity_name: string;
  level: number;
  outputs: Record<string, number>;
  node_values: Record<string, number>;
  node_count: number;
}

export interface ValidateResult {
  profile_id: string;
  entity_key: string;
  total: number;
  valid: number;
  errors: { index: number; name: string; messages: string[] }[];
}

export async function validateData(profileId: string, entityKey: string): Promise<ValidateResult> {
  const r = await fetch("/api/data/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile_id: profileId, entity_key: entityKey }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function dagVerify(
  profileId: string,
  entityKey: string,
  entityName: string,
  level: number = 90,
): Promise<DagVerifyResult> {
  const r = await fetch("/api/data/dag-verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile_id: profileId, entity_key: entityKey, entity_name: entityName, level }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
