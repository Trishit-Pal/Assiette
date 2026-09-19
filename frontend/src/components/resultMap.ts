import * as L from "leaflet";
import "leaflet/dist/leaflet.css";
import { t } from "../i18n";
import type { RankedPlace } from "../types";

const PARIS = L.latLngBounds(
  [48.815573, 2.224199],
  [48.902145, 2.469920],
);

let map: L.Map | null = null;
let layer: L.LayerGroup | null = null;
let observer: ResizeObserver | null = null;
let lastKey = "";
const markers = new Map<string, L.Marker>();

function hasCoords(place: RankedPlace): boolean {
  return Number.isFinite(place.latitude) && Number.isFinite(place.longitude);
}

function reducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function activateTicket(id: string): void {
  for (const node of document.querySelectorAll(".ticket.is-active")) {
    node.classList.remove("is-active");
    node.removeAttribute("aria-current");
  }
  const ticket = document.getElementById(`ticket-${id}`);
  if (!ticket) return;
  ticket.classList.add("is-active");
  ticket.setAttribute("aria-current", "true");
  ticket.scrollIntoView({ block: "start", behavior: reducedMotion() ? "auto" : "smooth" });
}

export function unmount(): void {
  observer?.disconnect();
  observer = null;
  map?.remove();
  map = null;
  layer = null;
  lastKey = "";
  markers.clear();
}

export function sync(places: RankedPlace[]): void {
  if (!map || !layer) return;
  const rows = places.map((place, i) => ({ place, n: i + 1 })).filter(({ place }) => hasCoords(place));
  const key = rows.map(({ place }) => place.id).join("|");
  layer.clearLayers();
  markers.clear();
  const latlngs: L.LatLngExpression[] = [];
  for (const { place, n } of rows) {
    const latlng: L.LatLngExpression = [place.latitude as number, place.longitude as number];
    latlngs.push(latlng);
    const label = String(n).padStart(2, "0");
    const open = place.open_for_request;
    const status = open ? t("openYes") : t("openCheck");
    const marker = L.marker(latlng, {
      icon: L.divIcon({
        className: `map-pin${open ? "" : " is-closed"}`,
        html: `<span>${label}</span>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      }),
      keyboard: true,
      title: `${label} ${place.name}`,
      alt: `${label} ${place.name} — ${status}`,
    });
    marker.on("click", () => activateTicket(place.id));
    marker.addTo(layer);
    markers.set(place.id, marker);
  }
  map.invalidateSize();
  if (key !== lastKey && latlngs.length) {
    map.fitBounds(L.latLngBounds(latlngs), { maxZoom: 15, animate: false, padding: [24, 24] });
  }
  lastKey = key;
}

export function mount(container: HTMLElement, places: RankedPlace[]): void {
  if (map && map.getContainer() === container) {
    sync(places);
    return;
  }
  unmount();
  map = L.map(container, {
    minZoom: 11,
    maxZoom: 17,
    maxBounds: PARIS,
    maxBoundsViscosity: 1,
    scrollWheelZoom: false,
    zoomAnimation: false,
    fadeAnimation: false,
    markerZoomAnimation: false,
    attributionControl: true,
  });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    keepBuffer: 1,
    updateWhenIdle: true,
    maxZoom: 17,
  }).addTo(map);
  layer = L.layerGroup().addTo(map);
  observer = new ResizeObserver(() => {
    map?.invalidateSize();
  });
  observer.observe(container);
  lastKey = "";
  sync(places);
}

export function panTo(id: string): void {
  const marker = markers.get(id);
  if (!marker || !map) return;
  map.setView(marker.getLatLng(), Math.min(Math.max(map.getZoom(), 13), 15), { animate: false });
  activateTicket(id);
}
