/** 搜索后端：local（默认，浏览器本地）| api | auto */

export type SearchBackendMode = "local" | "api" | "auto";

export function getSearchBackendMode(): SearchBackendMode {
  const raw = (import.meta.env.VITE_SEARCH_BACKEND as string | undefined)?.trim().toLowerCase();
  if (raw === "api") return "api";
  if (raw === "auto") return "auto";
  return "local";
}

/** @deprecated 使用 getSearchBackendMode */
export function getSearchBackend(): SearchBackendMode {
  return getSearchBackendMode();
}
