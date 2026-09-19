import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { divIcon } from 'leaflet'
import type { Copy, Lang, Place } from '../lib/data'
import 'leaflet/dist/leaflet.css'

const icon = divIcon({
  html: '<span class="map-pin"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 3v5a3 3 0 0 0 6 0V3M7 3v19M20 22V3c-4 2-5 6-5 10h5"/></svg></span>',
  className: 'custom-map-marker', iconSize: [40, 48], iconAnchor: [20, 44], popupAnchor: [0, -40],
})

export default function ParisMap({ places, lang, t, onSelect }: { places: Place[]; lang: Lang; t: Copy; onSelect: (place: Place) => void }) {
  return <div className="map-layout">
    <div className="map-sidebar">
      {places.map(place => <button key={place.id} className="map-place" onClick={() => onSelect(place)}>
        <img src={place.image} alt="" />
        <span><strong>{place.name}</strong><small>{lang === 'en' ? place.area : place.areaFr}</small><b>{place.price ? '€1' : t.free}</b></span>
        <span aria-hidden="true">↗</span>
      </button>)}
      <p className="map-explainer">{t.mapNote}</p>
    </div>
    <MapContainer center={[48.849, 2.342]} zoom={13} className="paris-map" scrollWheelZoom={false}>
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {places.filter(place => place.coordinates).map(place => <Marker key={place.id} position={place.coordinates!} icon={icon}>
        <Popup><strong>{place.name}</strong><p>{lang === 'en' ? place.area : place.areaFr}</p><button className="popup-button" onClick={() => onSelect(place)}>{t.details} →</button></Popup>
      </Marker>)}
    </MapContainer>
  </div>
}
