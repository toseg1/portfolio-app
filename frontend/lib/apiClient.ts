import { getCookie } from "./cookies";

const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function toCamelCase(key: string): string {
  return key.replace(/_([a-z0-9])/g, (_match, char: string) => char.toUpperCase());
}

/**
 * Converts object/array keys snake_case -> camelCase, recursively. Values
 * pass through untouched — money-shaped strings stay strings, this only
 * ever touches keys.
 */
export function camelizeKeys<T = unknown>(value: unknown): T {
  if (Array.isArray(value)) {
    return value.map((item) => camelizeKeys(item)) as unknown as T;
  }
  if (value !== null && typeof value === "object" && !(value instanceof Date)) {
    const result: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(value as Record<string, unknown>)) {
      result[toCamelCase(key)] = camelizeKeys(val);
    }
    return result as unknown as T;
  }
  return value as T;
}

export interface ApiEnvelope<T = unknown> {
  status: number;
  data?: T;
  meta?: Record<string, unknown>;
  errors?: Array<{ code?: string; message?: string; param?: string }>;
}

export interface ApiFetchInit extends Omit<RequestInit, "body"> {
  body?: BodyInit | Record<string, unknown> | unknown[];
}

function baseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    throw new Error("NEXT_PUBLIC_API_URL is not set");
  }
  return url;
}

/**
 * The one place CSRF is handled: reads the (JS-readable, non-httpOnly)
 * csrftoken cookie Django's CSRF middleware sets and attaches it as
 * X-CSRFToken on every mutating request. Always sends credentials so the
 * httpOnly session cookie round-trips. Callers never touch fetch directly.
 */
export async function apiFetch<T = unknown>(
  path: string,
  init: ApiFetchInit = {},
): Promise<ApiEnvelope<T>> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);

  if (MUTATING_METHODS.has(method)) {
    const csrfToken = getCookie("csrftoken");
    if (csrfToken) {
      headers.set("X-CSRFToken", csrfToken);
    }
  }

  let body: BodyInit | undefined;
  if (init.body === undefined || init.body instanceof FormData || typeof init.body === "string") {
    body = init.body as BodyInit | undefined;
  } else {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(init.body);
  }

  const response = await fetch(`${baseUrl()}${path}`, {
    ...init,
    method,
    headers,
    body,
    credentials: "include",
  });

  const json = await response.json();
  return camelizeKeys<ApiEnvelope<T>>(json);
}
