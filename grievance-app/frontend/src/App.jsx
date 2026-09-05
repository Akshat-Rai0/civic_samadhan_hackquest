import React from 'react';
import { Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { SessionProvider, useSession } from './context/SessionContext';
import { logoutApi } from './api/client';
import Login from './pages/citizen/Login';
import Upload from './pages/citizen/Upload';
import Confirm from './pages/citizen/Confirm';
import Track from './pages/citizen/Track';
import Queue from './pages/admin/Queue';
import Heatmap from './pages/admin/Heatmap';
import IssueDetail from './pages/admin/IssueDetail';

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useSession();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function NavigationHeader() {
  const location = useLocation();
  const navigate = useNavigate();
  const { citizen, sessionId, isAuthenticated, closeSession } = useSession();
  const isAdmin = location.pathname.startsWith('/admin');

  const handleEndSession = async () => {
    await logoutApi();
    closeSession();
    navigate('/login');
  };

  const maskedId = citizen?.mock_id_number
    ? `XXXX ${citizen.mock_id_number.slice(-4)}`
    : 'XXXX 4821';

  return (
    <header
      style={{
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid var(--color-border)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <div
        style={{
          maxWidth: '1080px',
          margin: '0 auto',
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 var(--spacing-md)',
        }}
      >
        {/* Brand Logo (Left) */}
        <Link
          to={isAdmin ? '/admin' : '/upload'}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            textDecoration: 'none',
          }}
        >
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '50%',
              backgroundColor: '#FFFFFF',
              border: '2px solid var(--color-blue)',
              color: 'var(--color-blue)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '1rem',
              boxShadow: '0 0 0 2px var(--color-orange-light)',
            }}
          >
            ⚙
          </div>
          <div>
            <div
              style={{
                fontFamily: 'var(--font-heading)',
                fontWeight: 700,
                fontSize: '1.15rem',
                color: 'var(--color-heading)',
                lineHeight: 1.1,
              }}
            >
              CivicSamadhaan
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--color-muted)', letterSpacing: '0.02em' }}>
              Nagar Seva Redressal
            </div>
          </div>
        </Link>

        {/* Navigation Tabs (Center) */}
        <nav style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
          <Link
            to="/upload"
            className={`nav-tab-link ${!isAdmin ? 'active' : ''}`}
          >
            Citizen Portal
          </Link>

          <Link
            to="/admin"
            className={`nav-tab-link ${isAdmin && location.pathname === '/admin' ? 'active' : ''}`}
          >
            Admin Queue
          </Link>

          <Link
            to="/admin/heatmap"
            className={`nav-tab-link ${isAdmin && location.pathname === '/admin/heatmap' ? 'active' : ''}`}
          >
            Heatmap
          </Link>
        </nav>

        {/* Top-Right Actions (Primary CTA in Accent Orange + Profile Far Right) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Link to="/upload" className="btn btn-primary btn-sm">
            <span style={{ fontSize: '1rem' }}>📄</span> File Complaint
          </Link>

          {/* Profile Avatar Far Right */}
          {isAuthenticated ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                paddingLeft: '8px',
                borderLeft: '1px solid var(--color-border)',
              }}
            >
              <div
                style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--color-orange-light)',
                  border: '1px solid var(--color-orange)',
                  color: 'var(--color-orange)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '0.9rem',
                }}
                title={`${citizen?.name || 'User'} (${maskedId})`}
              >
                {citizen?.name ? citizen.name.charAt(0) : 'U'}
              </div>
              <button
                type="button"
                onClick={handleEndSession}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--color-muted)',
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                  padding: '2px 4px',
                }}
                title="Sign out"
              >
                Exit
              </button>
            </div>
          ) : (
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '50%',
                backgroundColor: 'var(--color-blue-light)',
                color: 'var(--color-blue)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 600,
                fontSize: '0.9rem',
              }}
            >
              👤
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <SessionProvider>
      <div>
        <NavigationHeader />

        {/* Main Content Area */}
        <main style={{ minHeight: 'calc(100vh - 120px)' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login />} />
            <Route
              path="/upload"
              element={
                <ProtectedRoute>
                  <Upload />
                </ProtectedRoute>
              }
            />
            <Route
              path="/confirm/:imageId"
              element={
                <ProtectedRoute>
                  <Confirm />
                </ProtectedRoute>
              }
            />
            <Route
              path="/track/:clusterId"
              element={
                <ProtectedRoute>
                  <Track />
                </ProtectedRoute>
              }
            />
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
    </SessionProvider>
  );
}
