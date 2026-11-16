'use client';

import { Barbell } from '@phosphor-icons/react';
import { useToast } from '@/components/ui/toast';
import { LANGUAGES, useLanguage, type Language } from '@/lib/i18n';
import { cn } from '@/lib/utils';

// The switch only changes exercise names and their steps; the rest of the app stays in English. Say so on the
// control itself and when it is used, because people otherwise expect the whole site to switch to Urdu.
const SCOPE = 'Changes exercise names and steps only';
const SWITCHED: Record<Language, string> = {
  en: 'Exercise names and steps are now in English.',
  ur: 'Exercise names and steps are now in Roman Urdu. The rest of the app stays in English.',
};

/** Two-option switch: English / Roman Urdu exercise names and steps. `compact` shows short labels for top bars. */
export function LanguageToggle({ compact, className }: { compact?: boolean; className?: string }) {
  const { lang, setLang } = useLanguage();
  const toast = useToast();

  const choose = (value: Language) => {
    if (value === lang) return;
    setLang(value);
    toast(SWITCHED[value]);
  };

  const buttons = (
    <div
      className={cn('flex items-center rounded-control bg-sunken p-0.5', !compact && 'w-full', compact && className)}
      role="group"
      aria-label={`Exercise language. ${SCOPE}.`}
      title={`Exercise language: ${SCOPE.toLowerCase()}`}
    >
      {compact && <Barbell size={14} className="ml-1.5 mr-0.5 shrink-0 text-muted" aria-hidden />}
      {LANGUAGES.map((option) => (
        <button
          key={option.value}
          onClick={() => choose(option.value)}
          aria-pressed={lang === option.value}
          title={`${option.label} exercise names and steps`}
          className={cn(
            'h-8 whitespace-nowrap rounded-[8px] px-2 text-xs font-medium transition-colors',
            !compact && 'flex-1',
            lang === option.value ? 'bg-surface text-ink shadow-sm' : 'text-muted hover:text-ink',
          )}
        >
          {compact ? (option.value === 'en' ? 'EN' : 'UR') : option.label}
        </button>
      ))}
    </div>
  );

  if (compact) return buttons;

  return (
    <div className={cn('flex min-w-0 flex-col gap-1', className)}>
      <span className="px-0.5 text-[11px] font-medium text-muted">Exercise language</span>
      {buttons}
    </div>
  );
}
