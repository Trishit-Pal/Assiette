import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/ticket.css";

import { getHealth } from "./api";
import { counterBar, currentPath } from "./components/counterBar";
import { getLang, t } from "./i18n";
import { aboutPage } from "./pages/about";
import { homePage } from "./pages/home";
import { signinPage } from "./pages/signin";
import { applyTheme, getTheme } from "./theme";

let apiOk = false;

function page(): HTMLElement {
  const path = currentPath();
  if (path === "/about") return aboutPage();
  if (path === "/signin") return signinPage(render);
  return homePage(render);
}

function render(): void {
  const root = document.getElementById("app");
  if (!root) return;
  root.replaceChildren(counterBar(apiOk), page());
  const skip = document.querySelector(".skip-link");
  if (skip) skip.textContent = t("skip");
}

function paintStatus(): void {
  const chip = document.querySelector(".status-chip");
  if (!chip) return;
  chip.className = `status-chip ${apiOk ? "live" : "offline"}`;
  chip.textContent = apiOk ? t("live") : t("offline");
}

async function ping(): Promise<void> {
  try {
    const h = await getHealth();
    apiOk = h.status === "ok";
  } catch {
    apiOk = false;
  }
  paintStatus();
}

applyTheme(getTheme());
document.documentElement.lang = getLang();
render();
void ping();

window.addEventListener("popstate", render);
window.addEventListener("assiette:route", render);
window.addEventListener("assiette:lang", render);
window.addEventListener("assiette:auth", render);
