const BASE = "/api/data/profiles";

export async function fetchProfileRows(profileId: string, entityKey: string): Promise<Record<string, unknown>[]> {
  const r = await fetch(`${BASE}/${encodeURIComponent(profileId)}/${encodeURIComponent(entityKey)}`);
  if (!r.ok) throw new Error(`加载失败: ${r.statusText}`);
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
  if (!r.ok) throw new Error(`新增失败: ${await r.text()}`);
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
  if (!r.ok) throw new Error(`更新失败: ${await r.text()}`);
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
  if (!r.ok) throw new Error(`删除失败: ${await r.text()}`);
}
