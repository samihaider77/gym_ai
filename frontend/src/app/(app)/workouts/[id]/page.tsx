'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { ArrowDown, ArrowLeft, ArrowUp, Barbell, Lightning, Plus, Trash } from '@phosphor-icons/react';
import { MiniThumb } from '@/components/exercise-media';
import { ExercisePicker } from '@/components/exercise-picker';
import { PageHeader } from '@/components/page';
import { Button } from '@/components/ui/button';
import { Dialog } from '@/components/ui/dialog';
import { Badge, EmptyState, ErrorNotice, Skeleton } from '@/components/ui/feedback';
import { useToast } from '@/components/ui/toast';
import { api } from '@/lib/api';
import type { Exercise, WorkoutDay, WorkoutExercise, WorkoutPlan, WorkoutSession } from '@/lib/types';
import { useApi } from '@/lib/use-api';
import { useExercises } from '@/lib/use-exercises';
import { cn, titleCase } from '@/lib/utils';
import { useExerciseText } from '@/lib/i18n';

function NumberStepper({ value, onChange, label, min = 1, max = 100 }: { value: number; onChange: (v: number) => void; label: string; min?: number; max?: number }) {
  return (
    <div className="flex items-center rounded-control border border-line" role="group" aria-label={label}>
      <button
        onClick={() => onChange(Math.max(min, value - 1))}
        className="h-8 w-8 text-muted transition-colors hover:text-ink disabled:opacity-40"
        disabled={value <= min}
        aria-label={`Fewer ${label}`}
      >
        -
      </button>
      <span className="w-8 text-center text-sm font-medium tabular">{value}</span>
      <button
        onClick={() => onChange(Math.min(max, value + 1))}
        className="h-8 w-8 text-muted transition-colors hover:text-ink disabled:opacity-40"
        disabled={value >= max}
        aria-label={`More ${label}`}
      >
        +
      </button>
    </div>
  );
}

function DayEditor({ day, onStart, starting }: { day: WorkoutDay; onStart: () => void; starting: boolean }) {
  const toast = useToast();
  const reduce = useReducedMotion();
  const list = useApi<{ items: WorkoutExercise[] }>(`/workout-days/${day.id}/exercises`);
  const items = [...(list.data?.items ?? [])].sort((a, b) => a.order_index - b.order_index);
  const exercise = useExercises(items.map((i) => i.exercise_id));
  const [picking, setPicking] = useState(false);
  const text = useExerciseText();
  const [title, setTitle] = useState(day.title);

  useEffect(() => setTitle(day.title), [day.title]);

  const patchLocal = (id: string, changes: Partial<WorkoutExercise>) =>
    list.setData((data) => data && { ...data, items: data.items.map((i) => (i.id === id ? { ...i, ...changes } : i)) });

  const update = async (item: WorkoutExercise, changes: Partial<WorkoutExercise>) => {
    patchLocal(item.id, changes);
    try {
      await api(`/workout-exercises/${item.id}`, { method: 'PUT', body: changes });
    } catch (err) {
      toast((err as Error).message, 'error');
      list.reload();
    }
  };

  const remove = async (item: WorkoutExercise) => {
    list.setData((data) => data && { ...data, items: data.items.filter((i) => i.id !== item.id) });
    try {
      await api(`/workout-exercises/${item.id}`, { method: 'DELETE' });
    } catch (err) {
      toast((err as Error).message, 'error');
      list.reload();
    }
  };

  const move = async (index: number, direction: -1 | 1) => {
    const reordered = [...items];
    const [moved] = reordered.splice(index, 1);
    reordered.splice(index + direction, 0, moved);
    const payload = reordered.map((item, order_index) => ({ id: item.id, order_index }));
    list.setData((data) => data && { ...data, items: reordered.map((item, order_index) => ({ ...item, order_index })) });
    try {
      await api('/workout-exercises/reorder', { method: 'PATCH', body: { items: payload } });
    } catch (err) {
      toast((err as Error).message, 'error');
      list.reload();
    }
  };

  // Read the latest list each time so several quick picks never reuse an index.
  const latest = useRef(items);
  latest.current = items;
  const nextIndex = () => latest.current.reduce((max, i) => Math.max(max, i.order_index + 1), 0);

  const add = async (picked: Exercise) => {
    const created = await api<WorkoutExercise>(`/workout-days/${day.id}/exercises`, {
      method: 'POST',
      body: { exercise_id: picked.id, order_index: nextIndex(), sets: 3, reps: 10 },
    });
    list.setData((data) => ({ items: [...(data?.items ?? []), created] }));
  };

  const rename = async () => {
    const next = title.trim();
    if (!next || next === day.title) return setTitle(day.title);
    try {
      await api(`/workout-days/${day.id}`, { method: 'PUT', body: { title: next } });
      day.title = next;
    } catch (err) {
      toast((err as Error).message, 'error');
      setTitle(day.title);
    }
  };

  return (
    <div>
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={rename}
          onKeyDown={(e) => e.key === 'Enter' && (e.target as HTMLInputElement).blur()}
          aria-label="Day name"
          maxLength={100}
          className="-ml-2 h-10 rounded-control border border-transparent bg-transparent px-2 text-lg font-semibold tracking-tight transition-colors hover:border-line focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/25"
        />
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setPicking(true)}>
            <Plus size={16} weight="bold" />
            Add exercises
          </Button>
          <Button onClick={onStart} loading={starting} disabled={items.length === 0}>
            <Lightning size={16} weight="fill" />
            Start
          </Button>
        </div>
      </div>

      {list.error ? (
        <ErrorNotice message={list.error} onRetry={list.reload} />
      ) : list.loading && !list.data ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-[76px] rounded-card" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={<Barbell size={22} />}
          title="Nothing planned for this day"
          body="Add exercises from the library. You can change sets and reps after."
          action={<Button onClick={() => setPicking(true)}>Add exercises</Button>}
        />
      ) : (
        <ul className="flex flex-col gap-2">
          <AnimatePresence initial={false}>
            {items.map((item, index) => {
              const ex = exercise(item.exercise_id);
              return (
                <motion.li
                  key={item.id}
                  layout={!reduce}
                  initial={reduce ? false : { opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, transition: { duration: 0.15 } }}
                  transition={{ type: 'spring', stiffness: 500, damping: 40 }}
                  className="flex flex-col gap-3 rounded-card border border-line bg-surface p-3 sm:flex-row sm:items-center"
                >
                  <Link href={`/exercises/${item.exercise_id}`} className="flex min-w-0 flex-1 items-center gap-3">
                    <MiniThumb exercise={ex} className="h-12 w-12" />
                    <div className="min-w-0">
                      <p className="truncate text-[15px] font-medium hover:text-accent">{ex ? text.name(ex) : 'Loading...'}</p>
                      <p className="truncate text-[13px] text-muted">{ex?.primary_muscles[0]?.name ?? ' '}</p>
                    </div>
                  </Link>
                  <div className="flex items-center justify-between gap-3 sm:justify-end">
                    <div className="flex items-center gap-2 text-[13px] text-muted">
                      <NumberStepper label="sets" value={item.sets} max={20} onChange={(sets) => update(item, { sets })} />
                      <span>x</span>
                      <NumberStepper label="reps" value={item.reps} onChange={(reps) => update(item, { reps })} />
                    </div>
                    <div className="flex">
                      <button onClick={() => move(index, -1)} disabled={index === 0} className="h-8 w-8 rounded-control text-muted hover:bg-sunken hover:text-ink disabled:opacity-30" aria-label="Move up">
                        <ArrowUp size={15} className="mx-auto" />
                      </button>
                      <button onClick={() => move(index, 1)} disabled={index === items.length - 1} className="h-8 w-8 rounded-control text-muted hover:bg-sunken hover:text-ink disabled:opacity-30" aria-label="Move down">
                        <ArrowDown size={15} className="mx-auto" />
                      </button>
                      <button onClick={() => remove(item)} className="h-8 w-8 rounded-control text-muted hover:bg-danger/10 hover:text-danger" aria-label="Remove exercise">
                        <Trash size={15} className="mx-auto" />
                      </button>
                    </div>
                  </div>
                </motion.li>
              );
            })}
          </AnimatePresence>
        </ul>
      )}

      <ExercisePicker open={picking} onClose={() => setPicking(false)} onPick={add} title={`Add to ${title}`} />
    </div>
  );
}

export default function PlanPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const toast = useToast();
  const plan = useApi<WorkoutPlan>(`/workout-plans/${params.id}`);
  const days = useApi<{ items: WorkoutDay[] }>(`/workout-plans/${params.id}/days`);
  const sorted = [...(days.data?.items ?? [])].sort((a, b) => a.day_number - b.day_number);
  const [activeDay, setActiveDay] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const current = sorted.find((d) => d.id === activeDay) ?? sorted[0];

  const addDay = async () => {
    const next = (sorted[sorted.length - 1]?.day_number ?? 0) + 1;
    try {
      const day = await api<WorkoutDay>(`/workout-plans/${params.id}/days`, {
        method: 'POST',
        body: { day_number: next, title: `Day ${next}` },
      });
      days.setData((data) => ({ items: [...(data?.items ?? []), day] }));
      setActiveDay(day.id);
    } catch (err) {
      toast((err as Error).message, 'error');
    }
  };

  const start = async () => {
    if (!current) return;
    setStarting(true);
    try {
      const session = await api<WorkoutSession>('/workout-sessions/start', {
        method: 'POST',
        body: { workout_plan_id: params.id, workout_day_id: current.id },
      });
      router.push(`/sessions/${session.id}`);
    } catch (err) {
      toast((err as Error).message, 'error');
      setStarting(false);
    }
  };

  const archivePlan = async () => {
    setDeleting(true);
    try {
      await api(`/workout-plans/${params.id}`, { method: 'DELETE' });
      toast('Plan archived');
      router.replace('/workouts');
    } catch (err) {
      toast((err as Error).message, 'error');
      setDeleting(false);
    }
  };

  const back = (
    <Link href="/workouts" className="inline-flex items-center gap-1.5 text-sm font-medium text-muted transition-colors hover:text-ink">
      <ArrowLeft size={16} />
      All plans
    </Link>
  );

  if (plan.error) {
    return (
      <>
        <PageHeader title="Workout plan" back={back} />
        <ErrorNotice message={plan.error} onRetry={plan.reload} />
      </>
    );
  }

  return (
    <>
      <PageHeader
        back={back}
        title={plan.data?.name ?? ' '}
        description={
          plan.data && (
            <span className="flex flex-wrap gap-1.5 pt-1">
              <Badge tone="accent">{titleCase(plan.data.goal)}</Badge>
              <Badge>{titleCase(plan.data.difficulty)}</Badge>
              <Badge>{plan.data.duration_weeks} weeks</Badge>
            </span>
          )
        }
        actions={
          <Button variant="danger" onClick={() => setConfirmDelete(true)}>
            <Trash size={16} />
            Archive
          </Button>
        }
      />

      {days.loading && !days.data ? (
        <Skeleton className="h-10 w-72" />
      ) : (
        <div className="mb-6 flex gap-1.5 overflow-x-auto pb-1 scrollbar-none" role="tablist" aria-label="Training days">
          {sorted.map((day) => (
            <button
              key={day.id}
              role="tab"
              aria-selected={day.id === current?.id}
              onClick={() => setActiveDay(day.id)}
              className={cn(
                'relative h-9 shrink-0 rounded-full px-4 text-sm font-medium transition-colors',
                day.id === current?.id ? 'text-accent-fg' : 'text-muted hover:bg-sunken hover:text-ink',
              )}
            >
              {day.id === current?.id && (
                <motion.span layoutId="day-pill" className="absolute inset-0 rounded-full bg-accent" transition={{ type: 'spring', stiffness: 500, damping: 40 }} />
              )}
              <span className="relative">Day {day.day_number}</span>
            </button>
          ))}
          <button
            onClick={addDay}
            className="flex h-9 shrink-0 items-center gap-1.5 rounded-full border border-dashed border-line px-3.5 text-sm font-medium text-muted transition-colors hover:border-faint hover:text-ink"
          >
            <Plus size={14} weight="bold" />
            Add day
          </button>
        </div>
      )}

      {current ? (
        <DayEditor key={current.id} day={current} onStart={start} starting={starting} />
      ) : (
        days.data && (
          <EmptyState
            icon={<Barbell size={22} />}
            title="This plan has no days"
            body="Add a training day to start filling it with exercises."
            action={<Button onClick={addDay}>Add a day</Button>}
          />
        )
      )}

      <Dialog open={confirmDelete} onClose={() => setConfirmDelete(false)} title="Archive this plan?" description="It disappears from your plans. Your past workouts stay in your history.">
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setConfirmDelete(false)}>
            Keep plan
          </Button>
          <Button onClick={archivePlan} loading={deleting} className="bg-danger hover:bg-danger/90">
            Archive plan
          </Button>
        </div>
      </Dialog>
    </>
  );
}
