import React, { useState, useEffect, useCallback } from 'react';
import {
  getContractorEmailStatus,
  approveContractorEmail,
  sendContractorEmail,
} from '../api/client';

export default function ContractorEmailCard({ clusterId }) {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await getContractorEmailStatus(clusterId);
      setEmails(data);
      setError(null);
    } catch (err) {
      // No drafts yet — not an error state
      setEmails([]);
    } finally {
      setLoading(false);
    }
  }, [clusterId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleApprove = async (draftId) => {
    setActionLoading(true);
    setError(null);
    setNotice(null);
    try {
      await approveContractorEmail(draftId, 1);
      setNotice('Email draft approved. You may now send it.');
      await fetchStatus();
    } catch (err) {
      setError(err.message || 'Error approving email draft.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSend = async (draftId) => {
    setActionLoading(true);
    setError(null);
    setNotice(null);
    try {
      await sendContractorEmail(draftId);
      setNotice('Email sent successfully to the assigned officer.');
      await fetchStatus();
    } catch (err) {
      setError(err.message || 'Error sending email. Make sure the draft is approved first.');
    } finally {
      setActionLoading(false);
    }
  };

  // Don't render anything if no emails exist yet
  if (loading) {
    return (
      <div className="card">
        <h2>Contractor Email Notification</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 0' }}>
          <div className="spinner" />
          <span className="text-muted">Loading email status...</span>
        </div>
      </div>
    );
  }



  const statusBadgeClass = (status) => {
    switch (status) {
      case 'sent':
        return 'badge badge-green';
      case 'approved':
        return 'badge badge-blue';
      case 'error':
        return 'badge badge-red';
      default:
        return 'badge';
    }
  };

  return (
    <div className="card">
      <h2>Contractor Email Notification</h2>
      <p className="text-muted" style={{ fontSize: '0.85rem' }}>
        Email notifications drafted by the Contractor Email Agent for assigned officers.
        Emails require admin approval before sending.
      </p>

      {notice && <div className="notice notice-success">{notice}</div>}
      {error && <div className="notice notice-warning">{error}</div>}

      {emails.length === 0 ? (
        <p className="text-muted" style={{ margin: '12px 0 0 0', fontSize: '0.85rem' }}>
          No contractor email drafts generated yet. Assign or reassign an officer using the sidebar to trigger automated email drafting.
        </p>
      ) : (
        <div className="flex flex-col gap-sm" style={{ marginTop: '12px' }}>

        {emails.map((email) => (
          <div
            key={email.id}
            style={{
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius)',
              padding: '14px',
              backgroundColor: 'var(--color-bg)',
            }}
          >
            {/* Header row */}
            <div className="flex items-center justify-between mb-xs">
              <span className={statusBadgeClass(email.status)}>
                {email.status.toUpperCase()}
              </span>
              <small className="text-muted">
                {email.created_at
                  ? new Date(email.created_at).toLocaleString()
                  : '—'}
              </small>
            </div>

            {/* Recipient */}
            <div style={{ fontSize: '0.85rem', marginBottom: '4px' }}>
              <strong>To:</strong> {email.recipient_email || '—'}
            </div>

            {/* Subject */}
            <div style={{ fontSize: '0.85rem', marginBottom: '8px' }}>
              <strong>Subject:</strong> {email.subject}
            </div>

            {/* Collapsible body */}
            <details style={{ marginBottom: '10px' }}>
              <summary
                style={{
                  cursor: 'pointer',
                  fontSize: '0.8rem',
                  color: 'var(--color-muted)',
                  fontWeight: 600,
                }}
              >
                View email body
              </summary>
              <pre
                style={{
                  whiteSpace: 'pre-wrap',
                  fontSize: '0.8rem',
                  backgroundColor: '#FFFFFF',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius)',
                  padding: '10px',
                  marginTop: '6px',
                  maxHeight: '240px',
                  overflowY: 'auto',
                }}
              >
                {email.body}
              </pre>
            </details>

            {/* Sent timestamp */}
            {email.sent_at && (
              <div
                style={{
                  fontSize: '0.8rem',
                  color: 'var(--color-muted)',
                  marginBottom: '8px',
                }}
              >
                Sent at: {new Date(email.sent_at).toLocaleString()}
              </div>
            )}

            {/* Approval info */}
            {email.approved_by_admin_id && (
              <div
                style={{
                  fontSize: '0.8rem',
                  color: 'var(--color-muted)',
                  marginBottom: '8px',
                }}
              >
                Approved by Admin #{email.approved_by_admin_id}
              </div>
            )}

            {/* Action buttons — only show for non-sent drafts */}
            {email.status !== 'sent' && (
              <div className="flex gap-sm" style={{ marginTop: '8px' }}>
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={() => handleApprove(email.draft_id)}
                  disabled={
                    actionLoading ||
                    email.status === 'approved'
                  }
                >
                  {email.status === 'approved' ? '✓ Approved' : 'Approve'}
                </button>

                <button
                  type="button"
                  className="btn btn-success btn-sm"
                  onClick={() => handleSend(email.draft_id)}
                  disabled={
                    actionLoading ||
                    email.status !== 'approved'
                  }
                  title={
                    email.status !== 'approved'
                      ? 'Approve the draft before sending'
                      : 'Send email to assigned officer'
                  }
                >
                  Send Email
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
      )}
    </div>
  );
}

