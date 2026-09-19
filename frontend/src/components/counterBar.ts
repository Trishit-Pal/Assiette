import { el, icons, svgIcon } from "../dom";
import { getLang, setLang, t } from "../i18n";
import { getTheme, toggleTheme } from "../theme";

export function currentPath(): string {
  return location.pathname.replace(/\/$/, "") || "/";
}

export function navigate(path: string): void {
  history.pushState({}, "", path);
  window.dispatchEvent(new Event("assiette:route"));
}

export function counterBar(apiOk: boolean): HTMLElement {
  const lang = getLang();
  const path = currentPath();

  const logo = el(
    "a",
    { class: "counter-logo", href: "/", "aria-label": `${t("brand")} home` },
    el("span", { class: "brand-mark", "aria-hidden": "true" }, svgIcon(icons.plate)),
    el("span", {}, t("brand"), el("span", { class: "brand-period" }, ".")),
  );
  logo.addEventListener("click", (e) => {
    e.preventDefault();
    navigate("/");
  });

  const about = el("a", { class: "nav-link", href: "/about" }, t("navAbout"));
  if (path === "/about") about.setAttribute("aria-current", "page");
  about.addEventListener("click", (e) => {
    e.preventDefault();
    navigate("/about");
  });

  const refresh = el(
    "button",
    {
      class: "nav-link refresh-link",
      type: "button",
      title: t("navRefreshHint"),
    },
    svgIcon(icons.refresh),
    t("navRefresh"),
  );
  refresh.addEventListener("click", () => {
    if (currentPath() !== "/") navigate("/");
    window.dispatchEvent(new Event("assiette:refresh"));
  });

  const langBtn = el(
    "button",
    {
      class: "language-button",
      type: "button",
      "aria-label": lang === "en" ? "Switch to French" : "Passer en anglais",
    },
    el("span", { class: lang === "en" ? "active" : "" }, t("langEn")),
    el("span", { class: "language-slash" }, "/"),
    el("span", { class: lang === "fr" ? "active" : "" }, t("langFr")),
  );
  langBtn.addEventListener("click", () => setLang(lang === "en" ? "fr" : "en"));

  const sun = svgIcon(icons.sun);
  sun.classList.add("icon-sun");
  const moon = svgIcon(icons.moon);
  moon.classList.add("icon-moon");
  const themeBtn = el(
    "button",
    {
      class: "icon-btn theme-toggle",
      type: "button",
      "aria-label": getTheme() === "dark" ? t("themeLight") : t("themeDark"),
    },
    sun,
    moon,
  );
  themeBtn.addEventListener("click", () => {
    toggleTheme();
    themeBtn.setAttribute("aria-label", getTheme() === "dark" ? t("themeLight") : t("themeDark"));
  });

  const status = el(
    "span",
    { class: `status-chip ${apiOk ? "live" : "offline"}` },
    apiOk ? t("live") : t("offline"),
  );

  const paris = el("span", { class: "paris-chip" }, el("span", { "aria-hidden": "true" }), t("parisChip"));

  return el(
    "header",
    { class: "counter" },
    logo,
    el("nav", { class: "counter-nav", "aria-label": "Main" }, status, about, paris, refresh, langBtn, themeBtn),
  );
}
