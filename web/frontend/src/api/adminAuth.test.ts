import { afterEach, describe, expect, it, vi } from "vitest";
import { adminHeaders, getAdminToken, setAdminToken } from "./adminAuth";

describe("adminAuth", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("stores the token only in session storage and injects the header", () => {
    const values = new Map<string, string>();
    vi.stubGlobal("sessionStorage", {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
    });

    setAdminToken("secret-token");

    expect(getAdminToken()).toBe("secret-token");
    expect(adminHeaders({ "Content-Type": "application/json" })).toEqual({
      "Content-Type": "application/json",
      "X-Admin-Token": "secret-token",
    });

    setAdminToken("");
    expect(adminHeaders()).toEqual({});
  });
});
