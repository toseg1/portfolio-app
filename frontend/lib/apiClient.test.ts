import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./cookies", () => ({
  getCookie: vi.fn(() => "test-csrf-token"),
}));

import { apiFetch, camelizeKeys } from "./apiClient";

describe("camelizeKeys", () => {
  it("converts nested snake_case keys to camelCase", () => {
    const input = { is_authenticated: true, data: { market_value_base: "123.45" } };
    expect(camelizeKeys(input)).toEqual({
      isAuthenticated: true,
      data: { marketValueBase: "123.45" },
    });
  });

  it("leaves money-shaped strings untouched — only keys are converted", () => {
    const input = { market_value_base: "1234.5600" };
    const result = camelizeKeys<{ marketValueBase: string }>(input);
    expect(result.marketValueBase).toBe("1234.5600");
    expect(typeof result.marketValueBase).toBe("string");
  });

  it("converts keys inside arrays", () => {
    const input = [{ user_id: 1 }, { user_id: 2 }];
    expect(camelizeKeys(input)).toEqual([{ userId: 1 }, { userId: 2 }]);
  });
});

describe("apiFetch", () => {
  const originalEnv = process.env.NEXT_PUBLIC_API_URL;

  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000/api/v1";
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_URL = originalEnv;
    vi.unstubAllGlobals();
  });

  it("attaches X-CSRFToken and credentials on a mutating request", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      json: async () => ({ status: 200, meta: { is_authenticated: true } }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await apiFetch("/auth/login", { method: "POST", body: { email: "a@b.com" } });

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/v1/auth/login");
    expect(options.credentials).toBe("include");
    expect(options.headers.get("X-CSRFToken")).toBe("test-csrf-token");
    expect(options.body).toBe(JSON.stringify({ email: "a@b.com" }));
  });

  it("does not attach X-CSRFToken on a GET request", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      json: async () => ({ status: 200 }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await apiFetch("/auth/session");

    const [, options] = mockFetch.mock.calls[0];
    expect(options.headers.get("X-CSRFToken")).toBeNull();
  });

  it("camelizes the response envelope", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      json: async () => ({
        status: 200,
        data: { user: { email: "a@b.com" } },
        meta: { is_authenticated: true },
      }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await apiFetch("/auth/session");

    expect(result.meta).toEqual({ isAuthenticated: true });
  });
});
