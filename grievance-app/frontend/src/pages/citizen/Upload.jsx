import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadIssue } from '../../api/client';
import { useSession } from '../../context/SessionContext';

export default function Upload() {
  const navigate = useNavigate();
  const { t } = useSession();
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [description, setDescription] = useState('');
  const [deviceCoords, setDeviceCoords] = useState({ lat: 28.6139, lng: 77.2090 });
  const [geoStatus, setGeoStatus] = useState('detecting'); // 'detecting' | 'detected' | 'fallback'
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setDeviceCoords({
            lat: Number(pos.coords.latitude.toFixed(6)),
            lng: Number(pos.coords.longitude.toFixed(6)),
          });
          setGeoStatus('detected');
        },
        () => {
          // Fallback to default Central Delhi location
          setDeviceCoords({ lat: 28.6139, lng: 77.2090 });
          setGeoStatus('fallback');
        },
        { enableHighAccuracy: true, timeout: 6000 }
      );
    } else {
      setGeoStatus('fallback');
    }
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError(t('selectPhotoError'));
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('device_lat', deviceCoords.lat);
      formData.append('device_lng', deviceCoords.lng);

      if (description.trim()) {
        formData.append('description', description.trim());
      }

      const res = await uploadIssue(formData);
      navigate(`/confirm/${res.image_id}`);
    } catch (err) {
      setError(err.message || 'Upload failed. Please try again.');
      setSubmitting(false);
    }
  };

  return (
    <div className="container-narrow" style={{ marginTop: 'var(--spacing-lg)' }}>
      <div className="card">
        {/* Step indicator */}
        <div style={{ display: 'flex', gap: '6px', marginBottom: 'var(--spacing-md)' }}>
          <div style={{ flex: 1, height: '4px', borderRadius: '2px', backgroundColor: 'var(--color-green)' }} />
          <div style={{ flex: 1, height: '4px', borderRadius: '2px', backgroundColor: 'var(--color-orange)' }} />
          <div style={{ flex: 1, height: '4px', borderRadius: '2px', backgroundColor: 'var(--color-border)' }} />
          <div style={{ flex: 1, height: '4px', borderRadius: '2px', backgroundColor: 'var(--color-border)' }} />
        </div>

        <div style={{ marginBottom: 'var(--spacing-md)' }}>
          <span className="badge badge-blue">{t('step2of4')}</span>
          <h1 style={{ marginTop: 'var(--spacing-xs)', marginBottom: '4px' }}>{t('reportAnIssue')}</h1>
        </div>

        {error && <div className="notice notice-warning">{error}</div>}

        <form onSubmit={handleSubmit}>
          <input
            type="file"
            accept="image/*"
            capture="environment"
            ref={fileInputRef}
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />

          <div
            onClick={() => fileInputRef.current && fileInputRef.current.click()}
            style={{
              border: '2px dashed var(--color-border)',
              borderRadius: 'var(--radius)',
              minHeight: '180px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'var(--color-bg)',
              cursor: 'pointer',
              marginBottom: 'var(--spacing-md)',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Selected issue"
                style={{ width: '100%', height: '180px', objectFit: 'cover' }}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: 'var(--spacing-md)' }}>
                <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📷</div>
                <div style={{ fontWeight: 600, color: 'var(--color-text)' }}>{t('tapToCapture')}</div>
              </div>
            )}
          </div>

          {previewUrl && (
            <button
              type="button"
              className="btn btn-secondary btn-sm btn-block"
              style={{ marginBottom: 'var(--spacing-md)' }}
              onClick={() => fileInputRef.current && fileInputRef.current.click()}
            >
              {t('chooseDifferentPhoto')}
            </button>
          )}

          {/* Location Geotag Status */}
          <div
            style={{
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius)',
              padding: '12px 14px',
              backgroundColor: 'var(--color-bg)',
              marginBottom: 'var(--spacing-md)',
              fontSize: '0.85rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>📍</span>
                <span>{t('municipalLocationGeotag')}</span>
              </div>
              <span
                className={`badge ${
                  geoStatus === 'detected'
                    ? 'badge-green'
                    : geoStatus === 'detecting'
                    ? 'badge-blue'
                    : 'badge-muted'
                }`}
                style={{ fontSize: '0.75rem', padding: '2px 8px' }}
              >
                {geoStatus === 'detected'
                  ? t('gpsCaptured')
                  : geoStatus === 'detecting'
                  ? t('detectingGps')
                  : t('municipalWardPin')}
              </span>
            </div>

            <div className="text-muted" style={{ fontSize: '0.8rem', marginBottom: '8px' }}>
              {t('coordinates')}: <strong>{deviceCoords.lat}° N, {deviceCoords.lng}° E</strong>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="desc">{t('describeIssueOptional')}</label>
            <textarea
              id="desc"
              className="form-textarea"
              placeholder={t('describePlaceholder')}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={submitting || !selectedFile}
          >
            {submitting ? t('uploadingPhoto') : t('continueToConfirmation')}
          </button>
        </form>
      </div>
    </div>
  );
}

