const STORAGE_KEY = "calc-admin-token";

export function getAdminToken(): string {
  try {
    return sessionStorage.getItem(STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

export function setAdminToken(token: string): void {
  try {
    if (token) sessionStorage.setItem(STORAGE_KEY, token);
    else sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Storage may be unavailable in private browsing; requests will stay unauthenticated.
  }
}

export function adminHeaders(base: Record<string, string> = {}): Record<string, string> {
  const token = getAdminToken();
  return token ? { ...base, "X-Admin-Token": token } : base;
}
