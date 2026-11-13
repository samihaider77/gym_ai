'use client';

import { LANGUAGES, useLanguage } from '@/lib/i18n';
import { cn } from '@/lib/utils';

/** Two-option switch: English / Roman Urdu exercise names and steps. `compact` shows short labels for top bars. */
export function LanguageToggle({ compact, className }: { compact?: boolean; className?: string }) {
  const { lang, setLang } = useLanguage();
  return (
    <div className={cn('flex rounded-control bg-sunken p-0.5', !compact && 'w-full', className)} role="group" aria-label="Exercise language">
      {LANGUAGES.map((option) => (
        <button
          key={option.value}
          onClick={() => setLang(option.value)}
          aria-pressed={lang === option.value}
          title={option.label}
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
}
