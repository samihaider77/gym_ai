'use client';

import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { Exercise } from './types';

export type Language = 'en' | 'ur';
export const LANGUAGES: { value: Language; label: string }[] = [
  { value: 'en', label: 'English' },
  { value: 'ur', label: 'Roman Urdu' },
];

const KEY = 'gymai.lang';

const I18nContext = createContext<{ lang: Language; setLang: (lang: Language) => void }>({
  lang: 'en',
  setLang: () => {},
});

/**
 * The language only changes exercise names and their "How to do it" steps. The Roman Urdu text
 * comes from the API (name_ur, instructions_ur), so it works offline; the rest of the app stays English.
 */
export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Language>('en');

  useEffect(() => {
    try {
      if (localStorage.getItem(KEY) === 'ur') setLangState('ur');
    } catch {}
  }, []);

  const setLang = useCallback((next: Language) => {
    setLangState(next);
    try {
      localStorage.setItem(KEY, next);
    } catch {}
  }, []);

  return <I18nContext.Provider value={{ lang, setLang }}>{children}</I18nContext.Provider>;
}

export function useLanguage() {
  return useContext(I18nContext);
}

/** Exercise name and steps in the chosen language, falling back to English when there is no translation. */
export function useExerciseText() {
  const { lang } = useLanguage();
  const ur = lang === 'ur';
  return {
    name: (exercise: Pick<Exercise, 'name' | 'name_ur'>) => (ur && exercise.name_ur) || exercise.name,
    instructions: (exercise: Pick<Exercise, 'instructions' | 'instructions_ur'>) =>
      (ur && exercise.instructions_ur) || exercise.instructions,
  };
}
