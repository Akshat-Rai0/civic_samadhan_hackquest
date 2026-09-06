import React from 'react';
import { Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { SessionProvider, useSession } from './context/SessionContext';
import { logoutApi, updatePreferredLangApi } from './api/client';
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
  const { citizen, sessionId, isAuthenticated, preferredLang, updatePreferredLanguage, closeSession, t } = useSession();
  const isAdmin = location.pathname.startsWith('/admin');

  const handleLangChange = async (e) => {
    const newLang = e.target.value;
    updatePreferredLanguage(newLang);
    if (isAuthenticated) {
      try {
        await updatePreferredLangApi(newLang);
      } catch (err) {
        console.warn('Failed to update language on server:', err);
      }
    }
  };

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
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 0 0 1.5px var(--color-border)',
              position: 'relative',
              flexShrink: 0,
            }}
            title="CivicSamadhaan"
          >
            <div style={{ flex: 1, backgroundColor: '#FF9933' }} />
            <div style={{ flex: 1, backgroundColor: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', border: '1.5px solid #000080' }} />
            </div>
            <div style={{ flex: 1, backgroundColor: '#138808' }} />
          </div>
          <div>
            <div
              style={{
                fontFamily: 'var(--font-heading)',
                fontWeight: 700,
                fontSize: '1.15rem',
                color: 'var(--color-heading)',
                lineHeight: 1.1,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <span>{t('appName')}</span>
              <span style={{ fontSize: '0.85rem', color: 'var(--color-muted)', fontWeight: 500 }}>{t('hindiTagline')}</span>
            </div>
          </div>
        </Link>

        {/* Navigation Tabs (Center) */}
        <nav style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
          <Link
            to="/upload"
            className={`nav-tab-link ${!isAdmin ? 'active' : ''}`}
          >
            {t('citizenPortal')}
          </Link>

          <Link
            to="/admin"
            className={`nav-tab-link ${isAdmin && location.pathname === '/admin' ? 'active' : ''}`}
          >
            {t('authorityDashboard')}
          </Link>

          <Link
            to="/admin/heatmap"
            className={`nav-tab-link ${isAdmin && location.pathname === '/admin/heatmap' ? 'active' : ''}`}
          >
            {t('heatmap')}
          </Link>
        </nav>

        {/* Top-Right Actions (Primary CTA in Accent Orange + Profile Far Right) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Language Switcher (Citizen Portal only) */}
          {!isAdmin && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <select
                aria-label="Preferred Language"
                value={preferredLang}
                onChange={handleLangChange}
                style={{
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  padding: '4px 8px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  backgroundColor: '#FFFFFF',
                  color: 'var(--color-heading)',
                  cursor: 'pointer',
                }}
              >
                <option value="en">English (EN)</option>
                <option value="hi">हिंदी (Hindi)</option>
              </select>
            </div>
          )}

          <Link to="/upload" className="btn btn-primary btn-sm">
            <span style={{ fontSize: '1rem' }}>📄</span> {t('fileComplaint')}
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
                {t('signOut')}
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

function AppFooter() {
  const { t } = useSession();
  return (
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
        {t('footerText')}
      </div>
    </footer>
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

        <AppFooter />
      </div>
    </SessionProvider>
  );
}

