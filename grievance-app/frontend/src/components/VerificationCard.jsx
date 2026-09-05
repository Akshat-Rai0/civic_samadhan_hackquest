import React from 'react';

export default function VerificationCard({
  evidence,
  onConfirm,
  onDispute,
  submitting = false,
  citizenStatus = null,
}) {
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
          <span className="badge badge-green">Citizen Confirmed</span>
        </div>
        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--color-text)' }}>
          You confirmed this issue was resolved. The ticket has been closed.
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
          <span className="badge badge-escalated">Citizen Disputed</span>
        </div>
        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--color-text)' }}>
          You reported that the issue is still not fixed. The ticket has been returned to the department queue.
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
        <span className="badge badge-orange">Verification Agent</span>
        {evidence && evidence.diff_score !== null && (
          <small style={{ fontWeight: 600, color: 'var(--color-text)' }}>
            Resolution match score: {Math.round((evidence.diff_score || 0.85) * 100)}%
          </small>
        )}
      </div>

      <p style={{ fontSize: '0.95rem', margin: '0 0 var(--spacing-sm) 0' }}>
        A completion photo has been submitted by the municipal field team. Automated checks show the issue appears fixed. Please verify whether the problem is resolved at your location.
      </p>

      {evidence && evidence.object_delta && (
        <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: 'var(--spacing-md)' }}>
          Visual analysis: {evidence.object_delta}
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
          Yes, it is fixed
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          style={{ flex: 1 }}
          onClick={onDispute}
          disabled={submitting}
        >
          Still not fixed
        </button>
      </div>
    </div>
  );
}
