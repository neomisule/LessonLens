import type { ApiError } from "@/lib/types/api";

const BASE_URL = `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1`;

class ApiClientError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
    public readonly code?: string
  ) {
    super(detail);
    this.name = "ApiClientError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;

  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });

  if (!res.ok) {
    let errorBody: ApiError = { detail: "An unexpected error occurred" };
    try {
      errorBody = await res.json();
    } catch {}
    throw new ApiClientError(res.status, errorBody.detail, errorBody.code);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, init?: Omit<RequestInit, "method" | "body">) =>
    request<T>(path, { ...init, method: "GET" }),

  post: <T>(path: string, body: unknown, init?: Omit<RequestInit, "method">) =>
    request<T>(path, { ...init, method: "POST", body: JSON.stringify(body) }),

  patch: <T>(path: string, body: unknown, init?: Omit<RequestInit, "method">) =>
    request<T>(path, { ...init, method: "PATCH", body: JSON.stringify(body) }),

  delete: <T = void>(path: string, init?: Omit<RequestInit, "method" | "body">) =>
    request<T>(path, { ...init, method: "DELETE" }),
};

export { ApiClientError };
