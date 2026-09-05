import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, register, logoutApi } from '../../api/client';
import { useSession } from '../../context/SessionContext';

export default function Login() {
  const navigate = useNavigate();
  const { citizen, sessionId, isAuthenticated, loginCitizen, closeSession } = useSession();

  const [name, setName] = useState('Ananya Sharma');
  const [mockId, setMockId] = useState('548291034821');
  const [otpStep, setOtpStep] = useState(false);
  const [otp, setOtp] = useState('123456');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSendOtp = (e) => {
    e.preventDefault();
    if (!name.trim() || !mockId.trim()) {
      setError('Please enter your full name and 12-digit identification number.');
      return;
    }
    if (mockId.replace(/\s+/g, '').length !== 12) {
      setError('Identification number must be exactly 12 digits.');
      return;
    }
    setError(null);
    setOtpStep(true);
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      try {
        await register(mockId, name);
      } catch {
        // User may already be registered, proceed to login
      }
      const data = await login(mockId, otp);
      if (data && data.session_id) {
        loginCitizen(data.access_token, data.session_id, data.user);
      }
      navigate('/upload');
    } catch (err) {
      setError(err.message || 'Login failed. Please check the OTP code.');
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchUser = async () => {
    await logoutApi();
    closeSession();
  };

  return (
    <div className="container-narrow" style={{ marginTop: 'var(--spacing-xl)' }}>
      <div className="card">
        <div style={{ marginBottom: 'var(--spacing-md)' }}>
          <span className="badge badge-blue">Nagar Seva Citizen Portal</span>
          <h1 style={{ marginTop: 'var(--spacing-sm)', marginBottom: '4px' }}>Sign in</h1>
          <p className="text-muted" style={{ fontSize: '0.85rem' }}>
            Simulated login for prototype. No real identity verification.
          </p>
        </div>

        {isAuthenticated && (
          <div
            className="notice notice-info"
            style={{
              marginBottom: 'var(--spacing-md)',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div>
              <strong>Active Citizen Session Detected:</strong>
              <div style={{ marginTop: '4px', fontSize: '0.9rem' }}>
                Signed in as <strong>{citizen?.name}</strong> (Session ID: <code>{sessionId}</code>)
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => navigate('/upload')}
              >
                Continue to Report Issue
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={handleSwitchUser}
              >
                Close Session & Switch User
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="notice notice-warning" style={{ marginBottom: 'var(--spacing-md)' }}>
            {error}
          </div>
        )}

        {!otpStep ? (
          <form onSubmit={handleSendOtp}>
            <div className="form-group">
              <label htmlFor="fullname">Full name</label>
              <input
                id="fullname"
                type="text"
                className="form-input"
                placeholder="Enter your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="mockid">12-digit ID number</label>
              <input
                id="mockid"
                type="text"
                maxLength={12}
                className="form-input"
                placeholder="XXXX XXXX XXXX"
                value={mockId}
                onChange={(e) => setMockId(e.target.value)}
                required
              />
              <div className="form-hint">
                Use any 12 digits for testing. Duplicate reports from the same ID update existing tickets.
              </div>
            </div>

            <button type="submit" className="btn btn-primary btn-block" style={{ marginTop: 'var(--spacing-md)' }}>
              Send one-time password
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp}>
            <div className="notice notice-info">
              One-time password sent. Use code <strong>123456</strong> for testing.
            </div>

            <div className="form-group">
              <label htmlFor="otp">Verification code</label>
              <input
                id="otp"
                type="text"
                className="form-input text-center"
                style={{ fontSize: '1.25rem', letterSpacing: '4px' }}
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                maxLength={6}
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={loading}
              style={{ marginTop: 'var(--spacing-md)' }}
            >
              {loading ? 'Verifying...' : 'Verify and continue'}
            </button>

            <button
              type="button"
              className="btn btn-secondary btn-block"
              style={{ marginTop: 'var(--spacing-sm)' }}
              onClick={() => setOtpStep(false)}
            >
              Back
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
