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
  if (!r.ok) throw new Error(`获取适配器列表失败: ${r.statusText}`);
  return r.json();
}

export async function fetchAdapterMeta(adapterId: string): Promise<Record<string, unknown>> {
  const r = await fetch(`${BASE}/${encodeURIComponent(adapterId)}/meta`);
  if (!r.ok) throw new Error(`获取适配器 meta 失败: ${r.statusText}`);
  const data = await r.json();
  return data.meta as Record<string, unknown>;
}
