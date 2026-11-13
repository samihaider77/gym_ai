'use client';

import { useEffect, useState } from 'react';
import { Brand } from '@/components/brand';
import { ThemeToggle } from '@/components/theme';
import { api } from '@/lib/api';
import type { Exercise, Paginated } from '@/lib/types';

// The demos are open-licensed (CC BY-SA), which asks for credit. Instead of a line under every player, all
// credits are collected here, linked from the sidebar and the sign-in page.
const SOURCES = [
  {
    name: 'Everkinetic',
    url: 'https://everkinetic.com',
    what: 'Exercise line drawings',
    license: 'CC BY-SA 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0/',
  },
  {
    name: 'Workout Guide by Bryl Lim',
    url: 'https://github.com/bryllim/workout-guide',
    what: 'Exercise drawings based on Everkinetic',
    license: 'CC BY-SA 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0/',
  },
  {
    name: 'wger.de contributors',
    url: 'https://wger.de',
    what: 'Exercise drawings and the front squat video on the sign-in page (by Goulart)',
    license: 'CC BY-SA 3.0 / 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0/',
  },
];

type Credit = { exercise: string; text: string };

export default function CreditsPage() {
  const [credits, setCredits] = useState<Credit[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const found: Credit[] = [];
      for (let page = 1; page <= 20; page++) {
        const result = await api<Paginated<Exercise>>('/exercises', {
          query: { page, page_size: 100, is_active: true, has_media: true },
        });
        result.items.forEach((exercise) =>
          exercise.media?.forEach((m) => m.attribution && found.push({ exercise: exercise.name, text: m.attribution })),
        );
        if (page >= result.total_pages) break;
      }
      if (!cancelled) setCredits(found.sort((a, b) => a.exercise.localeCompare(b.exercise)));
    })().catch(() => !cancelled && setCredits([]));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-5 py-6 sm:px-10">
      <div className="flex items-center justify-between">
        <Brand href="/" />
        <ThemeToggle />
      </div>

      <h1 className="mt-10 text-3xl font-semibold tracking-tight">Credits</h1>
      <p className="mt-2 max-w-[65ch] text-muted">
        RepRight&apos;s exercise demos come from open, freely licensed collections. Thank you to their creators.
      </p>

      <ul className="mt-8 divide-y divide-line border-y border-line">
        {SOURCES.map((source) => (
          <li key={source.name} className="py-4">
            <a href={source.url} target="_blank" rel="noreferrer" className="font-medium hover:text-accent">
              {source.name}
            </a>
            <p className="mt-0.5 text-sm text-muted">
              {source.what} ·{' '}
              <a href={source.licenseUrl} target="_blank" rel="noreferrer" className="underline-offset-2 hover:underline">
                {source.license}
              </a>
            </p>
          </li>
        ))}
      </ul>

      <h2 className="mt-10 text-lg font-semibold">Every demo</h2>
      {credits === null ? (
        <p className="mt-3 text-sm text-muted">Loading credits…</p>
      ) : credits.length === 0 ? (
        <p className="mt-3 text-sm text-muted">Credits couldn&apos;t be loaded right now.</p>
      ) : (
        <ul className="mt-3 space-y-2 text-sm text-muted">
          {credits.map((credit, index) => (
            <li key={index}>
              <span className="font-medium text-ink">{credit.exercise}</span>: {credit.text}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
