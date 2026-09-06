import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, register, logoutApi } from '../../api/client';
import { useSession } from '../../context/SessionContext';

export default function Login() {
  const navigate = useNavigate();
  const { citizen, sessionId, isAuthenticated, loginCitizen, closeSession, t } = useSession();

  const [name, setName] = useState('Ananya Sharma');
  const [mockId, setMockId] = useState('548291034821');
  const [otpStep, setOtpStep] = useState(false);
  const [otp, setOtp] = useState('123456');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSendOtp = (e) => {
    e.preventDefault();
    if (!name.trim() || !mockId.trim()) {
      setError(t('aadhaarHint'));
      return;
    }
    if (mockId.replace(/\s+/g, '').length !== 12) {
      setError(t('aadhaarHint'));
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
          <h1 style={{ marginTop: 0, marginBottom: '4px' }}>{t('signIn')}</h1>
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
              <strong>{t('activeSessionDetected')}</strong>
              <div style={{ marginTop: '4px', fontSize: '0.9rem' }}>
                {t('signedInAs')} <strong>{citizen?.name}</strong> (Session ID: <code>{sessionId}</code>)
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => navigate('/upload')}
              >
                {t('continueToReport')}
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={handleSwitchUser}
              >
                {t('closeSessionSwitch')}
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
              <label htmlFor="fullname">{t('fullName')}</label>
              <input
                id="fullname"
                type="text"
                className="form-input"
                placeholder={t('enterName')}
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="mockid">{t('enterAadhaar')}</label>
              <input
                id="mockid"
                type="text"
                maxLength={12}
                className="form-input"
                placeholder={t('aadhaarPlaceholder')}
                value={mockId}
                onChange={(e) => setMockId(e.target.value)}
                required
              />
              <div className="form-hint">
                {t('aadhaarHint')}
              </div>
            </div>

            <button type="submit" className="btn btn-primary btn-block" style={{ marginTop: 'var(--spacing-md)' }}>
              {t('sendOtp')}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp}>
            <div className="notice notice-info">
              {t('otpSentNotice')}
            </div>

            <div className="form-group">
              <label htmlFor="otp">{t('verificationCode')}</label>
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
              {loading ? t('verifying') : t('verifyAndContinue')}
            </button>

            <button
              type="button"
              className="btn btn-secondary btn-block"
              style={{ marginTop: 'var(--spacing-sm)' }}
              onClick={() => setOtpStep(false)}
            >
              {t('back')}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

