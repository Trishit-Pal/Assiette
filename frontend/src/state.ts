import type { ComposerState, Meal } from "./types";

const AUTH_KEY = "assiette-auth";

export type AuthState = { token: string; email: string } | null;

export function getAuth(): AuthState {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AuthState;
    if (parsed && parsed.token && parsed.email) return parsed;
  } catch {
    /* ignore */
  }
  return null;
}

export function setAuth(auth: AuthState): void {
  if (auth) localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
  else localStorage.removeItem(AUTH_KEY);
  window.dispatchEvent(new Event("assiette:auth"));
}

export function mealFromClock(now = new Date()): Meal {
  const hour = now.getHours();
  if (hour < 11) return "breakfast";
  if (hour < 15) return "lunch";
  return "dinner";
}

export const DEMO_QUERY = "I live in the 13th, €3 budget, dinner after 18:00";

export const defaultComposer = (): ComposerState => ({
  queryText: DEMO_QUERY,
  arrondissement: 13,
  budget: 3.3,
  meal: "dinner",
  diet: "any",
  bursary: false,
  category: "any",
});
