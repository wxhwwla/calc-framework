const HUB_BASE = "/api/hub";

export interface HubPackInfo {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  tags: string[];
  rating: number;
  rating_count: number;
  download_count: number;
  file_size: number;
  screenshot_urls: string[];
  created_at: string;
  updated_at: string;
}

export interface PackListResponse {
  packs: HubPackInfo[];
  total: number;
  offset: number;
  limit: number;
}

export async function listPacks(params: {
  search?: string;
  tag?: string;
  sort?: string;
  order?: string;
  offset?: number;
  limit?: number;
}): Promise<PackListResponse> {
  const qs = new URLSearchParams();
  if (params.search) qs.set("search", params.search);
  if (params.tag) qs.set("tag", params.tag);
  if (params.sort) qs.set("sort", params.sort);
  if (params.order) qs.set("order", params.order);
  if (params.offset) qs.set("offset", String(params.offset));
  if (params.limit) qs.set("limit", String(params.limit));
  const resp = await fetch(`${HUB_BASE}/packs?${qs.toString()}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export async function getPack(id: string): Promise<HubPackInfo> {
  const resp = await fetch(`${HUB_BASE}/packs/${id}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export async function createPack(data: {
  name: string;
  version: string;
  description?: string;
  author?: string;
  tags?: string[];
}): Promise<{ id: string; name: string; version: string; message: string }> {
  const resp = await fetch(`${HUB_BASE}/packs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export async function uploadPackFile(
  packId: string,
  file: File
): Promise<{ filename: string; size: number }> {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`${HUB_BASE}/packs/${packId}/upload`, {
    method: "POST",
    body: form,
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export async function downloadPackFile(
  packId: string,
  filename: string
): Promise<void> {
  const resp = await fetch(`${HUB_BASE}/packs/${packId}/download/${filename}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function ratePack(
  packId: string,
  score: number,
  comment?: string
): Promise<{ rating: number; rating_count: number }> {
  const resp = await fetch(`${HUB_BASE}/packs/${packId}/rate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ score, comment: comment || "" }),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}
