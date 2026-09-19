import { el, icons, svgIcon } from "../dom";
import { t } from "../i18n";
import type { ItineraryStop, RankedPlace, SourceMeta } from "../types";

function fmtPrice(n: number): string {
  if (n === 0) return "0";
  return n % 1 === 0 ? String(n) : n.toFixed(2);
}

function stampLabel(place: RankedPlace): { text: string; date: string; stale: boolean } {
  const stale = place.freshness_status === "stale";
  const date = (place.last_verified || "?").slice(0, 10);
  return { text: stale ? t("checkHours") : t("verified"), date, stale };
}

async function copyText(text: string, btn: HTMLButtonElement): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = t("copied");
    setTimeout(() => {
      btn.replaceChildren(svgIcon(icons.copy));
      btn.setAttribute("aria-label", t("copy"));
    }, 1500);
  } catch {
    /* ignore */
  }
}

export function ticketCard(
  place: RankedPlace,
  stop: ItineraryStop | undefined,
  index: number,
  sources?: SourceMeta[],
  ctx?: { meal?: string; diet?: string; onFocusPlace?: (id: string) => void },
): HTMLElement {
  const stamp = stampLabel(place);
  const stampEl = el(
    "div",
    {
      class: `stamp${stamp.stale ? " stale" : ""}`,
      "aria-label": `${t("lastVerified")} ${stamp.date} (${stamp.text})`,
    },
    el("span", {}, stamp.text.toUpperCase()),
    el("time", { datetime: stamp.date }, stamp.date),
  );

  const phrases = (stop?.french_phrases?.length ? stop.french_phrases : [place.french_hint]).filter(Boolean);
  const phraseNodes = phrases.map((p) => {
    const btn = el(
      "button",
      { class: "copy-btn", type: "button", "aria-label": t("copy") },
      svgIcon(icons.copy),
    );
    btn.addEventListener("click", () => copyText(p, btn));
    return el("div", { class: "phrase" }, el("code", {}, p), btn);
  });

  const provenance =
    sources && sources.length
      ? sources.map((s) => `${s.name}: ${s.mode}${s.fetched_at ? ` ${s.fetched_at.slice(0, 16)}` : ""}`).join(" · ")
      : "";

  const body = el(
    "div",
    { class: "ticket-body" },
    stop?.why ? el("p", {}, stop.why) : null,
    el("h4", {}, t("eligibility")),
    el("p", {}, place.eligibility || "—"),
    el("h4", {}, t("dietary")),
    el("p", {}, stop?.dietary_note || place.menu_text || place.notes || "—"),
    place.source === "crous" && place.menu_text ? el("h4", {}, t("menu")) : null,
    place.source === "crous" && place.menu_text ? el("p", {}, place.menu_text) : null,
    el("h4", {}, t("say")),
    ...phraseNodes,
    provenance ? el("h4", {}, t("provenance")) : null,
    provenance ? el("p", { class: "provenance" }, provenance) : null,
    place.source_url
      ? el("p", {}, el("a", { href: place.source_url, target: "_blank", rel: "noopener noreferrer" }, t("source")))
      : null,
  );

  const summary = el("summary", {}, svgIcon(icons.chevron), t("expand"));
  const details = el("details", index === 1 ? { open: true } : {}, summary, body);

  const arr = place.arrondissement ? `${place.arrondissement}e` : "—";
  const match = place.match;
  const closed = match?.meal === "closed";
  const mealLabel = ctx?.meal || "";
  const openText = closed && mealLabel
    ? `${t("closedFor")} ${mealLabel}`
    : place.open_for_request
      ? t("openYes")
      : t("openCheck");

  const badges: HTMLElement[] = [];
  if (match?.arrondissement === "nearby") {
    badges.push(el("span", { class: "badge nearby" }, t("nearby")));
  }
  if (match && match.diet !== "not_applicable") {
    badges.push(
      el(
        "span",
        { class: match.diet === "match" ? "badge diet-ok" : "badge diet-unknown" },
        match.diet === "match" ? `${t("dietConfirmed")} ${ctx?.diet || ""}`.trim() : t("dietNotConfirmed"),
      ),
    );
  }

  const num = el(
    "button",
    {
      class: "ticket-num",
      type: "button",
      "aria-label": `${String(index).padStart(2, "0")} ${place.name}`,
    },
    String(index).padStart(2, "0"),
  );
  num.addEventListener("click", () => ctx?.onFocusPlace?.(place.id));

  const article = el(
    "article",
    {
      class: "ticket",
      id: `ticket-${place.id}`,
      role: "article",
      "aria-label": `${index}. ${place.name}`,
    },
    el("div", { class: "ticket-perf top", "aria-hidden": "true" }),
    el(
      "header",
      { class: "ticket-head" },
      num,
      el(
        "div",
        {},
        el("h3", {}, place.name),
        el(
          "p",
          { class: "ticket-org" },
          [place.org, place.address].filter(Boolean).join(" · ") +
            (place.booking_required ? ` · ${t("booking")}` : ""),
        ),
      ),
      el(
        "div",
        { class: "price-token", "aria-label": `€${fmtPrice(place.price_eur)}` },
        el("span", { class: "amt" }, `€${fmtPrice(place.price_eur)}`),
        el("span", { class: "unit" }, place.source === "crous" ? "CROUS" : place.kind || ""),
      ),
    ),
    stampEl,
    el("div", { class: "ticket-tear", "aria-hidden": "true" }),
    el(
      "dl",
      { class: "ticket-data" },
      el("div", {}, el("dt", {}, t("hours")), el("dd", {}, place.schedule_text || "—")),
      el("div", {}, el("dt", {}, t("arr")), el("dd", {}, arr)),
      el("div", {}, el("dt", {}, t("open")), el("dd", {}, openText)),
    ),
    badges.length ? el("div", { class: "ticket-badges" }, ...badges) : null,
    details,
    el("div", { class: "ticket-perf bottom", "aria-hidden": "true" }),
  );
  return article;
}

export function pairStops(places: RankedPlace[], stops: ItineraryStop[]): [RankedPlace, ItineraryStop | undefined][] {
  const byStop = new Map(stops.map((s) => [s.id, s]));
  return places
    .filter((p) => p.freshness_status !== "refused")
    .map((place) => [place, byStop.get(place.id)]);
}
