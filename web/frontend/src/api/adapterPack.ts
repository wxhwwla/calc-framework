const BASE = "/api/adapters";

export interface DataEntitySummary {
  key: string;
  label: string;
  count: number;
  read_only: boolean;
}

export interface PackExportBundle {
  adapter_id: string;
  meta: Record<string, unknown>;
  layout: Record<string, unknown>;
  dag: Record<string, unknown>;
  data_files: Record<string, Record<string, unknown>[]>;
  data_summary: Record<string, number>;
}

export async function fetchAdapterLayout(adapterId: string): Promise<Record<string, unknown>> {
  const r = await fetch(`${BASE}/${encodeURIComponent(adapterId)}/layout`);
  if (!r.ok) throw new Error(`获取 layout 失败: ${r.statusText}`);
  return r.json();
}

export async function fetchAdapterDag(adapterId: string): Promise<Record<string, unknown>> {
  const r = await fetch(`${BASE}/${encodeURIComponent(adapterId)}/dag`);
  if (!r.ok) throw new Error(`获取 DAG 失败: ${r.statusText}`);
  return r.json();
}

export async function fetchAdapterDataSummary(adapterId: string): Promise<DataEntitySummary[]> {
  const r = await fetch(`${BASE}/${encodeURIComponent(adapterId)}/data-summary`);
  if (!r.ok) throw new Error(`获取数据摘要失败: ${r.statusText}`);
  const data = await r.json();
  return data.entities as DataEntitySummary[];
}

export async function fetchAdapterPackBundle(adapterId: string): Promise<PackExportBundle> {
  const r = await fetch(`${BASE}/${encodeURIComponent(adapterId)}/pack-bundle`);
  if (!r.ok) throw new Error(`获取导出包失败: ${r.statusText}`);
  return r.json();
}
