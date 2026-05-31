const BASE = "/api/history";

export interface HistoryEntry {
  label?: string;
  char_name: string;
  weapon_name: string;
  context?: Record<string, unknown>;
  outputs?: Record<string, number>;
  node_values?: Record<string, number | string | null>;
  saved_at?: string;
  [key: string]: unknown;
}

export async function fetchHistory(): Promise<HistoryEntry[]> {
  const r = await fetch(BASE);
  if (!r.ok) throw new Error(`获取计算历史失败: ${r.statusText}`);
  return r.json();
}

export async function saveHistory(entry: HistoryEntry): Promise<void> {
  const r = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
  });
  if (!r.ok) throw new Error(`保存计算历史失败: ${r.statusText}`);
}
