'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, Barbell, ClipboardText, Lightning, Play } from '@phosphor-icons/react';
import { ExerciseCard, ExerciseCardSkeleton } from '@/components/exercise-card';
import { Panel, Reveal } from '@/components/page';
import { LinkButton } from '@/components/ui/button';
import { EmptyState, Skeleton } from '@/components/ui/feedback';
import { session } from '@/lib/api';
import type { BodyProgress, Exercise, Paginated, WorkoutPlan, WorkoutSession } from '@/lib/types';
import { useApi } from '@/lib/use-api';
import { formatDate, formatNumber, greeting } from '@/lib/utils';

function startOfWeek() {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return d;
}

export default function DashboardPage() {
  const [name, setName] = useState('');
  useEffect(() => setName(session.user()?.first_name ?? ''), []);

  const sessions = useApi<Paginated<WorkoutSession>>('/workout-sessions', { query: { page_size: 50 } });
  const plans = useApi<Paginated<WorkoutPlan>>('/workout-plans', { query: { page_size: 5, is_active: true } });
  // Latest measurement: newest-first history, one row. Empty for new users (the /progress endpoint answers 404).
  const progressHistory = useApi<Paginated<BodyProgress>>('/progress/history', { query: { page_size: 1 } });
  const progress = { loading: progressHistory.loading, data: progressHistory.data?.items[0] ?? null };
  // A different page of demo exercises on each visit keeps the home screen fresh.
  const [demoPage] = useState(() => 1 + Math.floor(Math.random() * 20));
  const demos = useApi<Paginated<Exercise>>('/exercises', { query: { has_media: true, page_size: 4, page: demoPage, is_active: true } });

  const items = sessions.data?.items ?? [];
  const active = items.find((s) => s.status === 'IN_PROGRESS');
  const completed = items.filter((s) => s.status === 'COMPLETED');
  const thisWeek = completed.filter((s) => new Date(s.started_at) >= startOfWeek()).length;
  const minutes = completed.reduce((sum, s) => sum + (s.duration_minutes || 0), 0);
  const firstPlan = plans.data?.items[0];

  return (
    <>
      <Reveal>
        <div className="mb-8 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-[15px] text-muted">{greeting()}{name ? `, ${name}` : ''}</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-[28px]">Ready to train?</h1>
          </div>
          {active ? (
            <LinkButton href={`/sessions/${active.id}`} size="lg">
              <Play size={16} weight="fill" />
              Resume workout
            </LinkButton>
          ) : firstPlan ? (
            <LinkButton href={`/workouts/${firstPlan.id}`} size="lg">
              <Lightning size={16} weight="fill" />
              Start a workout
            </LinkButton>
          ) : (
            <LinkButton href="/workouts?new=1" size="lg">
              <ClipboardText size={16} weight="bold" />
              Create a plan
            </LinkButton>
          )}
        </div>
      </Reveal>

      <Reveal delay={0.05}>
        <Panel className="grid grid-cols-2 divide-line md:grid-cols-4 md:divide-x [&>*:nth-child(-n+2)]:border-b [&>*:nth-child(-n+2)]:border-line md:[&>*:nth-child(-n+2)]:border-b-0 [&>*:nth-child(odd)]:border-r [&>*:nth-child(odd)]:border-line md:[&>*:nth-child(odd)]:border-r-0">
          {[
            { label: 'Workouts this week', value: sessions.loading ? null : String(thisWeek) },
            { label: 'Workouts completed', value: sessions.loading ? null : String(completed.length) },
            { label: 'Minutes trained', value: sessions.loading ? null : minutes.toLocaleString() },
            {
              label: 'Body weight',
              value: progress.loading ? null : progress.data ? `${formatNumber(progress.data.weight_kg)} kg` : '-',
            },
          ].map((stat) => (
            <div key={stat.label} className="px-5 py-5">
              <p className="text-[13px] text-muted">{stat.label}</p>
              {stat.value === null ? (
                <Skeleton className="mt-2 h-7 w-16" />
              ) : (
                <p className="mt-1 text-2xl font-semibold tabular tracking-tight">{stat.value}</p>
              )}
            </div>
          ))}
        </Panel>
      </Reveal>

      <div className="mt-10 grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">
        <Reveal delay={0.1}>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight">Recent workouts</h2>
            <Link href="/workouts" className="text-sm font-medium text-accent hover:underline">
              Plans
            </Link>
          </div>
          {sessions.loading ? (
            <div className="space-y-2">
              {[0, 1, 2].map((i) => (
                <Skeleton key={i} className="h-16 rounded-card" />
              ))}
            </div>
          ) : items.length === 0 ? (
            <EmptyState
              icon={<ClipboardText size={22} />}
              title="No workouts yet"
              body="Build a plan, start a session and your history shows up here."
              action={firstPlan && <LinkButton href={`/workouts/${firstPlan.id}`} variant="secondary">Open your plan</LinkButton>}
            />
          ) : (
            <Panel className="divide-y divide-line">
              {items.slice(0, 5).map((s) => (
                <Link
                  key={s.id}
                  href={`/sessions/${s.id}`}
                  className="group flex items-center justify-between gap-3 px-4 py-3.5 transition-colors first:rounded-t-card last:rounded-b-card hover:bg-sunken/60"
                >
                  <div>
                    <p className="text-[15px] font-medium">{formatDate(s.started_at, { weekday: 'long', day: 'numeric', month: 'short' })}</p>
                    <p className="text-[13px] text-muted">
                      {s.status === 'COMPLETED'
                        ? `${s.duration_minutes} min`
                        : s.status === 'IN_PROGRESS'
                          ? 'In progress'
                          : 'Cancelled'}
                    </p>
                  </div>
                  <ArrowRight size={16} className="text-faint transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-ink" />
                </Link>
              ))}
            </Panel>
          )}
        </Reveal>

        <Reveal delay={0.15}>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight">Learn a movement</h2>
            <Link href="/exercises" className="text-sm font-medium text-accent hover:underline">
              Browse all
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
            {demos.loading || !demos.data
              ? [0, 1, 2, 3].map((i) => <ExerciseCardSkeleton key={i} />)
              : demos.data.items.map((e) => <ExerciseCard key={e.id} exercise={e} />)}
          </div>
          {demos.data?.items.length === 0 && (
            <EmptyState icon={<Barbell size={22} />} title="No demos yet" body="Run the media importer to add exercise videos." />
          )}
        </Reveal>
      </div>
    </>
  );
}
