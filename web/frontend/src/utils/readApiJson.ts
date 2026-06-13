import i18n from "../i18n/config";

/** 解析 API JSON；若收到 HTML（多为后端未启动或端口错误）则抛出可读错误 */
export async function readApiJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(
      text ? `${i18n.t("api.requestFailed")} (${response.status}): ${text.slice(0, 200)}` : `${i18n.t("api.requestFailed")}: ${response.statusText}`,
    );
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    const text = await response.text();
    if (/^\s*</.test(text)) {
      throw new Error(
        i18n.t("api.htmlInsteadOfJson"),
      );
    }
    throw new Error(`${i18n.t("api.nonJsonResponse")}: ${text.slice(0, 120)}`);
  }
  return response.json() as Promise<T>;
}
