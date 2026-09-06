import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { trackIssue, confirmResolution } from '../../api/client';
import { useSession } from '../../context/SessionContext';
import StatusStepper from '../../components/StatusStepper';
import AgentUpdateLog from '../../components/AgentUpdateLog';
import VerificationCard from '../../components/VerificationCard';

export default function Track() {
  const { clusterId } = useParams();
  const { t } = useSession();

  const [issueData, setIssueData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submittingVerification, setSubmittingVerification] = useState(false);

  const fetchIssue = async () => {
    try {
      const data = await trackIssue(clusterId);
      setIssueData(data);
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Unable to load ticket details.');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssue();
    const interval = setInterval(fetchIssue, 15000);
    return () => clearInterval(interval);
  }, [clusterId]);

  const handleConfirmResolution = async (status) => {
    setSubmittingVerification(true);
    try {
      await confirmResolution(clusterId, status);
      await fetchIssue();
    } catch (err) {
      alert(err.message || 'Error updating confirmation status.');
    } finally {
      setSubmittingVerification(false);
    }
  };

  if (loading) {
    return (
      <div className="container-narrow loading-center">
        <div className="spinner spinner-lg" />
        <p>{t('loadingTicket')}</p>
      </div>
    );
  }

  if (error || !issueData) {
    return (
      <div className="container-narrow" style={{ marginTop: 'var(--spacing-xl)' }}>
        <div className="card text-center">
          <h2>{t('ticketNotFound')}</h2>
          <p className="text-muted">{error || t('ticketNotFoundDesc')}</p>
          <Link to="/upload" className="btn btn-primary" style={{ marginTop: 'var(--spacing-md)' }}>
            {t('reportAnotherIssue')}
          </Link>
        </div>
      </div>
    );
  }

  const otherCount = Math.max(0, (issueData.affected_count || 1) - 1);

  return (
    <div className="container-narrow" style={{ marginTop: 'var(--spacing-md)' }}>
      {/* Top Header */}
      <div className="card" style={{ marginBottom: 'var(--spacing-md)' }}>
        <div className="flex items-center justify-between mb-xs">
          <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '1.1rem' }}>
            {issueData.ticket_id}
          </span>
          <span className="badge badge-blue">{issueData.department_name}</span>
        </div>

        <h2 style={{ textTransform: 'capitalize', marginBottom: '4px' }}>
          {issueData.category} Issue
        </h2>
        <p className="text-muted" style={{ fontSize: '0.85rem', margin: 0 }}>
          {t('location')}: {issueData.zone || 'Central Ward'} (PIN: {issueData.postal_code || '110001'})
        </p>

        {otherCount > 0 && (
          <div
            className="notice notice-info"
            style={{ marginTop: 'var(--spacing-sm)', marginBottom: 0 }}
          >
            {otherCount} {t('otherCitizensReported')} {issueData.affected_count}.
          </div>
        )}
      </div>

      {/* Status Stepper */}
      <div className="card" style={{ marginBottom: 'var(--spacing-md)' }}>
        <h3 style={{ fontSize: '1rem', marginBottom: 'var(--spacing-xs)' }}>{t('progressStatus')}</h3>
        <StatusStepper currentStatus={issueData.status} />
      </div>

      {/* Verification Card (when completion evidence exists or citizen confirmation pending) */}
      {(issueData.completion_evidence || issueData.status === 'pending_confirmation') && (
        <div style={{ marginBottom: 'var(--spacing-md)' }}>
          <VerificationCard
            evidence={issueData.completion_evidence}
            citizenStatus={issueData.citizen_confirmation_status}
            submitting={submittingVerification}
            onConfirm={() => handleConfirmResolution('confirmed')}
            onDispute={() => handleConfirmResolution('disputed')}
          />
        </div>
      )}

      {/* Communication Agent Updates */}
      <div style={{ marginBottom: 'var(--spacing-lg)' }}>
        <h3 style={{ fontSize: '1rem', marginBottom: 'var(--spacing-sm)' }}>{t('departmentUpdates')}</h3>
        <AgentUpdateLog updates={issueData.notifications} />
      </div>

      <div className="text-center">
        <Link to="/upload" className="btn btn-secondary">
          {t('reportAnotherIssue')}
        </Link>
      </div>
    </div>
  );
}

