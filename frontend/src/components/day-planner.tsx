'use client';

import { useEffect, useState } from 'react';
import { ArrowClockwise, ArrowLeft, HandPointing, MagicWand, X } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';
import { Dialog } from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/feedback';
import { api } from '@/lib/api';
import { useExerciseText } from '@/lib/i18n';
import { prescribe, suggestDay, type Prescription } from '@/lib/suggest';
import type { Exercise, MuscleGroup, Paginated, WorkoutPlan } from '@/lib/types';
import { useApi } from '@/lib/use-api';
import { rememberExercise } from '@/lib/use-exercises';
import { cn, titleCase } from '@/lib/utils';
import { MiniThumb } from './exercise-media';

type Step = 'choose' | 'muscles' | 'preview';
type Facets = { muscles: { value: string; count: number }[] };
const MAX_MUSCLES = 3;

const rest = (seconds: number) => (seconds % 60 === 0 ? `${seconds / 60} min rest` : `${seconds}s rest`);

/**
 * "How do you want to fill this day?": either suggest exercises for chosen muscles, matched to the plan's goal
 * and level, or open the normal picker. Suggestions are shown first and only added on confirm.
 */
export function DayPlanner({
  open,
  onClose,
  plan,
  dayTitle,
  onPickManually,
  onAddSuggested,
}: {
  open: boolean;
  onClose: () => void;
  plan: WorkoutPlan | null;
  dayTitle: string;
  onPickManually: () => void;
  onAddSuggested: (picks: { exercise: Exercise; prescription: Prescription }[]) => Promise<void>;
}) {
  const text = useExerciseText();
  const [step, setStep] = useState<Step>('choose');
  const [chosen, setChosen] = useState<string[]>([]);
  const [pools, setPools] = useState<Exercise[][] | null>(null);
  const [picks, setPicks] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const goal = plan?.goal ?? 'general_fitness';
  const level = plan?.difficulty ?? 'beginner';

  useEffect(() => {
    if (open) return;
    setStep('choose');
    setChosen([]);
    setPools(null);
    setPicks([]);
    setError(null);
  }, [open]);

  // Only muscles that have exercises with a demo can be suggested.
  const muscles = useApi<Paginated<MuscleGroup>>(step === 'muscles' ? '/muscle-groups' : null, {
    query: { page_size: 100, is_active: true },
  });
  const facets = useApi<Facets>(step === 'muscles' ? '/exercises/facets' : null, {
    query: { is_active: true, has_media: true },
  });
  const counts = new Map((facets.data?.muscles ?? []).map((m) => [m.value, m.count]));
  const options = (muscles.data?.items ?? [])
    .filter((m) => (counts.get(m.id) ?? 0) >= 2)
    .sort((a, b) => a.name.localeCompare(b.name));

  const toggle = (id: string) =>
    setChosen((list) => (list.includes(id) ? list.filter((m) => m !== id) : list.length < MAX_MUSCLES ? [...list, id] : list));

  const suggest = async () => {
    setLoading(true);
    setError(null);
    try {
      const results = await Promise.all(
        chosen.map((muscle_group_id) =>
          api<Paginated<Exercise>>('/exercises', {
            query: { muscle_group_id, has_media: true, is_active: true, page_size: 100 },
          }),
        ),
      );
      const byMuscle = results.map((r) => r.items);
      setPools(byMuscle);
      setPicks(suggestDay(goal, level, byMuscle));
      setStep('preview');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const add = async () => {
    setSaving(true);
    try {
      picks.forEach(rememberExercise);
      await onAddSuggested(picks.map((exercise) => ({ exercise, prescription: prescribe(goal, level, exercise) })));
      onClose();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const titles: Record<Step, [string, string]> = {
    choose: [`Plan ${dayTitle}`, 'Let LiftAndPlate suggest a workout for your goal, or pick the exercises yourself.'],
    muscles: ['Which muscles today?', `Pick up to ${MAX_MUSCLES}. Exercises match your ${titleCase(goal).toLowerCase()} goal and ${level} level.`],
    preview: ['Your suggested workout', `Sets, reps and rest are set for ${titleCase(goal).toLowerCase()}. You can change them after adding.`],
  };

  return (
    <Dialog open={open} onClose={onClose} title={titles[step][0]} description={titles[step][1]} wide={step !== 'choose'}>
      {step === 'choose' && (
        <div className="grid gap-3 sm:grid-cols-2">
          <button
            onClick={() => setStep('muscles')}
            className="flex flex-col items-start gap-2 rounded-card border border-accent bg-accent-soft p-4 text-left transition-colors hover:bg-accent/20"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-accent text-accent-fg">
              <MagicWand size={20} weight="fill" />
            </span>
            <span className="text-[15px] font-semibold">Suggest exercises for me</span>
            <span className="text-sm text-muted">Choose the muscles; LiftAndPlate builds the list for your goal and level.</span>
          </button>
          <button
            onClick={() => {
              onClose();
              onPickManually();
            }}
            className="flex flex-col items-start gap-2 rounded-card border border-line bg-surface p-4 text-left transition-colors hover:bg-sunken"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-sunken text-ink">
              <HandPointing size={20} weight="fill" />
            </span>
            <span className="text-[15px] font-semibold">I&apos;ll pick them myself</span>
            <span className="text-sm text-muted">Search the library and add exactly what you want.</span>
          </button>
        </div>
      )}

      {step === 'muscles' && (
        <div>
          {muscles.loading || facets.loading ? (
            <div className="flex flex-wrap gap-2">
              {Array.from({ length: 10 }).map((_, i) => (
                <Skeleton key={i} className="h-9 w-24 rounded-full" />
              ))}
            </div>
          ) : (
            <div className="flex flex-wrap gap-2" role="group" aria-label="Muscles">
              {options.map((m) => {
                const on = chosen.includes(m.id);
                return (
                  <button
                    key={m.id}
                    onClick={() => toggle(m.id)}
                    aria-pressed={on}
                    disabled={!on && chosen.length >= MAX_MUSCLES}
                    className={cn(
                      'h-9 rounded-full border px-4 text-sm font-medium transition-colors disabled:opacity-40',
                      on ? 'border-accent bg-accent text-accent-fg' : 'border-line bg-surface text-ink hover:border-faint',
                    )}
                  >
                    {m.name}
                  </button>
                );
              })}
            </div>
          )}
          {error && <p className="mt-3 text-sm text-danger">{error}</p>}
          <div className="mt-6 flex justify-between gap-2">
            <Button variant="ghost" onClick={() => setStep('choose')}>
              <ArrowLeft size={16} />
              Back
            </Button>
            <Button onClick={suggest} loading={loading} disabled={chosen.length === 0}>
              <MagicWand size={16} weight="fill" />
              Suggest exercises
            </Button>
          </div>
        </div>
      )}

      {step === 'preview' && (
        <div>
          {picks.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted">No exercises at your level for these muscles yet. Try other muscles.</p>
          ) : (
            <ul className="flex flex-col gap-1">
              {picks.map((exercise) => {
                const p = prescribe(goal, level, exercise);
                return (
                  <li key={exercise.id} className="flex items-center gap-3 rounded-control p-2">
                    <MiniThumb exercise={exercise} className="h-12 w-12" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[15px] font-medium">{text.name(exercise)}</p>
                      <p className="truncate text-[13px] text-muted">
                        {p.sets} × {p.reps} · {rest(p.rest_seconds)} · {exercise.primary_muscles[0]?.name}
                      </p>
                    </div>
                    <button
                      onClick={() => setPicks((list) => list.filter((e) => e.id !== exercise.id))}
                      className="flex h-8 w-8 items-center justify-center rounded-control text-muted hover:bg-sunken hover:text-ink"
                      aria-label={`Remove ${exercise.name}`}
                    >
                      <X size={15} />
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
          {error && <p className="mt-3 text-sm text-danger">{error}</p>}
          <div className="mt-6 flex flex-wrap justify-between gap-2">
            <Button variant="ghost" onClick={() => setStep('muscles')}>
              <ArrowLeft size={16} />
              Muscles
            </Button>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => pools && setPicks(suggestDay(goal, level, pools))}>
                <ArrowClockwise size={16} />
                Suggest again
              </Button>
              <Button onClick={add} loading={saving} disabled={picks.length === 0}>
                Add {picks.length} exercise{picks.length === 1 ? '' : 's'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </Dialog>
  );
}
