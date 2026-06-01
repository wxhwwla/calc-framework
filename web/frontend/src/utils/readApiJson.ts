/** 解析 API JSON；若收到 HTML（多为后端未启动或端口错误）则抛出可读错误 */
export async function readApiJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(
      text ? `请求失败 (${response.status}): ${text.slice(0, 200)}` : `请求失败: ${response.statusText}`,
    );
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    const text = await response.text();
    if (/^\s*</.test(text)) {
      throw new Error(
        "API 返回了 HTML 而非 JSON。请先启动后端：cd web/backend && python -m uvicorn main:app --reload --port 8000",
      );
    }
    throw new Error(`非 JSON 响应: ${text.slice(0, 120)}`);
  }
  return response.json() as Promise<T>;
}
