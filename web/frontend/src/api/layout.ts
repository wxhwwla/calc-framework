const BASE = "/api/layout";

export interface LayoutSection {
  id: string;
  type: "inputs" | "outputs" | "widget";
  title: string;
  variables?: string[];
  outputs?: string[];
  columns?: number;
  widget_type?: string;
  widget_config?: Record<string, unknown>;
}

export interface LayoutDefinition {
  schema_version: string;
  name: string;
  description?: string;
  sections: LayoutSection[];
}

export interface DagVariable {
  type: string;
  source: string;
  description?: string;
  default?: number | boolean | string | null;
  min?: number | null;
  max?: number | null;
  options?: string[];
  ui_control?: {
    widget?: string;
    step?: number;
    options?: string[];
  };
}

export interface AttrSchemaEntry {
  name: string;
  type: string;
  source: string;
  default?: number | boolean | null;
  description?: string;
}

export async function fetchLayout(): Promise<LayoutDefinition> {
  const r = await fetch(BASE);
  if (!r.ok) throw new Error(`获取 layout 失败: ${r.statusText}`);
  return r.json();
}

export async function fetchVariables(): Promise<Record<string, DagVariable>> {
  const r = await fetch(`${BASE}/variables`);
  if (!r.ok) throw new Error(`获取 variables 失败: ${r.statusText}`);
  return r.json();
}

export async function fetchAttrSchema(): Promise<AttrSchemaEntry[]> {
  const r = await fetch(`${BASE}/schema`);
  if (!r.ok) throw new Error(`获取 schema 失败: ${r.statusText}`);
  const data = await r.json();
  return data.attributes;
}

export async function fetchDag(): Promise<Record<string, unknown>> {
  const r = await fetch(`${BASE}/dag`);
  if (!r.ok) throw new Error(`获取 DAG 失败: ${r.statusText}`);
  return r.json();
}
