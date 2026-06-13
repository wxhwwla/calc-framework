import i18n from "../i18n/config";

const BASE = "/api/adapters";

export interface AdapterInfo {
  id: string;
  name: string;
  game: string;
  version: string;
  description: string;
}

export async function listAdapters(): Promise<AdapterInfo[]> {
  const r = await fetch(BASE);
  if (!r.ok) throw new Error(`${i18n.t("api.adaptersListGetFailed")}: ${r.statusText}`);
  return r.json();
}

export async function fetchAdapterMeta(adapterId: string): Promise<Record<string, unknown>> {
  const r = await fetch(`${BASE}/${encodeURIComponent(adapterId)}/meta`);
  if (!r.ok) throw new Error(`${i18n.t("api.adapterMetaGetFailed")}: ${r.statusText}`);
  const data = await r.json();
  return data.meta as Record<string, unknown>;
}
