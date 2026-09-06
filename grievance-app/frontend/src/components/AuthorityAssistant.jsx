import React, { useState } from 'react';
import { askAuthorityAssistant } from '../api/client';

const STARTERS = [
  'Which issues have the highest priority right now?',
  'Give me the responsibility and current status for GR-1.',
  'Summarise the backlog by department.',
];

export default function AuthorityAssistant() {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const sendMessage = async (text = draft) => {
    const message = text.trim();
    if (!message || loading) return;

    const history = messages.slice(-10).map(({ role, content }) => ({ role, content }));
    setMessages((current) => [...current, { role: 'user', content: message }]);
    setDraft('');
    setLoading(true);
    setError('');
    try {
      const result = await askAuthorityAssistant(message, history);
      setMessages((current) => [...current, {
        role: 'assistant',
        content: result.answer,
        sources: result.sources || [],
      }]);
    } catch (err) {
      setError(err.message || 'The issue assistant is unavailable.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card" aria-labelledby="authority-assistant-title" style={{ marginTop: 'var(--spacing-lg)', padding: 'var(--spacing-md)' }}>
      <div className="flex items-center justify-between" style={{ gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
        <div>
          <h2 id="authority-assistant-title" style={{ margin: 0 }}>Authority Issue Assistant</h2>
          <p className="text-muted" style={{ margin: '4px 0 0' }}>
            Ask about live tickets, issue dates and locations, department responsibility, assignments, priority, SLA, and evidence.
          </p>
        </div>
        <span className="badge badge-blue">Read-only live data</span>
      </div>

      {messages.length === 0 && (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', margin: 'var(--spacing-md) 0' }}>
          {STARTERS.map((starter) => (
            <button key={starter} type="button" className="btn btn-secondary btn-sm" onClick={() => sendMessage(starter)} disabled={loading}>
              {starter}
            </button>
          ))}
        </div>
      )}

      {messages.length > 0 && (
        <div aria-live="polite" style={{ maxHeight: '340px', overflowY: 'auto', display: 'grid', gap: '10px', margin: 'var(--spacing-md) 0' }}>
          {messages.map((item, index) => (
            <div key={`${item.role}-${index}`} style={{ justifySelf: item.role === 'user' ? 'end' : 'start', maxWidth: '88%', background: item.role === 'user' ? 'var(--color-blue-light)' : '#f8fafc', border: '1px solid var(--color-border)', borderRadius: '10px', padding: '10px 12px', whiteSpace: 'pre-wrap' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--color-muted)', fontWeight: 700, marginBottom: '4px' }}>{item.role === 'user' ? 'YOU' : 'ASSISTANT'}</div>
              <div>{item.content}</div>
              {item.sources?.length > 0 && <div className="text-muted" style={{ fontSize: '0.72rem', marginTop: '6px' }}>Live data checked: {[...new Set(item.sources)].join(', ')}</div>}
            </div>
          ))}
          {loading && <div className="text-muted" style={{ fontSize: '0.9rem' }}>Checking the current issue records…</div>}
        </div>
      )}

      {error && <div className="notice notice-warning" style={{ marginBottom: '10px' }}>{error}</div>}
      <form onSubmit={(event) => { event.preventDefault(); sendMessage(); }} style={{ display: 'flex', gap: '8px', alignItems: 'end' }}>
        <textarea className="form-input" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="For example: Who is responsible for GR-12 and when was it reported?" rows={2} maxLength={4000} disabled={loading} style={{ resize: 'vertical', flex: 1 }} />
        <button type="submit" className="btn btn-primary" disabled={!draft.trim() || loading}>{loading ? 'Asking…' : 'Ask'}</button>
      </form>
    </section>
  );
}
