import { getRefreshRuns } from "../api";
import { el } from "../dom";
import { t } from "../i18n";

export function aboutPage(): HTMLElement {
  const runs = el("div", { class: "runs", "aria-live": "polite" }, el("p", { class: "caveat" }, t("aboutRunsEmpty")));
  const scrape = el("div", { class: "runs" }, el("p", { class: "caveat" }, t("aboutScrapeEmpty")));
  void getRefreshRuns()
    .then((payload) => {
      const rows = payload.runs || [];
      if (rows.length) {
        const list = el("ul");
        for (const row of rows) {
          const when = (row.finished_at || row.started_at || "").slice(0, 19).replace("T", " ");
          const flag = row.diff_summary && row.diff_summary["suspect"] ? ` · ${t("aboutSuspect")}` : "";
          list.append(el("li", {}, `${when} · ${row.source} · ${row.status}${flag}`));
        }
        runs.replaceChildren(list);
      }
      const health = payload.scrape_health || [];
      const pending = payload.pending_candidates || 0;
      const bits: HTMLElement[] = [el("p", {}, `${t("aboutPending")}: ${pending}`)];
      if (health.length) {
        const list = el("ul");
        for (const row of health) {
          const suspect = row.suspect ? ` · ${t("aboutSuspect")}` : "";
          list.append(el("li", {}, `${row.source} · ${row.rows ?? "?"} rows · ${row.fetched_at || "?"}${suspect}`));
        }
        bits.push(list);
      }
      scrape.replaceChildren(...bits);
    })
    .catch(() => {
      /* keep empty copy */
    });

  const step = (n: string, titleKey: "aboutStep1" | "aboutStep2" | "aboutStep3", bodyKey: "aboutStep1Body" | "aboutStep2Body" | "aboutStep3Body") =>
    el(
      "article",
      { class: "step-card" },
      el("span", { class: "step-n" }, n),
      el("h2", {}, t(titleKey)),
      el("p", {}, t(bodyKey)),
    );

  return el(
    "main",
    { id: "main", class: "prose" },
    el("h1", {}, t("aboutTitle")),
    el("p", {}, t("aboutIntro")),
    el("div", { class: "steps-grid" }, step("01", "aboutStep1", "aboutStep1Body"), step("02", "aboutStep2", "aboutStep2Body"), step("03", "aboutStep3", "aboutStep3Body")),
    el("h2", {}, t("aboutGroundTitle")),
    el("p", {}, t("aboutGround")),
    el("h2", {}, t("aboutFreshTitle")),
    el("p", {}, t("aboutFresh")),
    el("h2", {}, t("aboutParcelsTitle")),
    el("p", {}, t("aboutParcels")),
    el("h2", {}, t("aboutNoncomTitle")),
    el("p", {}, t("aboutNoncom")),
    el("h2", {}, t("aboutMapTitle")),
    el("p", {}, t("aboutMap")),
    el("h2", {}, t("aboutRunsTitle")),
    runs,
    el("h2", {}, t("aboutScrapeTitle")),
    scrape,
  );
}
