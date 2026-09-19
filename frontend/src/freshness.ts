const FLOOR_MS = 120_000;
const INTERVAL_MS = 5 * 60_000;

export type FreshnessHandle = {
  markFetched: (etag: string) => void;
  lastEtag: () => string;
  stop: () => void;
};

function jitter(ms: number): number {
  const delta = ms * 0.2;
  return ms + (Math.random() * 2 - 1) * delta;
}

export function startFreshness(revalidate: () => void): FreshnessHandle {
  let lastFetchedAt = 0;
  let etag = "";
  let timer = 0;

  const maybeRevalidate = () => {
    if (document.hidden) return;
    if (Date.now() - lastFetchedAt < FLOOR_MS) return;
    revalidate();
  };

  const armInterval = () => {
    window.clearInterval(timer);
    if (document.hidden) return;
    timer = window.setInterval(maybeRevalidate, jitter(INTERVAL_MS));
  };

  const onVis = () => {
    if (document.hidden) {
      window.clearInterval(timer);
      return;
    }
    maybeRevalidate();
    armInterval();
  };

  document.addEventListener("visibilitychange", onVis);
  armInterval();

  return {
    markFetched(next: string) {
      lastFetchedAt = Date.now();
      etag = next;
    },
    lastEtag: () => etag,
    stop() {
      document.removeEventListener("visibilitychange", onVis);
      window.clearInterval(timer);
    },
  };
}

export function patchAgeLabel(text: string): void {
  const node = document.querySelector(".freshness-age");
  if (node) node.textContent = text;
}
