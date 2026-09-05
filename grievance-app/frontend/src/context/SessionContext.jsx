import React, { createContext, useContext, useState, useEffect } from 'react';
import { getToken, setToken, clearToken } from '../api/client';

const SessionContext = createContext(null);

const STORAGE_KEYS = {
  TOKEN: 'nagar_seva_token',
  SESSION_ID: 'nagar_seva_session',
  USER: 'nagar_seva_user',
};

export function SessionProvider({ children }) {
  const [token, setTokenState] = useState(() => localStorage.getItem(STORAGE_KEYS.TOKEN) || getToken());
  const [sessionId, setSessionIdState] = useState(() => localStorage.getItem(STORAGE_KEYS.SESSION_ID) || null);
  const [citizen, setCitizenState] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.USER);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const isAuthenticated = Boolean(token && sessionId && citizen);

  const loginCitizen = (jwtToken, newSessionId, userData) => {
    setToken(jwtToken);
    localStorage.setItem(STORAGE_KEYS.TOKEN, jwtToken);
    localStorage.setItem(STORAGE_KEYS.SESSION_ID, newSessionId);
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));

    setTokenState(jwtToken);
    setSessionIdState(newSessionId);
    setCitizenState(userData);
  };

  const closeSession = () => {
    clearToken();
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
    localStorage.removeItem(STORAGE_KEYS.SESSION_ID);
    localStorage.removeItem(STORAGE_KEYS.USER);

    setTokenState(null);
    setSessionIdState(null);
    setCitizenState(null);
  };

  return (
    <SessionContext.Provider
      value={{
        token,
        sessionId,
        citizen,
        isAuthenticated,
        loginCitizen,
        closeSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
}
