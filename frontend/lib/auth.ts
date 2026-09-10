import { apiFetch, type ApiEnvelope } from "./apiClient";

export interface AuthUser {
  email: string;
}

export interface AuthFlow {
  id: string;
}

export interface AuthMeta {
  isAuthenticated: boolean;
}

export interface AuthData {
  user?: AuthUser;
  flows?: AuthFlow[];
}

export type AuthResponse = ApiEnvelope<AuthData>;

export function signup(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthData>("/auth/signup", {
    method: "POST",
    body: { email, password },
  });
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthData>("/auth/login", {
    method: "POST",
    body: { email, password },
  });
}

export function logout(): Promise<AuthResponse> {
  return apiFetch<AuthData>("/auth/session", { method: "DELETE" });
}

export function getSession(): Promise<AuthResponse> {
  return apiFetch<AuthData>("/auth/session", { method: "GET" });
}

export function requestPasswordReset(email: string): Promise<ApiEnvelope> {
  return apiFetch("/auth/password/request", {
    method: "POST",
    body: { email },
  });
}

export function resetPassword(key: string, password: string): Promise<ApiEnvelope> {
  return apiFetch("/auth/password/reset", {
    method: "POST",
    body: { key, password },
  });
}

export function confirmTotpLogin(code: string): Promise<AuthResponse> {
  return apiFetch<AuthData>("/auth/2fa/authenticate", {
    method: "POST",
    body: { code },
  });
}

export interface TotpSecret {
  secret: string;
  totpUrl: string;
}

export function getTotpSecret(): Promise<ApiEnvelope<unknown> & { meta?: TotpSecret }> {
  return apiFetch("/account/authenticators/totp", { method: "GET" }) as Promise<
    ApiEnvelope<unknown> & { meta?: TotpSecret }
  >;
}

export function activateTotp(code: string): Promise<ApiEnvelope> {
  return apiFetch("/account/authenticators/totp", {
    method: "POST",
    body: { code },
  });
}
