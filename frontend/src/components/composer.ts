import { el } from "../dom";
import { t, type CopyKey } from "../i18n";
import type { Category, ComposerState, Diet, Meal } from "../types";

const BUDGETS: { label: string; value: number | null }[] = [
  { label: "open", value: null },
  { label: "€0", value: 0 },
  { label: "€1", value: 1 },
  { label: "€3.30", value: 3.3 },
  { label: "€8", value: 8 },
];

const MEALS: Meal[] = ["breakfast", "lunch", "dinner", "any"];
const DIETS: Diet[] = ["any", "vegetarian", "vegan", "halal"];
const CATEGORIES: { value: Category; label: CopyKey }[] = [
  { value: "any", label: "catBoth" },
  { value: "crous", label: "catCrous" },
  { value: "distribution", label: "catDist" },
];

type Preset = {
  label: CopyKey;
  arrondissement: number | null;
  meal: Meal;
  budget: number | null;
  diet?: Diet;
  category?: Category;
};

const PRESETS: Preset[] = [
  {
    label: "preset13dinner",
    arrondissement: 13,
    meal: "dinner",
    budget: 3.3,
  },
  {
    label: "presetVeg5",
    arrondissement: 5,
    meal: "lunch",
    budget: 3.3,
    diet: "vegetarian",
  },
  {
    label: "presetFree",
    arrondissement: null,
    meal: "dinner",
    budget: 0,
    category: "distribution",
  },
];

function chip(label: string, selected: boolean, onPick: (btn: HTMLButtonElement) => void): HTMLButtonElement {
  const btn = el("button", { class: "chip", type: "button", "aria-pressed": selected }, label);
  btn.addEventListener("click", () => onPick(btn));
  return btn;
}

function pressIn(row: HTMLElement, btn: HTMLButtonElement): void {
  for (const node of row.querySelectorAll("[aria-pressed]")) node.setAttribute("aria-pressed", "false");
  btn.setAttribute("aria-pressed", "true");
}

function fieldset(legend: string, row: HTMLElement): HTMLFieldSetElement {
  return el("fieldset", { class: "composer-set" }, el("legend", {}, legend), row);
}

export function composer(state: ComposerState, onSubmit: () => void, busy: boolean): HTMLElement {
  const arrChips = el("div", { class: "chip-row arr-chips", role: "group", "aria-label": t("arr") });
  arrChips.append(
    chip(t("arrAll"), state.arrondissement === null, (btn) => {
      state.arrondissement = null;
      pressIn(arrChips, btn);
    }),
  );
  const extra: HTMLButtonElement[] = [];
  for (let i = 1; i <= 20; i++) {
    const btn = chip(`${i}e`, state.arrondissement === i, (b) => {
      state.arrondissement = i;
      pressIn(arrChips, b);
    });
    if (i > 8) {
      btn.classList.add("arr-extra");
      btn.hidden = state.arrondissement !== i;
      extra.push(btn);
    }
    arrChips.append(btn);
  }
  const more = el("button", { class: "chip chip-more", type: "button", "aria-expanded": "false" }, t("moreArr"));
  more.addEventListener("click", () => {
    const open = more.getAttribute("aria-expanded") === "true";
    more.setAttribute("aria-expanded", open ? "false" : "true");
    more.textContent = open ? t("moreArr") : t("fewerArr");
    for (const btn of extra) {
      const selected = btn.getAttribute("aria-pressed") === "true";
      btn.hidden = open && !selected;
    }
  });
  arrChips.append(more);

  const catRow = el("div", { class: "chip-row", role: "group", "aria-label": t("kindOfPlace") });
  const budgetRow = el("div", { class: "chip-row", role: "group", "aria-label": t("budget") });
  const mealRow = el("div", { class: "chip-row", role: "group", "aria-label": t("meal") });
  const dietRow = el("div", { class: "chip-row", role: "group", "aria-label": t("diet") });

  const bursary = el("input", { type: "checkbox", id: "bursary" }) as HTMLInputElement;
  const bursaryRow = el("div", { class: "field field-row" }, bursary, el("label", { for: "bursary" }, t("bursary")));

  const syncBursary = (): void => {
    const distOnly = state.category === "distribution";
    if (distOnly) state.bursary = false;
    bursary.checked = state.bursary;
    bursary.disabled = distOnly;
    bursaryRow.classList.toggle("is-disabled", distOnly);
  };

  for (const c of CATEGORIES) {
    catRow.append(
      chip(t(c.label), state.category === c.value, (btn) => {
        state.category = c.value;
        pressIn(catRow, btn);
        syncBursary();
      }),
    );
  }

  for (const b of BUDGETS) {
    const label = b.value === null ? t("budgetOpen") : b.label;
    budgetRow.append(
      chip(label, state.budget === b.value, (btn) => {
        state.budget = b.value;
        pressIn(budgetRow, btn);
      }),
    );
  }

  for (const m of MEALS) {
    mealRow.append(
      chip(t(m as CopyKey), state.meal === m, (btn) => {
        state.meal = m;
        pressIn(mealRow, btn);
      }),
    );
  }

  for (const d of DIETS) {
    dietRow.append(
      chip(t(d as CopyKey), state.diet === d, (btn) => {
        state.diet = d;
        pressIn(dietRow, btn);
      }),
    );
  }

  bursary.addEventListener("change", () => {
    state.bursary = bursary.checked;
  });
  syncBursary();

  const submit = el("button", { class: "btn btn-primary", type: "submit", disabled: busy }, t("find"));

  const pressMatching = (row: HTMLElement, test: (btn: HTMLButtonElement) => boolean): void => {
    const buttons = [...row.querySelectorAll<HTMLButtonElement>(".chip:not(.chip-more)")];
    const match = buttons.find(test);
    if (match) pressIn(row, match);
  };

  const applyPreset = (preset: Preset): void => {
    state.arrondissement = preset.arrondissement;
    state.meal = preset.meal;
    state.budget = preset.budget;
    state.diet = preset.diet ?? "any";
    state.category = preset.category ?? "any";
    pressMatching(arrChips, (btn) =>
      preset.arrondissement === null ? btn.textContent === t("arrAll") : btn.textContent === `${preset.arrondissement}e`,
    );
    const arrOpen = more.getAttribute("aria-expanded") === "true";
    for (const btn of extra) {
      const selected = btn.getAttribute("aria-pressed") === "true";
      btn.hidden = !arrOpen && !selected;
    }
    pressMatching(mealRow, (btn) => btn.textContent === t(preset.meal as CopyKey));
    pressMatching(budgetRow, (btn) =>
      preset.budget === null ? btn.textContent === t("budgetOpen") : btn.textContent === BUDGETS.find((b) => b.value === preset.budget)?.label,
    );
    pressMatching(dietRow, (btn) => btn.textContent === t((preset.diet ?? "any") as CopyKey));
    pressMatching(catRow, (btn) => btn.textContent === t((CATEGORIES.find((c) => c.value === (preset.category ?? "any")) ?? CATEGORIES[0]).label));
    syncBursary();
  };

  const presets = el("div", { class: "chip-row presets" });
  for (const preset of PRESETS) {
    const btn = el("button", { class: "chip", type: "button" }, t(preset.label));
    btn.addEventListener("click", () => applyPreset(preset));
    presets.append(btn);
  }

  const form = el(
    "form",
    { class: "composer" },
    fieldset(t("arr"), arrChips),
    fieldset(t("kindOfPlace"), catRow),
    fieldset(t("meal"), mealRow),
    fieldset(t("budget"), budgetRow),
    fieldset(t("diet"), dietRow),
    el("fieldset", { class: "composer-set" }, el("legend", { class: "sr-only" }, t("bursary")), bursaryRow),
    el("div", { class: "composer-actions" }, submit),
    el("p", { class: "legend" }, t("tryPreset")),
    presets,
  );
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    onSubmit();
  });
  return form;
}
