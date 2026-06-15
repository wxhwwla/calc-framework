/** 搜索后端：auto（默认，wasm+local 时走浏览器）| api | local */

export type SearchBackendMode = "auto" | "api" | "local";

export function getSearchBackendMode(): SearchBackendMode {
  const raw = (import.meta.env.VITE_SEARCH_BACKEND as string | undefined)?.trim().toLowerCase();
  if (raw === "local" || raw === "api") return raw;
  return "auto";
}

/** @deprecated 使用 getSearchBackendMode */
export function getSearchBackend(): SearchBackendMode {
  return getSearchBackendMode();
}
