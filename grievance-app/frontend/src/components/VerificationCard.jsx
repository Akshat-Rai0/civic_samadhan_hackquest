import React from 'react';
import { useSession } from '../context/SessionContext';

export default function VerificationCard({
  evidence,
  onConfirm,
  onDispute,
  submitting = false,
  citizenStatus = null,
}) {
  const { t } = useSession();

  if (!evidence && !citizenStatus) {
    return null;
  }

  if (citizenStatus === 'confirmed') {
    return (
      <div
        className="card"
        style={{
          border: '1px solid var(--color-green)',
          backgroundColor: 'var(--color-green-light)',
          padding: 'var(--spacing-md)',
        }}
      >
        <div className="flex items-center gap-sm mb-xs">
          <span className="badge badge-green">{t('citizenConfirmed')}</span>
        </div>
        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--color-text)' }}>
          {t('citizenConfirmedDesc')}
        </p>
      </div>
    );
  }

  if (citizenStatus === 'disputed') {
    return (
      <div
        className="card"
        style={{
          border: '1px solid var(--color-escalated)',
          backgroundColor: '#FFF3E6',
          padding: 'var(--spacing-md)',
        }}
      >
        <div className="flex items-center gap-sm mb-xs">
          <span className="badge badge-escalated">{t('citizenDisputed')}</span>
        </div>
        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--color-text)' }}>
          {t('citizenDisputedDesc')}
        </p>
      </div>
    );
  }

  return (
    <div
      className="card"
      style={{
        border: '2px solid var(--color-orange)',
        backgroundColor: 'var(--color-orange-light)',
        padding: 'var(--spacing-md)',
      }}
    >
      <div className="flex items-center justify-between mb-sm">
        <span className="badge badge-orange">{t('verificationAgent')}</span>
        {evidence && evidence.diff_score !== null && (
          <small style={{ fontWeight: 600, color: 'var(--color-text)' }}>
            {t('resolutionMatchScore')} {Math.round((evidence.diff_score || 0.85) * 100)}%
          </small>
        )}
      </div>

      <p style={{ fontSize: '0.95rem', margin: '0 0 var(--spacing-sm) 0' }}>
        {t('completionPhotoSubmitted')}
      </p>

      {evidence && evidence.object_delta && (
        <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: 'var(--spacing-md)' }}>
          {t('visualAnalysis')} {evidence.object_delta}
        </p>
      )}

      <div className="flex gap-sm">
        <button
          type="button"
          className="btn btn-primary"
          style={{ flex: 1 }}
          onClick={onConfirm}
          disabled={submitting}
        >
          {t('yesFixed')}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          style={{ flex: 1 }}
          onClick={onDispute}
          disabled={submitting}
        >
          {t('stillNotFixed')}
        </button>
      </div>
    </div>
  );
}

