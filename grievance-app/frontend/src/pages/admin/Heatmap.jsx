import React, { useEffect, useState, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import { getHeatmapData } from '../../api/client';

export default function Heatmap() {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const heatLayerRef = useRef(null);
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  // Leaflet map initialization. The initial viewport is only a city default;
  // it is not a complaint record or fallback data point.
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;
    const map = L.map(mapContainerRef.current).setView([28.6139, 77.2090], 12);
    mapInstanceRef.current = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 18,
    }).addTo(map);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
      heatLayerRef.current = null;
    };
  }, []);

  // Each open cluster contributes its real affected-report count as heat weight.
  // Priority does not influence either the position or intensity of the heatmap.
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || typeof L.heatLayer !== 'function') return;

    const validPoints = points.filter(
      (point) => Number.isFinite(point.lat) && Number.isFinite(point.lng)
    );
    const maxAffectedCount = Math.max(
      1,
      ...validPoints.map((point) => Math.max(1, Number(point.affected_count) || 1))
    );
    const heatPoints = validPoints.map((point) => [
      point.lat,
      point.lng,
      Math.max(1, Number(point.affected_count) || 1) / maxAffectedCount,
    ]);

    if (heatLayerRef.current) {
      heatLayerRef.current.setLatLngs(heatPoints);
    } else {
      heatLayerRef.current = L.heatLayer(heatPoints, {
        radius: 32,
        blur: 24,
        minOpacity: 0.25,
        gradient: { 0.25: '#2F80ED', 0.5: '#F2994A', 0.75: '#E53935', 1: '#A82424' },
      }).addTo(map);
    }

    if (validPoints.length > 0) {
      map.fitBounds(L.latLngBounds(validPoints.map((point) => [point.lat, point.lng])), {
        padding: [32, 32],
        maxZoom: 15,
      });
    }
  }, [points]);

  return (
    <div className="container" style={{ marginTop: 'var(--spacing-md)' }}>
      <div className="mb-md">
        <h1>Complaint Density Heatmap</h1>
        <p className="text-muted" style={{ margin: 0 }}>
          Raw density of open civic reports, weighted only by the number of citizen reports in each cluster.
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

        {loading || points.length === 0 ? (
          <div
            className="notice notice-info"
            style={{ position: 'absolute', top: '16px', left: '16px', zIndex: 1000, margin: 0 }}
          >
            {loading
              ? 'Loading reported issue locations…'
              : 'No open reports with valid location data are available yet.'}
          </div>
        ) : null}

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
            Raw report density
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#E53935' }} />
            <span><strong>High</strong> (more citizen reports nearby)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#F2994A' }} />
            <span><strong>Medium</strong> (moderate report concentration)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#2F80ED' }} />
            <span><strong>Low</strong> (fewer nearby reports)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#2F80ED' }} />
            <span><strong>Coverage</strong> (an open report cluster)</span>
          </div>
        </div>
      </div>

      <p className="text-muted" style={{ fontSize: '0.85rem', marginTop: 'var(--spacing-md)' }}>
        Note: Heat intensity is derived from affected-report counts only. Priority score, category, and hotspot tier do not affect the visualization.
      </p>
    </div>
  );
}
