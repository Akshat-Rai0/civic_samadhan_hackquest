import React from 'react';
import { Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import Login from './pages/citizen/Login';
import Upload from './pages/citizen/Upload';
import Confirm from './pages/citizen/Confirm';
import Track from './pages/citizen/Track';
import Queue from './pages/admin/Queue';
import Heatmap from './pages/admin/Heatmap';
import IssueDetail from './pages/admin/IssueDetail';

export default function App() {
  const location = useLocation();
  const isAdmin = location.pathname.startsWith('/admin');

  return (
    <div>
      {/* Global Navigation Header */}
      <header
        style={{
          backgroundColor: '#FFFFFF',
          borderBottom: '1px solid var(--color-border)',
          padding: '0 var(--spacing-md)',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <div
          style={{
            maxWidth: '1040px',
            margin: '0 auto',
            height: '60px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {/* Brand Logo */}
          <Link
            to={isAdmin ? '/admin' : '/upload'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              textDecoration: 'none',
              color: 'var(--color-text)',
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '6px',
                backgroundColor: 'var(--color-orange)',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '1.1rem',
              }}
            >
              N
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', lineHeight: 1.1 }}>Nagar Seva</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-muted)' }}>
                Auto Grievance Raiser
              </div>
            </div>
          </Link>

          {/* Section Mode Toggle */}
          <nav style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Link
              to="/upload"
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                fontSize: '0.85rem',
                fontWeight: 600,
                color: !isAdmin ? 'var(--color-white)' : 'var(--color-text)',
                backgroundColor: !isAdmin ? 'var(--color-blue)' : 'transparent',
                textDecoration: 'none',
              }}
            >
              Citizen Portal
            </Link>

            <Link
              to="/admin"
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                fontSize: '0.85rem',
                fontWeight: 600,
                color: isAdmin ? 'var(--color-white)' : 'var(--color-text)',
                backgroundColor: isAdmin ? 'var(--color-text)' : 'transparent',
                textDecoration: 'none',
              }}
            >
              Admin Dashboard
            </Link>

            {isAdmin && (
              <div style={{ display: 'flex', gap: '4px', marginLeft: '12px', borderLeft: '1px solid var(--color-border)', paddingLeft: '12px' }}>
                <Link
                  to="/admin"
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: 500,
                    padding: '4px 8px',
                    color: location.pathname === '/admin' ? 'var(--color-orange)' : 'var(--color-muted)',
                    textDecoration: 'none',
                  }}
                >
                  Queue
                </Link>
                <Link
                  to="/admin/heatmap"
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: 500,
                    padding: '4px 8px',
                    color: location.pathname === '/admin/heatmap' ? 'var(--color-orange)' : 'var(--color-muted)',
                    textDecoration: 'none',
                  }}
                >
                  Heatmap
                </Link>
              </div>
            )}
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ minHeight: 'calc(100vh - 120px)' }}>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/confirm/:imageId" element={<Confirm />} />
          <Route path="/track/:clusterId" element={<Track />} />
          <Route path="/my-issues" element={<Navigate to="/upload" replace />} />

          {/* Admin Routes */}
          <Route path="/admin" element={<Queue />} />
          <Route path="/admin/heatmap" element={<Heatmap />} />
          <Route path="/admin/issues/:clusterId" element={<IssueDetail />} />

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--color-border)',
          backgroundColor: '#FFFFFF',
          padding: 'var(--spacing-md) 0',
          textAlign: 'center',
          fontSize: '0.8rem',
          color: 'var(--color-muted)',
          marginTop: 'var(--spacing-xl)',
        }}
      >
        <div className="container">
          Nagar Seva - Municipal Corporation Grievance Redressal System (Prototype)
        </div>
      </footer>
    </div>
  );
}
