import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./cookies", () => ({
  getCookie: vi.fn(() => "test-csrf-token"),
}));

import { login, logout, requestPasswordReset, signup } from "./auth";

describe("auth call-sites", () => {
  const originalEnv = process.env.NEXT_PUBLIC_API_URL;

  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000/api/v1";
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_URL = originalEnv;
    vi.unstubAllGlobals();
  });

  it("signup posts to /auth/signup with email and password", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      json: async () => ({ status: 401, meta: { is_authenticated: false } }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await signup("new@example.com", "correct-horse-battery-staple");

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/v1/auth/signup");
    expect(JSON.parse(options.body)).toEqual({
      email: "new@example.com",
      password: "correct-horse-battery-staple",
    });
    expect(result.meta?.isAuthenticated).toBe(false);
  });

  it("login posts to /auth/login and surfaces MFA-required flows", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      json: async () => ({
        status: 401,
        data: { flows: [{ id: "mfa_authenticate" }] },
        meta: { is_authenticated: false },
      }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await login("user@example.com", "correct-horse-battery-staple");

    expect(result.data?.flows?.[0].id).toBe("mfa_authenticate");
  });

  it("logout sends DELETE to /auth/session", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      json: async () => ({ status: 401, meta: { is_authenticated: false } }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await logout();

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/v1/auth/session");
    expect(options.method).toBe("DELETE");
  });

  it("requestPasswordReset always returns the same shape regardless of caller-visible content", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      json: async () => ({ status: 200, data: {} }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await requestPasswordReset("anyone@example.com");

    expect(result.status).toBe(200);
  });
});
