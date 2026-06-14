import i18n from "../i18n/config";

const BASE = "/api/pack";

export interface ThemeColors {
  primary: string;
  background: string;
  surface: string;
  text: string;
  text_secondary: string;
  border: string;
  success: string;
  warning: string;
  error: string;
}

export interface ThemeConfig {
  schema_version: string;
  name: string;
  font: {
    family: string;
    size: number;
    weight: string;
  };
  colors: ThemeColors;
  spacing: {
    padding: number;
    gap: number;
  };
}

export async function fetchDefaultTheme(): Promise<ThemeConfig> {
  const r = await fetch(`${BASE}/theme/default`);
  if (!r.ok) throw new Error(`${i18n.t("api.defaultThemeGetFailed")}: ${r.statusText}`);
  return r.json();
}

export async function previewExport(payload: {
  meta: Record<string, unknown>;
  dag: Record<string, unknown>;
  layout: Record<string, unknown>;
  theme?: Record<string, unknown>;
  data_files?: Record<string, unknown[]>;
}): Promise<{
  meta: Record<string, unknown>;
  dag_nodes: number;
  layout_sections: number;
  has_theme: boolean;
  data_files: Record<string, number>;
}> {
  const r = await fetch(`${BASE}/export/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`${i18n.t("api.previewFailed")}: ${r.statusText}`);
  return r.json();
}

export async function downloadCalcpack(
  payload: {
    meta: Record<string, unknown>;
    dag: Record<string, unknown>;
    layout: Record<string, unknown>;
    theme?: Record<string, unknown>;
    data_files?: Record<string, unknown[]>;
    filename?: string;
  },
): Promise<void> {
  const r = await fetch(`${BASE}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`${i18n.t("api.exportFailed")}: ${r.statusText}`);

  const blob = await r.blob();
  const disposition = r.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename="?(.+?)"?$/);
  const filename = match?.[1] ?? "config.calcpack";

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
