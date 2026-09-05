import React from 'react';

export default function EscalationBadge({ daysPending = 0, tier = 0, escalationInfo = null }) {
  const isEscalated = tier > 0;
  const isWarning = daysPending >= 3 && !isEscalated;

  let badgeColor = 'var(--color-muted)';
  let tierText = 'Tier 1 (Within SLA)';

  if (isEscalated) {
    badgeColor = 'var(--color-escalated)';
    tierText = `Escalated to Tier ${tier + 1}`;
  } else if (isWarning) {
    badgeColor = 'var(--color-orange)';
    tierText = 'Approaching SLA';
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
      <span
        style={{
          fontSize: '0.85rem',
          fontWeight: isEscalated || isWarning ? 600 : 500,
          color: badgeColor,
        }}
      >
        {daysPending}d pending
      </span>
      <span style={{ fontSize: '0.75rem', color: 'var(--color-muted)' }}>
        {escalationInfo || tierText}
      </span>
    </div>
  );
}
