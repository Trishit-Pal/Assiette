export type Meal = "breakfast" | "lunch" | "dinner" | "any";
export type Diet = "any" | "vegetarian" | "vegan" | "halal";
export type Category = "any" | "crous" | "distribution";
export type Freshness = "fresh" | "stale" | "refused";
export type SourceMode = "live" | "cache" | "stale" | "snapshot";

export type QueryRequest = {
  query: string;
  arrondissement?: number | null;
  budget_eur?: number | null;
  meal?: Meal;
  diet?: Diet;
  bursary?: boolean;
  category?: Category;
  use_network?: boolean;
  refresh?: boolean;
};

export type ItineraryStop = {
  id: string;
  why: string;
  dietary_note: string;
  french_phrases: string[];
};

export type RankedPlace = {
  id: string;
  source: string;
  name: string;
  org: string;
  kind: string;
  address: string;
  arrondissement: number | null;
  latitude: number | null;
  longitude: number | null;
  price_eur: number;
  open_for_request: boolean;
  schedule_text: string;
  eligibility: string;
  menu_text: string;
  booking_required: boolean;
  last_verified: string;
  source_url: string;
  french_hint: string;
  notes: string;
  score: number;
  reasons: string[];
  freshness_status: string;
  match?: MatchRecord;
};

export type MatchRecord = {
  arrondissement: "exact" | "nearby" | "unscoped";
  budget: "ok" | "unscoped";
  meal: "open" | "closed";
  diet: "match" | "not_confirmed" | "not_applicable";
};

export type EmptyReason = {
  reason: "filters_too_strict" | "no_data";
  blocking_chips: Array<"budget" | "arrondissement">;
  suggestion: "relax_budget" | "relax_arrondissement" | "relax_both" | null;
  counts: Record<string, number>;
};

export type SourceMeta = {
  name: string;
  fetched_at: string | null;
  mode: SourceMode;
};

export type QueryResponse = {
  summary: string;
  stops: ItineraryStop[];
  caveats: string[];
  engine: string;
  intent: Record<string, unknown>;
  places: RankedPlace[];
  meta: Record<string, unknown>;
  refreshed_at: string | null;
  offline_mode: boolean;
  data_version?: string;
  generated_at?: string | null;
  sources?: SourceMeta[];
  empty_reason?: EmptyReason | null;
};

export type RetrieveResponse = {
  places: RankedPlace[];
  meta: Record<string, unknown>;
  intent: Record<string, unknown>;
  data_version: string;
  generated_at: string | null;
  sources: SourceMeta[];
  refreshed_at: string | null;
  offline_mode: boolean;
  empty_reason?: EmptyReason | null;
};

export type ComposeResponse = {
  summary: string;
  stops: ItineraryStop[];
  caveats: string[];
  engine: string;
  meta: Record<string, unknown>;
  data_version: string;
  generated_at: string | null;
};

export type HealthResponse = {
  status: string;
  database: string;
  venue_count: number;
  last_refresh: string | null;
};

export type AuthRequestOut = {
  message: string;
  dev_token?: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  email: string;
};

export type RefreshRun = {
  id: number;
  source: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  diff_summary: Record<string, unknown>;
};

export type ScrapeHealth = {
  source: string;
  rows?: number;
  suspect: boolean;
  fetched_at?: string | null;
};

export type RefreshRunsOut = {
  runs: RefreshRun[];
  pending_candidates: number;
  scrape_health: ScrapeHealth[];
};

export type ComposerState = {
  queryText: string;
  arrondissement: number | null;
  budget: number | null;
  meal: Meal;
  diet: Diet;
  bursary: boolean;
  category: Category;
};
