import React, { createContext, useContext, useState, useEffect } from 'react';
import { getToken, setToken, clearToken } from '../api/client';
import { translations } from '../i18n/translations';

const SessionContext = createContext(null);

const STORAGE_KEYS = {
  TOKEN: 'nagar_seva_token',
  SESSION_ID: 'nagar_seva_session',
  USER: 'nagar_seva_user',
  LANG: 'nagar_seva_lang',
};

export function SessionProvider({ children }) {
  const [token, setTokenState] = useState(() => localStorage.getItem(STORAGE_KEYS.TOKEN) || getToken());
  const [sessionId, setSessionIdState] = useState(() => localStorage.getItem(STORAGE_KEYS.SESSION_ID) || null);
  const [langState, setLangState] = useState(() => localStorage.getItem(STORAGE_KEYS.LANG) || 'en');
  const [citizen, setCitizenState] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.USER);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const isAuthenticated = Boolean(token && sessionId && citizen);
  const preferredLang = citizen?.preferred_lang || langState || 'en';

  const loginCitizen = (jwtToken, newSessionId, userData) => {
    setToken(jwtToken);
    localStorage.setItem(STORAGE_KEYS.TOKEN, jwtToken);
    localStorage.setItem(STORAGE_KEYS.SESSION_ID, newSessionId);
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
    if (userData && userData.preferred_lang) {
      localStorage.setItem(STORAGE_KEYS.LANG, userData.preferred_lang);
      setLangState(userData.preferred_lang);
    }

    setTokenState(jwtToken);
    setSessionIdState(newSessionId);
    setCitizenState(userData);
  };

  const updatePreferredLanguage = (newLang) => {
    localStorage.setItem(STORAGE_KEYS.LANG, newLang);
    setLangState(newLang);
    if (citizen) {
      const updated = { ...citizen, preferred_lang: newLang };
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(updated));
      setCitizenState(updated);
    }
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

  const t = (key) => {
    const dict = translations[preferredLang] || translations.en;
    return dict[key] || translations.en[key] || key;
  };

  return (
    <SessionContext.Provider
      value={{
        token,
        sessionId,
        citizen,
        preferredLang,
        isAuthenticated,
        loginCitizen,
        updatePreferredLanguage,
        closeSession,
        t,
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
