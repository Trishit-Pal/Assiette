import { el } from "../dom";
import { t } from "../i18n";
import type { EmptyReason } from "../types";

export function loadingState(): HTMLElement {
  return el(
    "div",
    { class: "ticket-stack", "aria-busy": "true", "aria-live": "polite" },
    el("p", { class: "sr-only" }, t("looking")),
    el("div", { class: "result-map is-skel", "aria-hidden": "true" }),
    el("div", { class: "ticket ticket-skel", "aria-hidden": "true" }),
    el("div", { class: "ticket ticket-skel", "aria-hidden": "true" }),
  );
}

export function idleState(): HTMLElement {
  return el(
    "div",
    { class: "idle-card", role: "status" },
    el("h2", {}, t("idleTitle")),
    el("p", {}, t("idleBody")),
  );
}

export function emptyState(
  reason: EmptyReason | null | undefined,
  onRelax: (chip: "budget" | "arrondissement") => void,
): HTMLElement {
  if (reason?.reason === "no_data") {
    return el(
      "div",
      { class: "empty", role: "status" },
      el("h2", {}, t("emptyNoDataTitle")),
      el("p", {}, t("emptyNoDataBody")),
    );
  }
  const chips = reason?.blocking_chips?.length ? reason.blocking_chips : (["budget", "arrondissement"] as const);
  const buttons = chips.map((chip) => {
    const btn = el(
      "button",
      { class: chip === chips[0] ? "btn btn-primary" : "btn", type: "button" },
      chip === "budget" ? t("relaxBudget") : t("relaxArea"),
    );
    btn.addEventListener("click", () => onRelax(chip));
    return btn;
  });
  return el(
    "div",
    { class: "empty", role: "status" },
    el("h2", {}, t("emptyTitle")),
    el("p", {}, t("emptyBody")),
    el("div", { class: "composer-actions" }, ...buttons),
  );
}

export function errorState(message: string, onRetry: () => void): HTMLElement {
  const btn = el("button", { class: "btn btn-primary", type: "button" }, t("retry"));
  btn.addEventListener("click", onRetry);
  return el(
    "div",
    { class: "error-box", role: "alert" },
    el("h2", {}, t("errorTitle")),
    el("p", {}, message),
    btn,
  );
}
