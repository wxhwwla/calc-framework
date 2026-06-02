const BASE = "/api/contribute";

export async function validateContributeData(data: unknown): Promise<{ valid: boolean; errors: string[] }> {
  const r = await fetch(`${BASE}/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return r.json();
}

export async function submitContributeData(data: unknown): Promise<{ message: string; filename: string }> {
  const r = await fetch(`${BASE}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(err.detail || "提交失败");
  }
  return r.json();
}
