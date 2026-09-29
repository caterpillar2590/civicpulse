import {
  ApiError,
  Category,
  ComplaintCreate,
  ComplaintListOut,
  ComplaintOut,
  FieldError,
  Priority,
  ProvidersMeta,
  Status,
  StatsOut,
} from "./types";

declare global {
  interface Window {
    __CONFIG__?: { API_BASE_URL?: string };
  }
}

// Runtime config, not import.meta.env: a Vite build bakes env values into
// static JS at build time, which would make this image environment-specific.
// Reading window.__CONFIG__ at call time keeps the image build-once,
// deploy-many. See docs/adr/0002-frontend-runtime-config.md.
function apiBase(): string {
  return window.__CONFIG__?.API_BASE_URL ?? "";
}

async function handleResponse<T>(res: Response): Promise<T> {
  const cacheHeader = res.headers.get("X-Cache");
  if (res.ok) {
    if (res.status === 204) return undefined as T;
    const data = (await res.json()) as T;
    if (cacheHeader && typeof data === "object" && data !== null) {
      (data as Record<string, unknown>).__cache = cacheHeader;
    }
    return data;
  }

  let detail = `Request failed with status ${res.status}`;
  let fieldErrors: FieldError[] = [];
  try {
    const body = await res.json();
    detail = body.detail ?? detail;
    fieldErrors = body.errors ?? [];
  } catch {
    // response had no JSON body - fall back to the generic message
  }

  const retryAfter = res.headers.get("Retry-After");
  throw new ApiError(res.status, detail, fieldErrors, retryAfter ? Number(retryAfter) : null);
}

export const api = {
  async submitComplaint(payload: ComplaintCreate): Promise<ComplaintOut> {
    const res = await fetch(`${apiBase()}/api/complaints`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse<ComplaintOut>(res);
  },

  async getComplaint(id: string): Promise<ComplaintOut> {
    const res = await fetch(`${apiBase()}/api/complaints/${id}`);
    return handleResponse<ComplaintOut>(res);
  },

  async listComplaints(params: {
    page?: number;
    page_size?: number;
    category?: Category | "";
    priority?: Priority | "";
    status?: Status | "";
  }): Promise<ComplaintListOut> {
    const qs = new URLSearchParams();
    if (params.page) qs.set("page", String(params.page));
    if (params.page_size) qs.set("page_size", String(params.page_size));
    if (params.category) qs.set("category", params.category);
    if (params.priority) qs.set("priority", params.priority);
    if (params.status) qs.set("status", params.status);

    const res = await fetch(`${apiBase()}/api/complaints?${qs.toString()}`);
    return handleResponse<ComplaintListOut>(res);
  },

  async updateStatus(id: string, status: Status): Promise<ComplaintOut> {
    const res = await fetch(`${apiBase()}/api/complaints/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    return handleResponse<ComplaintOut>(res);
  },

  async getStats(): Promise<StatsOut & { __cache?: string }> {
    const res = await fetch(`${apiBase()}/api/stats`);
    return handleResponse<StatsOut & { __cache?: string }>(res);
  },

  async getProvidersMeta(): Promise<ProvidersMeta> {
    const res = await fetch(`${apiBase()}/api/meta/providers`);
    return handleResponse<ProvidersMeta>(res);
  },
};
