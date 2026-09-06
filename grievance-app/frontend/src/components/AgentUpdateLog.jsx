import React from 'react';
import { useSession } from '../context/SessionContext';

export default function AgentUpdateLog({ updates = [] }) {
  const { t } = useSession();

  if (!updates || updates.length === 0) {
    return (
      <div className="card" style={{ padding: 'var(--spacing-md)' }}>
        <p className="text-muted" style={{ margin: 0, textAlign: 'center' }}>
          {t('noUpdatesYet')}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-sm">
      {updates.map((update, idx) => {
        const timeFormatted = update.sent_at
          ? new Date(update.sent_at).toLocaleString()
          : 'Recent';

        return (
          <div
            key={update.id || idx}
            className="card"
            style={{
              padding: 'var(--spacing-md)',
              borderLeft: '4px solid var(--color-blue)',
            }}
          >
            <div className="flex items-center justify-between mb-xs">
              <span className="badge badge-blue">{t('communicationAgent')}</span>
              <small className="text-muted">{timeFormatted}</small>
            </div>
            <p style={{ margin: '4px 0 0 0', fontSize: '0.95rem' }}>
              {update.message}
            </p>
          </div>
        );
      })}
    </div>
  );
}

