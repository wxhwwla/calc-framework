const BASE = "/api";

export interface AdapterInfo {
  name: string;
  game: string;
  version: string;
  description: string;
}

export interface AdapterAttr {
  name: string;
  type: string;
  source: string;
  default: number | boolean | null;
  description: string;
}

export interface EvaluateResult {
  outputs: Record<string, number>;
  node_values: Record<string, number | string | null>;
  execution_order: string[];
}

export async function fetchAdapters(): Promise<AdapterInfo[]> {
  const r = await fetch(`${BASE}/adapters`);
  if (!r.ok) throw new Error(`Failed to fetch adapters: ${r.statusText}`);
  return r.json();
}

export async function fetchSchema(name: string): Promise<AdapterAttr[]> {
  const r = await fetch(`${BASE}/adapters/${encodeURIComponent(name)}/schema`);
  if (!r.ok) throw new Error(`Failed to fetch schema: ${r.statusText}`);
  const data = await r.json();
  return data.attributes;
}

export async function evaluate(
  adapter: string,
  context: Record<string, Record<string, number | boolean | string>>,
): Promise<EvaluateResult> {
  const r = await fetch(`${BASE}/compute/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ adapter, context }),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`Compute failed (${r.status}): ${text}`);
  }
  return r.json();
}
