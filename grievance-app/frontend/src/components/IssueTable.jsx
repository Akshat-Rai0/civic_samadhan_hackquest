import React from 'react';
import PriorityBadge from './PriorityBadge';
import EscalationBadge from './EscalationBadge';

export default function IssueTable({ issues = [], onRowClick }) {
  if (!issues || issues.length === 0) {
    return (
      <div className="card empty-state">
        <p>No issues found in this queue.</p>
      </div>
    );
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'submitted':
      case 'in_review':
        return <span className="badge badge-blue">{status.replace('_', ' ')}</span>;
      case 'assigned':
      case 'in_progress':
        return <span className="badge badge-orange">{status.replace('_', ' ')}</span>;
      case 'pending_confirmation':
        return <span className="badge badge-orange">verification pending</span>;
      case 'resolved':
      case 'closed':
        return <span className="badge badge-green">resolved</span>;
      default:
        return <span className="badge badge-muted">{status}</span>;
    }
  };

  return (
    <div className="table-wrap card" style={{ padding: 0 }}>
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          textAlign: 'left',
          fontSize: '0.9rem',
        }}
      >
        <thead>
          <tr
            style={{
              backgroundColor: 'var(--color-bg)',
              borderBottom: '1px solid var(--color-border)',
              color: 'var(--color-heading)',
              fontSize: '0.8rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            <th style={{ padding: '14px 16px' }}>Priority</th>
            <th style={{ padding: '14px 16px' }}>Ticket</th>
            <th style={{ padding: '14px 16px' }}>Category</th>
            <th style={{ padding: '14px 16px' }}>Location</th>
            <th style={{ padding: '14px 16px' }}>Affected</th>
            <th style={{ padding: '14px 16px' }}>Status</th>
            <th style={{ padding: '14px 16px' }}>Escalation</th>
            <th style={{ padding: '14px 16px' }}>Officer</th>
          </tr>
        </thead>
        <tbody>
          {issues.map((issue) => (
            <tr
              key={issue.id}
              onClick={() => onRowClick && onRowClick(issue.id)}
              style={{
                borderBottom: '1px solid var(--color-border)',
                cursor: onRowClick ? 'pointer' : 'default',
                transition: 'background-color 0.1s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--color-bg)')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
            >
              <td style={{ padding: '14px 16px' }}>
                <PriorityBadge score={issue.priority_score} />
              </td>
              <td style={{ padding: '14px 16px', fontWeight: 600 }}>
                {issue.ticket_id || `GR-${issue.id}`}
              </td>
              <td style={{ padding: '14px 16px', textTransform: 'capitalize' }}>
                {issue.category}
              </td>
              <td style={{ padding: '14px 16px', color: 'var(--color-muted)' }}>
                {issue.zone ? `${issue.zone}, ${issue.postal_code}` : 'Ward Central'}
              </td>
              <td style={{ padding: '14px 16px' }}>
                <span
                  style={{
                    backgroundColor: 'var(--color-bg)',
                    border: '1px solid var(--color-border)',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontWeight: 600,
                  }}
                >
                  {issue.affected_count || 1}
                </span>
              </td>
              <td style={{ padding: '14px 16px' }}>
                {getStatusBadge(issue.status)}
              </td>
              <td style={{ padding: '14px 16px' }}>
                <EscalationBadge
                  daysPending={issue.days_pending || 0}
                  tier={issue.escalation_tier || 0}
                  escalationInfo={issue.escalation_info}
                />
              </td>
              <td style={{ padding: '14px 16px', color: 'var(--color-text)' }}>
                {issue.officer_name || 'Unassigned'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
