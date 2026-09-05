import React from 'react';

const STEPS = [
  { key: 'submitted', label: 'Submitted' },
  { key: 'in_review', label: 'In Review' },
  { key: 'assigned', label: 'Assigned' },
  { key: 'in_progress', label: 'In Progress' },
  { key: 'pending_confirmation', label: 'Pending Confirmation' },
  { key: 'resolved', label: 'Resolved' },
];

export default function StatusStepper({ currentStatus }) {
  const normalizedStatus = currentStatus === 'closed' ? 'resolved' : currentStatus;
  const currentIndex = STEPS.findIndex((s) => s.key === normalizedStatus);
  const activeIndex = currentIndex === -1 ? 0 : currentIndex;

  return (
    <div style={{ margin: 'var(--spacing-md) 0 var(--spacing-lg) 0' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'relative',
        }}
      >
        {STEPS.map((step, index) => {
          const isDone = index < activeIndex;
          const isCurrent = index === activeIndex;

          let dotColor = 'var(--color-border)';
          let textColor = 'var(--color-muted)';

          if (isDone) {
            dotColor = 'var(--color-green)';
            textColor = 'var(--color-text)';
          } else if (isCurrent) {
            dotColor = currentStatus === 'in_progress' ? 'var(--color-orange)' : 'var(--color-blue)';
            textColor = 'var(--color-text)';
          }

          return (
            <div
              key={step.key}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                flex: 1,
                position: 'relative',
                zIndex: 2,
              }}
            >
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  backgroundColor: dotColor,
                  color: isDone || isCurrent ? '#FFFFFF' : 'var(--color-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.75rem',
                  fontWeight: '600',
                  boxShadow: isCurrent ? '0 0 0 4px var(--color-blue-light)' : 'none',
                  transition: 'all 0.2s ease',
                }}
              >
                {isDone ? '✓' : index + 1}
              </div>
              <div
                style={{
                  fontSize: '0.75rem',
                  fontWeight: isCurrent ? '600' : '400',
                  color: textColor,
                  textAlign: 'center',
                  marginTop: '6px',
                  lineHeight: '1.2',
                }}
              >
                {step.label}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
