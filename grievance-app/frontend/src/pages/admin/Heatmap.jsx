import React, { useEffect, useState, useRef } from 'react';
import { getHeatmapData } from '../../api/client';

export default function Heatmap() {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getHeatmapData();
        setPoints(data);
      } catch (err) {
        setError(err.message || 'Failed to load heatmap coordinate data.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  useEffect(() => {
    if (loading || !mapContainerRef.current || mapInstanceRef.current) return;

    // Dynamically initialize Leaflet map
    if (window.L) {
      initLeafletMap();
    } else {
      // Inject Leaflet CSS & JS if not already on page
      const cssLink = document.createElement('link');
      cssLink.rel = 'stylesheet';
      cssLink.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      document.head.appendChild(cssLink);

      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.onload = () => {
        initLeafletMap();
      };
      document.head.appendChild(script);
    }

    function initLeafletMap() {
      if (!mapContainerRef.current || mapInstanceRef.current) return;

      const map = window.L.map(mapContainerRef.current).setView([28.6139, 77.2090], 12);
      mapInstanceRef.current = map;

      window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18,
      }).addTo(map);

      // Render points as circles with color reflecting priority score
      points.forEach((pt) => {
        const score = pt.priority_score || 50;
        let color = '#2F80ED'; // Blue for low
        if (score >= 70) {
          color = '#D4722A'; // Red-orange for high
        } else if (score >= 40) {
          color = '#F2994A'; // Orange for medium
        }

        const radius = Math.max(12, Math.min(28, score / 3.5));

        const circle = window.L.circleMarker([pt.lat, pt.lng], {
          radius: radius,
          fillColor: color,
          color: color,
          weight: 1,
          opacity: 0.8,
          fillOpacity: 0.5,
        }).addTo(map);

        circle.bindPopup(`
          <div style="font-family: sans-serif; font-size: 13px;">
            <strong>${pt.ticket_id || 'Issue'}</strong><br/>
            Category: ${pt.category || 'Civic defect'}<br/>
            Priority score: ${score}<br/>
            Affected reports: ${pt.affected_count || 1}
          </div>
        `);
      });
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [loading, points]);

  return (
    <div className="container" style={{ marginTop: 'var(--spacing-md)' }}>
      <div className="mb-md">
        <h1>Complaint Density Heatmap</h1>
        <p className="text-muted" style={{ margin: 0 }}>
          Spatial distribution of open civic issues across administrative zones.
        </p>
      </div>

      {error && <div className="notice notice-warning">{error}</div>}

      <div
        className="card"
        style={{
          padding: 0,
          overflow: 'hidden',
          position: 'relative',
          border: '1px solid var(--color-border)',
        }}
      >
        <div
          ref={mapContainerRef}
          style={{
            width: '100%',
            height: '520px',
            backgroundColor: '#e5e3df',
          }}
        />

        {/* Legend */}
        <div
          style={{
            position: 'absolute',
            bottom: '16px',
            left: '16px',
            zIndex: 1000,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            padding: '10px 14px',
            borderRadius: 'var(--radius)',
            border: '1px solid var(--color-border)',
            boxShadow: 'var(--shadow-sm)',
            fontSize: '0.8rem',
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: '6px' }}>Density & Priority</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#D4722A' }} />
            <span>High priority / dense (score ≥ 70)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#F2994A' }} />
            <span>Medium priority (score 40–69)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#2F80ED' }} />
            <span>Standard priority (score &lt; 40)</span>
          </div>
        </div>
      </div>

      <p className="text-muted" style={{ fontSize: '0.85rem', marginTop: 'var(--spacing-md)' }}>
        Note: Version 1 shows raw complaint density. Normalization by ward population will be introduced in future updates.
      </p>
    </div>
  );
}
