import { el } from "../dom";
import { t } from "../i18n";
import { navigate } from "../components/counterBar";

export function signinPage(_onNeedRender: () => void): HTMLElement {
  const home = el("button", { class: "btn btn-primary", type: "button" }, t("find"));
  home.addEventListener("click", () => {
    navigate("/");
    window.dispatchEvent(new Event("assiette:refresh"));
  });
  return el(
    "main",
    { id: "main", class: "signin-page" },
    el("h1", {}, t("signinTitle")),
    el("p", {}, t("signinLead")),
    el("div", { class: "composer-actions" }, home),
  );
}
