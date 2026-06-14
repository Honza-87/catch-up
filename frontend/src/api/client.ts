// Thin typed fetch client. All API calls go through /api (Vite proxy → backend)
// and include the session cookie. Errors normalize to { code, message }.

export class ApiClientError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function parseError(resp: Response): Promise<ApiClientError> {
  let code = "error";
  let message = resp.statusText;
  try {
    const body = await resp.json();
    if (body?.error) {
      code = body.error.code ?? code;
      message = body.error.message ?? message;
    }
  } catch {
    // non-JSON error body; keep defaults
  }
  return new ApiClientError(code, message, resp.status);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`/api${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!resp.ok) throw await parseError(resp);
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  // multipart upload: do NOT set Content-Type (browser sets the boundary).
  postForm: <T>(path: string, form: FormData) =>
    request<T>(path, { method: "POST", body: form, headers: {} }),
};
