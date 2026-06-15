/** 搜索后端：auto（默认，小 catalog 走浏览器）| api | local */

export type SearchBackendMode = "auto" | "api" | "local";

/** 浏览器本地搜索允许的最大组合数（auto 模式）。 */
export const LOCAL_SEARCH_MAX_COMBINATIONS = 5000;

export function getSearchBackendMode(): SearchBackendMode {
  const raw = (import.meta.env.VITE_SEARCH_BACKEND as string | undefined)?.trim().toLowerCase();
  if (raw === "local" || raw === "api") return raw;
  return "auto";
}

/** @deprecated 使用 getSearchBackendMode */
export function getSearchBackend(): SearchBackendMode {
  return getSearchBackendMode();
}
