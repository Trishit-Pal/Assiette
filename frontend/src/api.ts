import type {
  AuthRequestOut,
  AuthResponse,
  ComposeResponse,
  HealthResponse,
  QueryRequest,
  QueryResponse,
  RefreshRunsOut,
  RetrieveResponse,
} from "./types";

export type VenueOut = {
  id: string;
  name: string;
  source: string;
  address: string;
  arrondissement: number | null;
  last_verified_at: string | null;
  freshness_status: string;
  source_url: string;
};

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return fetch("/health").then((r) => json<HealthResponse>(r));
}

export function postQuery(payload: QueryRequest): Promise<QueryResponse> {
  return fetch("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then((r) => json<QueryResponse>(r));
}

export type RetrieveResult = { data: RetrieveResponse | null; etag: string; notModified: boolean };

export async function getRetrieve(
  payload: QueryRequest,
  etag?: string,
  opts?: { refresh?: boolean },
): Promise<RetrieveResult> {
  const params = new URLSearchParams();
  params.set("q", payload.query);
  if (payload.arrondissement) params.set("arrondissement", String(payload.arrondissement));
  if (payload.budget_eur !== undefined && payload.budget_eur !== null) params.set("budget_eur", String(payload.budget_eur));
  if (payload.meal) params.set("meal", payload.meal);
  if (payload.diet) params.set("diet", payload.diet);
  if (payload.bursary) params.set("bursary", "true");
  if (payload.category) params.set("category", payload.category);
  params.set("use_network", payload.use_network === false ? "false" : "true");
  if (opts?.refresh || payload.refresh) params.set("refresh", "true");
  const headers: Record<string, string> = {};
  if (etag && !opts?.refresh && !payload.refresh) headers["If-None-Match"] = etag;
  const res = await fetch(`/retrieve?${params.toString()}`, { headers });
  const nextTag = res.headers.get("ETag") || etag || "";
  if (res.status === 304) return { data: null, etag: nextTag, notModified: true };
  const data = await json<RetrieveResponse>(res);
  return { data, etag: nextTag, notModified: false };
}

export function postCompose(payload: {
  query: string;
  intent: Record<string, unknown>;
  place_ids: string[];
  data_version?: string;
  use_network?: boolean;
}): Promise<ComposeResponse> {
  return fetch("/compose", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then((r) => json<ComposeResponse>(r));
}

export function getRefreshRuns(): Promise<RefreshRunsOut> {
  return fetch("/refresh-runs").then((r) => json<RefreshRunsOut>(r));
}

export function getVenues(): Promise<VenueOut[]> {
  return fetch("/venues").then((r) => json<VenueOut[]>(r));
}

export function authRequest(email: string): Promise<AuthRequestOut> {
  return fetch("/auth/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  }).then((r) => json<AuthRequestOut>(r));
}

export function authVerify(token: string): Promise<AuthResponse> {
  return fetch("/auth/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  }).then((r) => json<AuthResponse>(r));
}
