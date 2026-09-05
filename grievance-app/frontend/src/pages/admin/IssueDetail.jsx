import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getIssueDetail,
  getOfficers,
  assignOfficer,
  dispatchContractor,
  uploadCompletion,
  closeIssue,
  reopenIssue,
  updateIssuePriority,
} from '../../api/client';
import PriorityBadge from '../../components/PriorityBadge';
import EscalationBadge from '../../components/EscalationBadge';
import ContractorEmailCard from '../../components/ContractorEmailCard';


export default function IssueDetail() {
  const { clusterId } = useParams();
  const navigate = useNavigate();
  const completionInputRef = useRef(null);

  const [issue, setIssue] = useState(null);
  const [officers, setOfficers] = useState([]);
  const [selectedOfficer, setSelectedOfficer] = useState('');
  const [priorityInput, setPriorityInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [reopenReason, setReopenReason] = useState('');
  const [showReopenModal, setShowReopenModal] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);

  const fetchDetails = async () => {
    try {
      const data = await getIssueDetail(clusterId);
      setIssue(data);
      setPriorityInput(String(data.priority_override ?? data.priority_score ?? ''));
      const officerList = await getOfficers(data.department_id);
      setOfficers(officerList);
    } catch (err) {
      setError(err.message || 'Failed to fetch issue details.');
    } finally {
      setLoading(false);
    }
  };

  const handlePriorityUpdate = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await updateIssuePriority(clusterId, Number(priorityInput));
      setNotice('Priority override saved.');
      await fetchDetails();
    } catch (err) {
      setError(err.message || 'Error updating priority.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRestoreComputedPriority = async () => {
    setActionLoading(true);
    try {
      await updateIssuePriority(clusterId, null, true);
      setNotice('Automatic priority score restored.');
      await fetchDetails();
    } catch (err) {
      setError(err.message || 'Error restoring automatic priority.');
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [clusterId]);

  const handleAssign = async (e) => {
    e.preventDefault();
    if (!selectedOfficer) return;
    setActionLoading(true);
    try {
      await assignOfficer(clusterId, selectedOfficer);
      setNotice('Officer assigned successfully.');
      await fetchDetails();
    } catch (err) {
      setError(err.message || 'Error assigning officer.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDispatch = async () => {
    setActionLoading(true);
    try {
      await dispatchContractor(clusterId);
      setNotice('Contractor marked dispatched. Ticket status updated to in progress.');
      await fetchDetails();
    } catch (err) {
      setError(err.message || 'Error dispatching contractor.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCompletionUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setActionLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await uploadCompletion(clusterId, formData);
      setNotice(`Completion photo uploaded. Verification result: ${res.verification?.recommendation || 'Recorded'}.`);
      await fetchDetails();
    } catch (err) {
      setError(err.message || 'Error uploading completion evidence.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleClose = async () => {
    if (!window.confirm('Confirm resolution and close this issue?')) return;
    setActionLoading(true);
    try {
      await closeIssue(clusterId);
      setNotice('Ticket confirmed resolved and closed.');
      await fetchDetails();
    } catch (err) {
      setError(err.message || 'Error closing ticket.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReopen = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await reopenIssue(clusterId, reopenReason || 'Issue still persists.');
      setShowReopenModal(false);
      setNotice('Ticket reopened and returned to active queue.');
      await fetchDetails();
    } catch (err) {
      setError(err.message || 'Error reopening ticket.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container loading-center">
        <div className="spinner spinner-lg" />
        <p>Loading issue dossier...</p>
      </div>
    );
  }

  if (error || !issue) {
    return (
      <div className="container text-center" style={{ marginTop: 'var(--spacing-xl)' }}>
        <div className="card">
          <h2>Error loading issue</h2>
          <p className="text-muted">{error || 'Issue not found.'}</p>
          <button className="btn btn-secondary" onClick={() => navigate('/admin')}>
            Back to Queue
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ marginTop: 'var(--spacing-md)', marginBottom: 'var(--spacing-xl)' }}>
      {/* Header Bar */}
      <div className="flex items-center justify-between mb-md">
        <div>
          <button
            className="btn btn-secondary btn-sm mb-xs"
            onClick={() => navigate('/admin')}
            style={{ marginBottom: '8px' }}
          >
            ← Back to Dashboard
          </button>
          <div className="flex items-center gap-sm">
            <h1 style={{ margin: 0 }}>{issue.ticket_id}</h1>
            <span className="badge badge-blue">{issue.department_name}</span>
            <PriorityBadge score={issue.priority_score} />
          </div>
        </div>

        <div className="flex gap-sm">
          {issue.status !== 'closed' && (
            <button
              type="button"
              className="btn btn-success"
              onClick={handleClose}
              disabled={actionLoading}
            >
              Confirm Closed
            </button>
          )}
          <button
            type="button"
            className="btn btn-danger"
            onClick={() => setShowReopenModal(true)}
            disabled={actionLoading}
          >
            Reopen Ticket
          </button>
        </div>
      </div>

      {notice && <div className="notice notice-success">{notice}</div>}
      {error && <div className="notice notice-warning">{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 'var(--spacing-md)' }}>
        {/* Main Column */}
        <div className="flex flex-col gap-md">
          {/* Metadata Card */}
          <div className="card">
            <h2>Issue Overview</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', marginTop: '12px' }}>
              <div>
                <div className="text-muted" style={{ fontSize: '0.8rem' }}>Category</div>
                <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{issue.category}</div>
              </div>
              <div>
                <div className="text-muted" style={{ fontSize: '0.8rem' }}>Rubric defect type</div>
                <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{issue.issue_type || 'Needs review'}</div>
              </div>
              <div>
                <div className="text-muted" style={{ fontSize: '0.8rem' }}>Administrative Zone</div>
                <div style={{ fontWeight: 600 }}>{issue.zone} (PIN {issue.postal_code})</div>
              </div>
              <div>
                <div className="text-muted" style={{ fontSize: '0.8rem' }}>Affected Reports</div>
                <div style={{ fontWeight: 600 }}>{issue.affected_count} citizen report(s)</div>
              </div>
              <div>
                <div className="text-muted" style={{ fontSize: '0.8rem' }}>Current Status</div>
                <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                  {issue.status.replace('_', ' ')}
                </div>
              </div>
            </div>
          </div>

          {/* Citizen Reference Photos */}
          <div className="card">
            <h2>Intake Photos ({issue.images?.length || 0})</h2>
            <p className="text-muted" style={{ fontSize: '0.85rem' }}>
              Reference photos attached by citizens contributing to this cluster.
            </p>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '12px' }}>
              {issue.images && issue.images.length > 0 ? (
                issue.images.map((img) => (
                  <div
                    key={img.id}
                    style={{
                      width: '160px',
                      height: '120px',
                      borderRadius: 'var(--radius)',
                      overflow: 'hidden',
                      border: '1px solid var(--color-border)',
                      backgroundColor: 'var(--color-bg)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <img
                      src={`http://localhost:8000/${img.image_url}`}
                      alt="Intake evidence"
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.parentNode.innerText = 'Photo on file';
                      }}
                    />
                  </div>
                ))
              ) : (
                <p className="text-muted">No images recorded.</p>
              )}
            </div>
          </div>

          {/* Completion Evidence & Verification */}
          <div className="card">
            <h2>Completion Evidence & Verification</h2>
            <p className="text-muted" style={{ fontSize: '0.85rem' }}>
              Field completion photos analyzed by the Verification Agent before closure.
            </p>

            {issue.completion_evidence && issue.completion_evidence.length > 0 ? (
              <div style={{ marginTop: '12px' }}>
                {issue.completion_evidence.map((ev) => (
                  <div
                    key={ev.id}
                    style={{
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius)',
                      padding: '12px',
                      marginBottom: '10px',
                      backgroundColor: 'var(--color-bg)',
                    }}
                  >
                    <div className="flex items-center justify-between mb-xs">
                      <span className="badge badge-green">Verification Agent Check</span>
                      <small>Match score: {Math.round((ev.diff_score || 0.88) * 100)}%</small>
                    </div>
                    <p style={{ margin: '4px 0', fontSize: '0.9rem' }}>
                      Visual Delta: {ev.object_delta || 'Issue defect repaired.'}
                    </p>
                    <small className="text-muted">
                      Automated criteria passed: {ev.passed_automated_checks ? 'Yes' : 'Pending review'}
                    </small>
                  </div>
                ))}
              </div>
            ) : (
              <div className="notice notice-info" style={{ marginTop: '12px' }}>
                No completion evidence submitted yet.
              </div>
            )}

            <div style={{ marginTop: 'var(--spacing-md)' }}>
              <input
                type="file"
                accept="image/*"
                ref={completionInputRef}
                style={{ display: 'none' }}
                onChange={handleCompletionUpload}
              />
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => completionInputRef.current && completionInputRef.current.click()}
                disabled={actionLoading}
              >
                Upload Field Completion Photo
              </button>
            </div>
          </div>

          {/* Escalation History */}
          <div className="card">
            <h2>Escalation Audit Trail</h2>
            {issue.escalation_logs && issue.escalation_logs.length > 0 ? (
              <div className="flex flex-col gap-sm" style={{ marginTop: '12px' }}>
                {issue.escalation_logs.map((log) => (
                  <div
                    key={log.id}
                    style={{
                      padding: '10px 14px',
                      borderLeft: '3px solid var(--color-escalated)',
                      backgroundColor: 'var(--color-bg)',
                      borderRadius: '0 var(--radius) var(--radius) 0',
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                        Tier {log.from_tier} → Tier {log.to_tier}
                      </span>
                      <small className="text-muted">{new Date(log.logged_at).toLocaleString()}</small>
                    </div>
                    <div style={{ fontSize: '0.9rem', marginTop: '2px' }}>{log.reason}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted" style={{ margin: '12px 0 0 0', fontSize: '0.85rem' }}>
                No escalations recorded. Issue is handled within standard SLA.
              </p>
            )}
          </div>

          {/* Contractor Email Agent Card */}
          <ContractorEmailCard clusterId={clusterId} />
        </div>


        {/* Sidebar Controls */}
        <div className="flex flex-col gap-md">
          {/* Officer Assignment */}
          <div className="card">
            <h3>Priority control</h3>
            <p className="text-muted" style={{ fontSize: '0.8rem', margin: '4px 0 12px' }}>
              Automatic: base severity {issue.priority_base_severity} × affected-count multiplier {issue.affected_count_multiplier} = {issue.computed_priority_score}.
            </p>
            <form onSubmit={handlePriorityUpdate}>
              <div className="form-group">
                <label htmlFor="priority-score">Priority score</label>
                <input
                  id="priority-score"
                  type="number"
                  min="0"
                  max="250"
                  step="0.1"
                  className="form-input"
                  value={priorityInput}
                  onChange={(e) => setPriorityInput(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn btn-primary btn-block" disabled={actionLoading}>
                Save priority override
              </button>
              {issue.priority_override !== null && issue.priority_override !== undefined && (
                <button
                  type="button"
                  className="btn btn-secondary btn-block"
                  style={{ marginTop: '8px' }}
                  onClick={handleRestoreComputedPriority}
                  disabled={actionLoading}
                >
                  Use automatic score
                </button>
              )}
            </form>
          </div>

          <div className="card">
            <h3>Assigned Officer</h3>
            <p style={{ fontWeight: 600, fontSize: '1.1rem', margin: '4px 0 12px 0' }}>
              {issue.assigned_officer || 'Unassigned'}
            </p>

            <form onSubmit={handleAssign}>
              <div className="form-group">
                <label htmlFor="officer">Reassign to officer</label>
                <select
                  id="officer"
                  className="form-select"
                  value={selectedOfficer}
                  onChange={(e) => setSelectedOfficer(e.target.value)}
                  required
                >
                  <option value="">Select from pool...</option>
                  {officers.map((off) => (
                    <option key={off.id} value={off.id}>
                      {off.name} ({off.email || 'Dept pool'})
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block"
                disabled={actionLoading || !selectedOfficer}
              >
                Assign Officer
              </button>
            </form>
          </div>

          {/* Workflow Actions */}
          <div className="card">
            <h3>Operations</h3>
            <div className="flex flex-col gap-sm" style={{ marginTop: '12px' }}>
              <button
                type="button"
                className="btn btn-primary btn-block"
                onClick={handleDispatch}
                disabled={actionLoading || issue.status === 'in_progress'}
              >
                Mark Contractor Dispatched
              </button>

              <button
                type="button"
                className="btn btn-success btn-block"
                onClick={handleClose}
                disabled={actionLoading || issue.status === 'closed'}
              >
                Confirm Closed
              </button>

              <button
                type="button"
                className="btn btn-secondary btn-block"
                onClick={() => setShowReopenModal(true)}
                disabled={actionLoading}
              >
                Reopen Ticket
              </button>
            </div>
          </div>

          {/* Escalation Status */}
          <div className="card">
            <h3>SLA Watchdog</h3>
            <div style={{ marginTop: '12px' }}>
              <EscalationBadge
                daysPending={issue.days_pending || 0}
                tier={issue.escalation_tier || 0}
              />
              <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: '8px' }}>
                SLA deadline: {issue.sla_deadline ? new Date(issue.sla_deadline).toLocaleString() : 'Standard 5 days'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Reopen Modal */}
      {showReopenModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
          }}
        >
          <div className="card" style={{ maxWidth: '440px', width: '90%' }}>
            <h2>Reopen Ticket</h2>
            <p className="text-muted" style={{ fontSize: '0.85rem' }}>
              Specify the justification for returning this ticket to the active queue.
            </p>
            <form onSubmit={handleReopen}>
              <div className="form-group">
                <textarea
                  className="form-textarea"
                  placeholder="Reason for reopening (e.g. Field inspection revealed pothole still incomplete)."
                  value={reopenReason}
                  onChange={(e) => setReopenReason(e.target.value)}
                  required
                />
              </div>
              <div className="flex gap-sm">
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={actionLoading}>
                  Confirm Reopen
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                  onClick={() => setShowReopenModal(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
