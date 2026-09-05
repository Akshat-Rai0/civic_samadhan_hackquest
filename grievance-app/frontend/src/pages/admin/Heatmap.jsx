import React, { useEffect, useState, useRef } from 'react';
import { getHeatmapData } from '../../api/client';

export default function Heatmap() {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef(new Map());
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Helper to determine marker color driven by hotspot_tier
  const getMarkerColor = (hotspotTier) => {
    switch ((hotspotTier || '').toLowerCase()) {
      case 'high':
        return '#E53935'; // Red — top band of priority_score
      case 'medium':
        return '#F2994A'; // Theme orange — mid band
      case 'low':
        return '#5C7080'; // Blue-gray — lower band (green reserved for resolved)
      default:
        return '#2F80ED'; // Default theme blue for standard single reports
    }
  };

  // Helper to build popup HTML
  const buildPopupHtml = (pt) => {
    const tier = pt.hotspot_tier ? pt.hotspot_tier.toUpperCase() : 'STANDARD';
    let tierBadgeColor = '#2F80ED';
    if (tier === 'HIGH') tierBadgeColor = '#E53935';
    else if (tier === 'MEDIUM') tierBadgeColor = '#F2994A';
    else if (tier === 'LOW') tierBadgeColor = '#5C7080';

    return `
      <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 13px; line-height: 1.4; min-width: 180px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <strong style="font-family: monospace; font-size: 14px;">${pt.ticket_id || 'Issue'}</strong>
          <span style="background: ${tierBadgeColor}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;">
            ${tier}
          </span>
        </div>
        <div><strong>Category:</strong> <span style="text-transform: capitalize;">${pt.category || 'Civic defect'}</span></div>
        <div><strong>Department:</strong> ${pt.department_name || 'Unassigned'}</div>
        <div><strong>Postal Code:</strong> ${pt.postal_code || 'Central'}</div>
        <div><strong>Affected Reports:</strong> ${pt.affected_count || 1}</div>
        <div><strong>Priority Score:</strong> ${pt.priority_score || 0}</div>
      </div>
    `;
  };

  const loadData = async () => {
    try {
      const data = await getHeatmapData();
      setPoints(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load heatmap coordinate data.');
    } finally {
      setLoading(false);
    }
  };

  // Initial load + periodic polling for live updates without page reload
  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 5000);
    return () => clearInterval(timer);
  }, []);

  // Leaflet map initialization
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    if (window.L) {
      initLeafletMap();
    } else {
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

      // Render initial points
      syncMarkers(points);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Synchronize and update markers in-place when points data changes
  const syncMarkers = (currentPoints) => {
    const map = mapInstanceRef.current;
    if (!map || !window.L) return;

    const activeIds = new Set();

    currentPoints.forEach((pt) => {
      const key = pt.id || pt.ticket_id;
      if (!key || pt.lat === null || pt.lng === null) return;
      activeIds.add(key);

      const score = pt.priority_score || 50;
      // Density sizing stays raw per existing v1 spec
      const radius = Math.max(12, Math.min(28, score / 3.5));
      // Color driven by hotspot_tier
      const color = getMarkerColor(pt.hotspot_tier);

      if (markersRef.current.has(key)) {
        // Update existing marker in-place: update popup with department, coords, style
        const marker = markersRef.current.get(key);
        marker.setLatLng([pt.lat, pt.lng]);
        marker.setStyle({
          radius: radius,
          fillColor: color,
          color: color,
        });
        marker.setPopupContent(buildPopupHtml(pt));
      } else {
        // Create new marker once
        const circle = window.L.circleMarker([pt.lat, pt.lng], {
          radius: radius,
          fillColor: color,
          color: color,
          weight: 2,
          opacity: 0.9,
          fillOpacity: 0.55,
        }).addTo(map);

        circle.bindPopup(buildPopupHtml(pt));
        markersRef.current.set(key, circle);
      }
    });

    // Remove obsolete markers that are no longer in points
    markersRef.current.forEach((marker, key) => {
      if (!activeIds.has(key)) {
        map.removeLayer(marker);
        markersRef.current.delete(key);
      }
    });
  };

  useEffect(() => {
    if (mapInstanceRef.current && points.length > 0) {
      syncMarkers(points);
    }
  }, [points]);

  return (
    <div className="container" style={{ marginTop: 'var(--spacing-md)' }}>
      <div className="mb-md">
        <h1>Complaint Density Heatmap</h1>
        <p className="text-muted" style={{ margin: 0 }}>
          Spatial distribution of open civic issues with dynamic hotspot tiering and real GPS coordinates.
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
            padding: '12px 16px',
            borderRadius: 'var(--radius)',
            border: '1px solid var(--color-border)',
            boxShadow: 'var(--shadow-sm)',
            fontSize: '0.8rem',
            backdropFilter: 'blur(4px)',
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: '8px', color: 'var(--color-text)' }}>
            Hotspot Tiers & Density
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#E53935' }} />
            <span><strong>Hotspot High</strong> (Top priority percentile)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#F2994A' }} />
            <span><strong>Hotspot Medium</strong> (Mid priority percentile)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#5C7080' }} />
            <span><strong>Hotspot Low</strong> (Lower priority percentile)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#2F80ED' }} />
            <span><strong>Standard</strong> (&lt; 2 reports in area)</span>
          </div>
        </div>
      </div>

      <p className="text-muted" style={{ fontSize: '0.85rem', marginTop: 'var(--spacing-md)' }}>
        Note: Marker size shows raw complaint density. Marker color reflects dynamic hotspot tiering updated live. Green is strictly reserved for resolved issues.
      </p>
    </div>
  );
}
