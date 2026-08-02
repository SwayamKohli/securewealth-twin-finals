// src/i18n/index.tsx
// SecureWealth Twin — lightweight i18n (task 1.5: EN / HI / PA).
// No external deps: React context + AsyncStorage persistence.

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { CATALOGS, LANGUAGES, type Language } from './translations';

const STORAGE_KEY = 'swt_language';

interface I18nContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextValue>({
  language: 'en',
  setLanguage: () => {},
  t: (k) => CATALOGS.en[k] ?? k,
});

export const I18nProvider = ({ children }: { children: React.ReactNode }) => {
  const [language, setLanguageState] = useState<Language>('en');

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((saved) => {
      if (saved === 'en' || saved === 'hi' || saved === 'pa') {
        setLanguageState(saved);
      }
    });
  }, []);

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    AsyncStorage.setItem(STORAGE_KEY, lang).catch(() => {});
  }, []);

  const t = useCallback(
    (key: string): string => CATALOGS[language][key] ?? CATALOGS.en[key] ?? key,
    [language]
  );

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = () => useContext(I18nContext);
export { LANGUAGES, type Language };
