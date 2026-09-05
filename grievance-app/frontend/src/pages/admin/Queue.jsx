import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getQueue } from '../../api/client';
import IssueTable from '../../components/IssueTable';

export default function Queue() {
  const navigate = useNavigate();
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [error, setError] = useState(null);

  const fetchIssues = async () => {
    setLoading(true);
    try {
      const data = await getQueue(departmentFilter || null, statusFilter || null);
      setIssues(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load issue queue.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
  }, [departmentFilter, statusFilter]);

  const handleRowClick = (issueId) => {
    navigate(`/admin/issues/${issueId}`);
  };

  return (
    <div className="container" style={{ marginTop: 'var(--spacing-md)' }}>
      <div className="flex items-center justify-between mb-md">
        <div>
          <h1>Municipal Triage Queue</h1>
          <p className="text-muted" style={{ margin: 0 }}>
            Issues clustered by location and visual similarity. Ranked by priority score.
          </p>
        </div>

        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={fetchIssues}
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh queue'}
        </button>
      </div>

      {/* Filter Bar */}
      <div
        className="card"
        style={{
          padding: 'var(--spacing-sm) var(--spacing-md)',
          marginBottom: 'var(--spacing-md)',
          display: 'flex',
          gap: 'var(--spacing-md)',
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label htmlFor="dept-select" style={{ fontSize: '0.85rem', fontWeight: 600 }}>
            Department:
          </label>
          <select
            id="dept-select"
            className="form-select"
            style={{ width: 'auto', minHeight: '36px', padding: '4px 8px' }}
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
          >
            <option value="">All Departments</option>
            <option value="1">Electrical</option>
            <option value="2">Roads and Bridges</option>
            <option value="3">Water and Sewage</option>
            <option value="4">Solid Waste Management</option>
            <option value="5">Horticulture</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label htmlFor="status-select" style={{ fontSize: '0.85rem', fontWeight: 600 }}>
            Status:
          </label>
          <select
            id="status-select"
            className="form-select"
            style={{ width: 'auto', minHeight: '36px', padding: '4px 8px' }}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Active Statuses</option>
            <option value="submitted">Submitted</option>
            <option value="in_review">In Review</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="pending_confirmation">Pending Confirmation</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
      </div>

      {error && <div className="notice notice-warning">{error}</div>}

      {loading ? (
        <div className="card loading-center">
          <div className="spinner" />
          <p>Loading queue items...</p>
        </div>
      ) : (
        <IssueTable issues={issues} onRowClick={handleRowClick} />
      )}
    </div>
  );
}
