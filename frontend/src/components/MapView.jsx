import { useEffect, useRef } from 'react';

export default function MapView({ mapData, person }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);

  useEffect(() => {
    // Dynamically load Leaflet CSS
    if (!document.querySelector('link[href*="leaflet"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      document.head.appendChild(link);
    }

    const initMap = async () => {
      const L = await import('leaflet');

      if (mapInstance.current) {
        mapInstance.current.remove();
      }

      const center = mapData?.epicenter?.lat && mapData?.epicenter?.lng
        ? [mapData.epicenter.lat, mapData.epicenter.lng]
        : person?.epicenter_lat && person?.epicenter_lng
          ? [person.epicenter_lat, person.epicenter_lng]
          : [40.7128, -74.0060]; // Default NYC

      const map = L.map(mapRef.current).setView(center, 12);
      mapInstance.current = map;

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
      }).addTo(map);

      // Radius circle
      const radiusMiles = mapData?.radius_miles || person?.current_radius || 1;
      const radiusMeters = radiusMiles * 1609.34;
      L.circle(center, {
        radius: radiusMeters,
        color: '#00d4ff',
        fillColor: '#00d4ff',
        fillOpacity: 0.06,
        weight: 1.5,
        dashArray: '8, 4',
      }).addTo(map);

      // Epicenter marker
      const epicenterIcon = L.divIcon({
        className: '',
        html: `<div style="width:16px;height:16px;background:var(--accent-cyan);border-radius:50%;border:3px solid #0a0e1a;box-shadow:0 0 12px rgba(0,212,255,0.5);"></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      });
      L.marker(center, { icon: epicenterIcon })
        .addTo(map)
        .bindPopup(`<b>Search Epicenter</b><br/>Radius: ${radiusMiles} mi`);

      // Match pins
      const pins = mapData?.pins || [];
      pins.forEach(pin => {
        if (!pin.lat || !pin.lng) return;

        const isHigh = (pin.confidence || 0) >= 0.75;
        const pinColor = isHigh ? '#ff3366' : '#ffaa00';

        const pinIcon = L.divIcon({
          className: '',
          html: `<div style="width:12px;height:12px;background:${pinColor};border-radius:50%;border:2px solid #0a0e1a;box-shadow:0 0 8px ${pinColor}80;"></div>`,
          iconSize: [12, 12],
          iconAnchor: [6, 6],
        });

        L.marker([pin.lat, pin.lng], { icon: pinIcon })
          .addTo(map)
          .bindPopup(`
            <b>${pin.source}</b><br/>
            Confidence: ${Math.round((pin.confidence || 0) * 100)}%<br/>
            ${pin.timestamp ? `Time: ${new Date(pin.timestamp).toLocaleString()}` : ''}
          `);
      });

      // Path lines
      const path = mapData?.path || [];
      if (path.length > 1) {
        const latlngs = path.map(p => [p.lat, p.lng]);
        L.polyline(latlngs, {
          color: '#7c4dff',
          weight: 2,
          opacity: 0.7,
          dashArray: '6, 4',
        }).addTo(map);
      }
    };

    if (mapRef.current) {
      initMap();
    }

    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, [mapData, person]);

  return (
    <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h4 style={{ margin: 0 }}>Movement Map</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', margin: 0 }}>
            Radius: {mapData?.radius_miles || person?.current_radius || 1} miles · {(mapData?.pins || []).length} locations
          </p>
        </div>
        <div style={{ display: 'flex', gap: 16, fontSize: '0.7rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#00d4ff', display: 'inline-block' }} /> Epicenter
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ff3366', display: 'inline-block' }} /> High Match
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ffaa00', display: 'inline-block' }} /> Possible
          </span>
        </div>
      </div>
      <div ref={mapRef} style={{ height: 500, width: '100%' }} />
    </div>
  );
}
