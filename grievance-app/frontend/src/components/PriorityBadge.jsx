import React from 'react';

export default function PriorityBadge({ score = 50 }) {
  const numericScore = Math.round(Number(score) || 0);

  let label = 'Low';
  let badgeClass = 'badge-muted';
  let barColor = 'var(--color-muted)';

  if (numericScore >= 70) {
    label = 'High';
    badgeClass = 'badge-escalated';
    barColor = 'var(--color-escalated)';
  } else if (numericScore >= 40) {
    label = 'Medium';
    badgeClass = 'badge-orange';
    barColor = 'var(--color-orange)';
  }

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
      <span
        style={{
          display: 'inline-block',
          width: '4px',
          height: '18px',
          borderRadius: '2px',
          backgroundColor: barColor,
        }}
      />
      <span className={`badge ${badgeClass}`}>
        {label} ({numericScore})
      </span>
    </div>
  );
}
