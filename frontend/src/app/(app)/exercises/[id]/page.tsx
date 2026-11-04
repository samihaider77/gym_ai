'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Plus } from '@phosphor-icons/react';
import { AddToWorkoutDialog } from '@/components/add-to-workout';
import { ExerciseCard } from '@/components/exercise-card';
import { ExercisePlayer } from '@/components/exercise-media';
import { PageHeader, Reveal } from '@/components/page';
import { Button } from '@/components/ui/button';
import { Badge, ErrorNotice, Skeleton } from '@/components/ui/feedback';
import type { Exercise, Paginated } from '@/lib/types';
import { useApi } from '@/lib/use-api';
import { titleCase } from '@/lib/utils';
import { useExerciseText } from '@/lib/i18n';

function BackLink() {
  return (
    <Link href="/exercises" className="inline-flex items-center gap-1.5 text-sm font-medium text-muted transition-colors hover:text-ink">
      <ArrowLeft size={16} />
      All exercises
    </Link>
  );
}

function Steps({ text }: { text: string }) {
  const steps = text
    .split(/\n+/)
    .map((s) => s.trim())
    .filter(Boolean);
  if (steps.length <= 1) return <p className="text-[15px] leading-relaxed text-muted">{steps[0]}</p>;
  return (
    <ol className="flex flex-col gap-3">
      {steps.map((step, index) => (
        <li key={index} className="grid grid-cols-[28px_1fr] gap-3 text-[15px] leading-relaxed">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-sunken text-xs font-semibold tabular text-muted">
            {index + 1}
          </span>
          <span className="pt-0.5">{step}</span>
        </li>
      ))}
    </ol>
  );
}

export default function ExerciseDetailPage({ params }: { params: { id: string } }) {
  const { data: exercise, error, loading, reload } = useApi<Exercise>(`/exercises/${params.id}`);
  const [adding, setAdding] = useState(false);
  const text = useExerciseText();
  const primary = exercise?.primary_muscles[0];
  const similar = useApi<Paginated<Exercise>>(
    primary ? '/exercises' : null,
    { query: { muscle_group_id: primary?.id, has_media: true, page_size: 5, is_active: true } },
    [primary?.id],
  );

  if (error) {
    return (
      <>
        <PageHeader title="Exercise" back={<BackLink />} />
        <ErrorNotice message={error} onRetry={reload} />
      </>
    );
  }

  if (loading || !exercise) {
    return (
      <>
        <div className="mb-8 space-y-3">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-8 w-72" />
        </div>
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
          <Skeleton className="aspect-[4/3] rounded-card" />
          <div className="space-y-3">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        </div>
      </>
    );
  }

  const others = similar.data?.items.filter((e) => e.id !== exercise.id).slice(0, 4) ?? [];

  return (
    <>
      <PageHeader
        back={<BackLink />}
        title={text.name(exercise)}
        description={
          <span className="flex flex-wrap gap-1.5 pt-1">
            <Badge tone="accent">{titleCase(exercise.difficulty_level)}</Badge>
            <Badge>{titleCase(exercise.exercise_type)}</Badge>
            {exercise.equipment && <Badge>{exercise.equipment.name}</Badge>}
            {exercise.mechanic_type && <Badge>{titleCase(exercise.mechanic_type)}</Badge>}
          </span>
        }
        actions={
          <Button onClick={() => setAdding(true)}>
            <Plus size={16} weight="bold" />
            Add to workout
          </Button>
        }
      />

      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
        <Reveal>
          <ExercisePlayer exercise={exercise} />
        </Reveal>

        <Reveal delay={0.06} className="flex flex-col gap-8">
          <section>
            <h2 className="mb-3 text-sm font-semibold text-ink">Muscles worked</h2>
            <div className="flex flex-col gap-2.5 text-[15px]">
              <div className="flex items-baseline gap-3">
                <span className="w-24 shrink-0 text-sm text-muted">Primary</span>
                <span className="font-medium">{exercise.primary_muscles.map((m) => m.name).join(', ') || '-'}</span>
              </div>
              {exercise.secondary_muscles.length > 0 && (
                <div className="flex items-baseline gap-3">
                  <span className="w-24 shrink-0 text-sm text-muted">Secondary</span>
                  <span>{exercise.secondary_muscles.map((m) => m.name).join(', ')}</span>
                </div>
              )}
            </div>
          </section>

          <section className="border-t border-line pt-6">
            <h2 className="mb-3 text-sm font-semibold text-ink">How to do it</h2>
            {text.instructions(exercise) ? (
              <Steps text={text.instructions(exercise) as string} />
            ) : (
              <p className="text-[15px] text-muted">No written steps yet. Follow the demo and keep the movement controlled.</p>
            )}
          </section>
        </Reveal>
      </div>

      {others.length > 0 && (
        <section className="mt-14">
          <h2 className="mb-4 text-lg font-semibold tracking-tight">More for your {primary?.name.toLowerCase()}</h2>
          <div className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-4">
            {others.map((e) => (
              <ExerciseCard key={e.id} exercise={e} />
            ))}
          </div>
        </section>
      )}

      <AddToWorkoutDialog open={adding} onClose={() => setAdding(false)} exerciseId={exercise.id} exerciseName={text.name(exercise)} />
    </>
  );
}
