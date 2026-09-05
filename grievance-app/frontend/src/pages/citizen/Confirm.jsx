import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useParams, useNavigate } from 'react-router-dom';
import { getPreview, confirmIssue } from '../../api/client';

export default function Confirm() {
  const { imageId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [error, setError] = useState(null);

  const [coords, setCoords] = useState(null);
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const pinRef = useRef(null);

  const needsManualPin = Boolean(previewData?.geotag?.prompt_manual_pin);

  useEffect(() => {
    let timer = null;

    async function fetchPreview() {
      try {
        const data = await getPreview(imageId);
        setPreviewData(data);
        if (data.geotag?.lat != null && data.geotag?.lng != null) {
          setCoords({ lat: data.geotag.lat, lng: data.geotag.lng });
        } else {
          setCoords(null);
        }
        setLoading(false);
      } catch {
        // Retry polling if still being analyzed
        timer = setTimeout(fetchPreview, 1500);
      }
    }

    fetchPreview();

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [imageId]);

  useEffect(() => {
    if (!needsManualPin || !mapContainerRef.current || mapRef.current) return;

    // This is only the initial map viewport; no coordinate is submitted until
    // the citizen deliberately clicks to place a pin.
    const map = L.map(mapContainerRef.current).setView([28.6139, 77.2090], 11);
    mapRef.current = map;
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 18,
    }).addTo(map);

    map.on('click', (event) => {
      const selectedCoords = {
        lat: Number(event.latlng.lat.toFixed(6)),
        lng: Number(event.latlng.lng.toFixed(6)),
      };
      setCoords(selectedCoords);

      if (pinRef.current) {
        pinRef.current.setLatLng(event.latlng);
      } else {
        pinRef.current = L.marker(event.latlng).addTo(map);
      }
    });

    return () => {
      map.remove();
      mapRef.current = null;
      pinRef.current = null;
    };
  }, [needsManualPin]);

  const handleConfirm = async () => {
    if (needsManualPin && !coords) {
      setError('Please drop a pin on the map before submitting your report.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const res = await confirmIssue(imageId, coords);
      navigate(`/track/${res.cluster_id}`);
    } catch (err) {
      setError(err.message || 'Failed to submit confirmation. Please try again.');
      setSubmitting(false);
    }
  };

  const handleRetake = () => {
    navigate('/upload');
  };

  return (
    <div className="container-narrow" style={{ marginTop: 'var(--spacing-lg)' }}>
      <div className="card">
        {/* Step indicator */}
        <div style={{ display: 'flex', gap: '6px', marginBottom: 'var(--spacing-md)' }}>
          <div style={{ flex: 1, height: '4px', borderRadius: '2px', backgroundColor: 'var(--color-green)' }} />
          <div style={{ flex: 1, height: '4px', borderRadius: '2px', backgroundColor: 'var(--color-green)' }} />
          <div style={{ flex: 1, height: '4px', borderRadius: '2px', backgroundColor: 'var(--color-orange)' }} />
          <div style={{ flex: 1, height: '4px', borderRadius: '2px', backgroundColor: 'var(--color-border)' }} />
        </div>

        <div style={{ marginBottom: 'var(--spacing-md)' }}>
          <span className="badge badge-blue">Step 3 of 4</span>
          <h1 style={{ marginTop: 'var(--spacing-xs)', marginBottom: '4px' }}>Confirm detected issues</h1>
          <p className="text-muted" style={{ fontSize: '0.85rem' }}>
            Automated image inspection identified the following civic problems in your upload.
          </p>
        </div>

        {error && <div className="notice notice-warning">{error}</div>}

        {loading ? (
          <div className="loading-center">
            <div className="spinner spinner-lg" />
            <p style={{ fontWeight: 500, color: 'var(--color-text)' }}>Analyzing photo with Moondream vision model...</p>
            <p className="text-muted" style={{ fontSize: '0.8rem' }}>
              Detecting civic infrastructure defects and routing to the right department.
            </p>
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: 'var(--spacing-md)' }}>
              <div className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '6px' }}>
                Detected issues:
              </div>
              <div className="flex flex-wrap gap-xs">
                {previewData && previewData.detected_issues && previewData.detected_issues.length > 0 ? (
                  previewData.detected_issues.map((issue, idx) => (
                    <span
                      key={idx}
                      className="badge badge-blue"
                      style={{ padding: '6px 12px', fontSize: '0.85rem', borderRadius: '6px' }}
                    >
                      {issue}
                    </span>
                  ))
                ) : (
                  <span className="badge badge-muted">Civic issue flagged</span>
                )}
              </div>
            </div>

            {/* Geotagged Municipal Location Card */}
            <div
              className="card"
              style={{
                backgroundColor: 'var(--color-bg)',
                padding: 'var(--spacing-md)',
                marginBottom: 'var(--spacing-md)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <div style={{ fontWeight: 600, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>📍</span>
                  <span>Geotagged Municipal Location</span>
                </div>
                <span className="badge badge-green" style={{ fontSize: '0.75rem', padding: '2px 8px' }}>
                  {previewData?.geotag?.source || 'Verified Geotag'}
                </span>
              </div>

              {needsManualPin ? (
                <>
                  <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text)', marginTop: '4px' }}>
                    Location required
                  </div>
                  <p className="text-muted" style={{ fontSize: '0.8rem', margin: '4px 0 12px' }}>
                    This photo has no usable location metadata. Drop a pin where the issue is located to continue.
                  </p>
                  <div
                    ref={mapContainerRef}
                    aria-label="Map for choosing the issue location"
                    style={{ height: '260px', borderRadius: 'var(--radius)', overflow: 'hidden', border: '1px solid var(--color-border)' }}
                  />
                  <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: '8px' }}>
                    {coords
                      ? <>Selected coordinates: <code>{coords.lat}° N, {coords.lng}° E</code></>
                      : 'Click the map to place your location pin.'}
                  </div>
                </>
              ) : (
                <>
                  <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text)', marginTop: '4px' }}>
                    {previewData?.geotag?.ward || previewData?.geotag?.zone}
                  </div>
                  <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: '2px' }}>
                    Postal PIN: <strong>{previewData?.geotag?.postal_code}</strong> • City: <strong>{previewData?.geotag?.city}</strong>
                  </div>
                  <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: '4px' }}>
                    Coordinates: <code>{coords?.lat}° N, {coords?.lng}° E</code>
                  </div>
                </>
              )}
            </div>

            <div
              className="card"
              style={{
                backgroundColor: 'var(--color-bg)',
                padding: 'var(--spacing-md)',
                marginBottom: 'var(--spacing-lg)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div className="text-muted" style={{ fontSize: '0.8rem' }}>Routing target:</div>
              <div style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--color-text)', marginTop: '2px' }}>
                {needsManualPin
                  ? 'Routing will be determined after you choose a location.'
                  : previewData?.routed_department}
              </div>
              <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: '4px' }}>
                Estimated severity level: <strong>{previewData?.severity_hint || 'Medium'}</strong>
              </div>
            </div>

            <div className="flex flex-col gap-sm">
              <button
                type="button"
                className="btn btn-primary btn-block"
                onClick={handleConfirm}
                disabled={submitting || (needsManualPin && !coords)}
              >
                {submitting ? 'Submitting to authority...' : 'Yes, send to concerned authority'}
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-block"
                onClick={handleRetake}
                disabled={submitting}
              >
                Retake photo
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
