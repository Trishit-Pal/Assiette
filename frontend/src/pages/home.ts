import { getRetrieve, postCompose } from "../api";
import { composer } from "../components/composer";
import { emptyState, errorState, idleState, loadingState } from "../components/states";
import { pairStops, ticketCard } from "../components/ticketCard";
import { el } from "../dom";
import { patchAgeLabel, startFreshness, type FreshnessHandle } from "../freshness";
import { t, type CopyKey } from "../i18n";
import { defaultComposer } from "../state";
import type { ComposerState, QueryRequest, QueryResponse, RankedPlace, RetrieveResponse } from "../types";

const composerState: ComposerState = defaultComposer();

type View =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "data"; data: QueryResponse; composing?: boolean };

type MapApi = typeof import("../components/resultMap");

let view: View = { kind: "idle" };
let lastPayload: QueryRequest | null = null;
let freshness: FreshnessHandle | null = null;
let mapApi: MapApi | null = null;
let mapGen = 0;

function syntheticQuery(state: ComposerState): string {
  const area = state.arrondissement ? String(state.arrondissement) : "paris";
  const kind = state.category === "any" ? "food" : state.category;
  return `${state.meal} ${area} ${kind}`;
}

function payloadFrom(state: ComposerState): QueryRequest {
  const payload: QueryRequest = {
    query: state.queryText.trim() || syntheticQuery(state),
    meal: state.meal,
    diet: state.diet,
    category: state.category,
    bursary: state.bursary,
    use_network: true,
  };
  if (state.arrondissement) payload.arrondissement = state.arrondissement;
  if (state.budget !== null) payload.budget_eur = state.budget;
  return payload;
}

function intentLabel(intent: Record<string, unknown>, key: string, fallback: string): string {
  const v = intent[key];
  if (v === null || v === undefined || v === "") return fallback;
  return String(v);
}

function ageText(iso: string | null | undefined): string {
  if (!iso) return "?";
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return iso;
  const mins = Math.max(0, Math.round((Date.now() - then) / 60000));
  if (mins < 1) return t("ageJustNow");
  return `${mins} ${t("ageMinutes")}`;
}

function hasCoords(place: RankedPlace): boolean {
  return Number.isFinite(place.latitude) && Number.isFinite(place.longitude);
}

function dropMap(): void {
  mapGen += 1;
  mapApi?.unmount();
  mapApi = null;
}

function attachMap(container: HTMLElement, places: RankedPlace[]): void {
  const gen = mapGen;
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      void import("../components/resultMap").then((mod) => {
        if (gen !== mapGen || !container.isConnected) return;
        mapApi = mod;
        mod.mount(container, places);
      });
    });
  });
}

function placeIds(places: RankedPlace[]): string {
  return places.map((p) => p.id).join("|");
}

function paintCopy(target: HTMLElement, data: QueryResponse, composing: boolean): void {
  const intent = data.intent || {};
  const arr = intent.arrondissement ? `${intent.arrondissement}e` : t("paris");
  const budget = typeof intent.budget_eur === "number" ? `€${intent.budget_eur}` : t("openBudget");
  const mealKey = String(intent.meal || "lunch");
  const meal = (["breakfast", "lunch", "dinner", "any"] as const).includes(mealKey as "lunch")
    ? t(mealKey as CopyKey)
    : mealKey;
  target.replaceChildren(
    el(
      "div",
      { class: "meta-row" },
      el("span", {}, `${t("area")}: ${arr}`),
      el("span", {}, `${t("budget")}: ${budget}`),
      el("span", {}, `${t("slot")}: ${meal}`),
      el("span", {}, `${t("engine")}: ${data.engine}`),
      el("span", { class: "freshness-age" }, `${t("lastRefresh")}: ${ageText(data.generated_at || data.refreshed_at)}`),
    ),
  );
  if (data.offline_mode) target.append(el("p", { class: "banner" }, t("snapshotBanner")));
  if (data.meta && data.meta.arrondissement_relaxed_to_nearby) {
    target.append(el("p", { class: "caveat" }, t("nearbyBanner")));
  }
  if (data.summary) target.append(el("p", {}, data.summary));
  else if (composing) target.append(el("p", { class: "caveat" }, t("composing")));
  const meta = data.meta || {};
  target.append(
    el(
      "p",
      { class: "caveat provenance" },
      `CROUS: ${intentLabel(meta, "crous_status", "?")} · ${t("lastRefresh")}: ${data.refreshed_at ?? meta.distributions_compiled ?? "?"}`,
    ),
  );
  for (const c of data.caveats || []) target.append(el("p", { class: "caveat" }, c));
}

function paintTickets(stack: HTMLElement, data: QueryResponse): void {
  const intent = data.intent || {};
  const mealKey = String(intent.meal || "lunch");
  const meal = (["breakfast", "lunch", "dinner"] as const).includes(mealKey as "lunch") ? t(mealKey as CopyKey) : mealKey;
  const diet = String(intent.diet || "any");
  const paired = pairStops(data.places || [], data.stops || []);
  stack.replaceChildren();
  paired.forEach(([place, stop], i) =>
    stack.append(
      ticketCard(place, stop, i + 1, data.sources, {
        meal,
        diet: diet === "any" ? "" : diet,
        onFocusPlace: (id) => mapApi?.panTo(id),
      }),
    ),
  );
}

type ResultsShell = {
  section: HTMLElement;
  copy: HTMLElement;
  skip: HTMLAnchorElement;
  mapEl: HTMLElement;
  stack: HTMLElement;
};

function ensureShell(host: HTMLElement): ResultsShell {
  const existing = host.querySelector(".results") as HTMLElement | null;
  if (existing) {
    return {
      section: existing,
      copy: existing.querySelector("#results-copy") as HTMLElement,
      skip: existing.querySelector(".skip-map") as HTMLAnchorElement,
      mapEl: existing.querySelector("#result-map") as HTMLElement,
      stack: existing.querySelector("#ticket-stack") as HTMLElement,
    };
  }
  const copy = el("div", { id: "results-copy" });
  const skip = el("a", { class: "skip-map", href: "#ticket-stack" }, t("skipMap")) as HTMLAnchorElement;
  const mapEl = el("div", {
    id: "result-map",
    class: "result-map",
    role: "region",
    "aria-label": t("mapRegion"),
  });
  const stack = el("div", { id: "ticket-stack", class: "ticket-stack" });
  const section = el(
    "section",
    {
      class: "results",
      "aria-live": "polite",
      "aria-label": t("resultsHeading"),
      tabindex: "-1",
    },
    copy,
    skip,
    mapEl,
    stack,
  );
  host.replaceChildren(section);
  return { section, copy, skip, mapEl, stack };
}

function paintData(host: HTMLElement, data: QueryResponse, composing: boolean, focus: boolean): void {
  const places = data.places || [];
  if (!places.length) {
    dropMap();
    const wrap = el("section", {
      class: "results",
      "aria-live": "polite",
      "aria-label": t("resultsHeading"),
      tabindex: "-1",
    });
    wrap.append(
      emptyState(data.empty_reason, (chip) => {
        if (chip === "budget") void runFromPatch({ budget: null });
        else void runFromPatch({ arrondissement: null });
      }),
    );
    host.replaceChildren(wrap);
    if (focus) wrap.focus();
    return;
  }
  const shell = ensureShell(host);
  paintCopy(shell.copy, data, composing);
  paintTickets(shell.stack, data);
  const mappable = places.some(hasCoords);
  shell.skip.hidden = !mappable;
  shell.mapEl.hidden = !mappable;
  if (mappable) attachMap(shell.mapEl, places);
  else dropMap();
  if (focus) shell.section.focus();
}

let runFromPatch: (patch?: Partial<ComposerState>) => Promise<void> = async () => undefined;
let refreshBound = false;

function paintResults(host: HTMLElement, rerun: (patch?: Partial<ComposerState>) => void, focus = false): void {
  if (view.kind === "idle") {
    dropMap();
    host.replaceChildren(idleState());
    return;
  }
  if (view.kind === "loading") {
    dropMap();
    host.replaceChildren(loadingState());
    return;
  }
  if (view.kind === "error") {
    dropMap();
    host.replaceChildren(errorState(view.message, () => void rerun()));
    return;
  }
  paintData(host, view.data, Boolean(view.composing), focus);
}

function mergeRetrieve(data: RetrieveResponse): QueryResponse {
  return {
    summary: "",
    stops: [],
    caveats: [],
    engine: "retrieving",
    intent: data.intent || {},
    places: data.places || [],
    meta: data.meta || {},
    refreshed_at: data.refreshed_at,
    offline_mode: data.offline_mode,
    data_version: data.data_version,
    generated_at: data.generated_at,
    sources: data.sources,
    empty_reason: data.empty_reason,
  };
}

export function homePage(_onNeedRender: () => void): HTMLElement {
  dropMap();
  const host = el("div", { id: "results" });

  const run = async (patch?: Partial<ComposerState>, live = true) => {
    if (patch) Object.assign(composerState, patch);
    const payload = payloadFrom(composerState);
    lastPayload = payload;
    const previous = view;
    view = { kind: "loading" };
    paintResults(host, run);
    try {
      const retrieved = await getRetrieve(payload, live ? undefined : freshness?.lastEtag(), { refresh: live });
      if (retrieved.notModified && previous.kind === "data") {
        view = previous;
        freshness?.markFetched(retrieved.etag);
        patchAgeLabel(`${t("lastRefresh")}: ${t("ageJustNow")}`);
        return;
      }
      if (!retrieved.data) throw new Error(t("errorTitle"));
      freshness?.markFetched(retrieved.etag);
      const partial = mergeRetrieve(retrieved.data);
      view = { kind: "data", data: partial, composing: true };
      paintResults(host, run, true);
      if (!retrieved.data.places.length) {
        view = { kind: "data", data: partial };
      } else {
        const composed = await postCompose({
          query: payload.query,
          intent: retrieved.data.intent,
          place_ids: retrieved.data.places.map((p) => p.id),
          data_version: retrieved.data.data_version,
          use_network: payload.use_network,
        });
        view = {
          kind: "data",
          data: {
            ...partial,
            summary: composed.summary,
            stops: composed.stops,
            caveats: composed.caveats,
            engine: composed.engine,
            meta: { ...partial.meta, ...composed.meta },
            generated_at: composed.generated_at,
          },
        };
      }
    } catch (err) {
      view = { kind: "error", message: err instanceof Error ? err.message : t("errorTitle") };
    }
    paintResults(host, run, false);
  };
  runFromPatch = (patch) => run(patch, true);
  if (!refreshBound) {
    refreshBound = true;
    window.addEventListener("assiette:refresh", () => {
      void runFromPatch();
    });
  }

  if (!freshness) {
    freshness = startFreshness(() => {
      if (!lastPayload || document.hidden) return;
      void (async () => {
        try {
          const retrieved = await getRetrieve(lastPayload!, freshness?.lastEtag());
          freshness?.markFetched(retrieved.etag);
          if (retrieved.notModified) {
            patchAgeLabel(`${t("lastRefresh")}: ${t("ageJustNow")}`);
            return;
          }
          if (retrieved.data && view.kind === "data") {
            const prev = placeIds(view.data.places);
            const next = placeIds(retrieved.data.places);
            view = {
              kind: "data",
              data: {
                ...view.data,
                places: retrieved.data.places,
                sources: retrieved.data.sources,
                data_version: retrieved.data.data_version,
                empty_reason: retrieved.data.empty_reason,
              },
            };
            patchAgeLabel(`${t("lastRefresh")}: ${t("ageJustNow")}`);
            if (next !== prev) paintResults(host, run, false);
            else if (next) mapApi?.sync(retrieved.data.places);
          }
        } catch {
          /* ignore background revalidation */
        }
      })();
    });
  }

  const main = el("main", { id: "main", "aria-label": t("brand") });
  main.append(
    el(
      "section",
      { class: "hero", "aria-labelledby": "hero-title" },
      el(
        "div",
        { class: "hero-copy" },
        el("p", { class: "hero-kicker" }, t("heroKicker")),
        el("h1", { id: "hero-title" }, t("heroLine1"), el("br"), el("span", {}, t("heroLine2"))),
        el("p", { class: "hero-intro" }, t("heroIntro")),
        el("p", {}, t("heroLead")),
      ),
      el(
        "div",
        { class: "hero-art", "aria-hidden": "true" },
        el("div", { class: "hero-leaf" }),
        el("div", { class: "css-plate" }),
        el("div", { class: "hero-tomato" }),
        el(
          "div",
          { class: "price-ticket" },
          el("div", { class: "from" }, t("priceFrom")),
          el("div", { class: "amt" }, "1", el("small", {}, "€")),
          el("div", { class: "sub" }, t("priceSub")),
        ),
      ),
    ),
    el(
      "section",
      { class: "trust-strip", "aria-label": t("trustLabel") },
      el("div", {}, el("strong", {}, t("trustOfficial")), el("span", {}, t("trustOfficialSub"))),
      el("div", {}, el("strong", {}, t("trustBudget")), el("span", {}, t("trustBudgetSub"))),
      el("div", {}, el("strong", {}, t("trustCommunity")), el("span", {}, t("trustCommunitySub"))),
    ),
    el(
      "section",
      { class: "ask", "aria-labelledby": "ask-title" },
      el("h2", { id: "ask-title" }, t("askHeading")),
      el("p", { class: "ask-lead" }, t("askLead")),
      composer(composerState, () => void run(), view.kind === "loading"),
    ),
    host,
  );
  paintResults(host, run);
  return main;
}
