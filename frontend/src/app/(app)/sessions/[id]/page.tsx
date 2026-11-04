'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AnimatePresence, motion } from 'motion/react';
import { ArrowLeft, Check, Timer, X } from '@phosphor-icons/react';
import { MiniThumb } from '@/components/exercise-media';
import { PageHeader, Panel, Reveal } from '@/components/page';
import { Button } from '@/components/ui/button';
import { Dialog } from '@/components/ui/dialog';
import { Badge, ErrorNotice, Skeleton } from '@/components/ui/feedback';
import { Field, Textarea } from '@/components/ui/field';
import { useToast } from '@/components/ui/toast';
import { api } from '@/lib/api';
import type { WorkoutExercise, WorkoutLog, WorkoutSession } from '@/lib/types';
import { useApi } from '@/lib/use-api';
import { useExercises } from '@/lib/use-exercises';
import { cn, formatDate, formatNumber } from '@/lib/utils';
import { useExerciseText } from '@/lib/i18n';

function Elapsed({ since }: { since: string }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const total = Math.max(0, Math.floor((now - new Date(since).getTime()) / 1000));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return (
    <span className="tabular">
      {h > 0 ? `${h}:` : ''}
      {String(m).padStart(h > 0 ? 2 : 1, '0')}:{String(s).padStart(2, '0')}
    </span>
  );
}

function RestTimer({ seconds, onDone }: { seconds: number; onDone: () => void }) {
  const [left, setLeft] = useState(seconds);
  useEffect(() => {
    if (left <= 0) {
      onDone();
      return;
    }
    const id = setTimeout(() => setLeft((v) => v - 1), 1000);
    return () => clearTimeout(id);
  }, [left, onDone]);
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 16 }}
      transition={{ type: 'spring', stiffness: 420, damping: 36 }}
      className="fixed inset-x-4 bottom-20 z-30 mx-auto flex max-w-sm items-center gap-3 rounded-full border border-line bg-surface py-2 pl-4 pr-2 shadow-lift lg:bottom-6"
      role="status"
    >
      <Timer size={18} className="text-accent" />
      <span className="flex-1 text-sm font-medium">
        Rest <span className="tabular">{Math.floor(left / 60)}:{String(left % 60).padStart(2, '0')}</span>
      </span>
      <Button size="sm" variant="ghost" onClick={() => setLeft((v) => v + 15)}>
        +15s
      </Button>
      <Button size="sm" variant="secondary" onClick={onDone}>
        Skip
      </Button>
    </motion.div>
  );
}

type Draft = { reps: string; weight: string };

function ExerciseBlock({
  item,
  logs,
  editable,
  onLog,
}: {
  item: WorkoutExercise;
  logs: WorkoutLog[];
  editable: boolean;
  onLog: (item: WorkoutExercise, set: number, reps: number, weight: number) => Promise<void>;
}) {
  const exercise = useExercises([item.exercise_id])(item.exercise_id);
  const [drafts, setDrafts] = useState<Record<number, Draft>>({});
  const [saving, setSaving] = useState<number | null>(null);
  const text = useExerciseText();
  const done = logs.length;

  const lastWeight = logs[logs.length - 1]?.completed_weight;
  const draftFor = (set: number): Draft =>
    drafts[set] ?? { reps: String(item.reps), weight: lastWeight !== undefined ? String(lastWeight) : item.target_weight ? String(item.target_weight) : '' };

  const setDraft = (set: number, changes: Partial<Draft>) => setDrafts((d) => ({ ...d, [set]: { ...draftFor(set), ...changes } }));

  const log = async (set: number) => {
    const draft = draftFor(set);
    setSaving(set);
    try {
      await onLog(item, set, Number(draft.reps) || 0, Number(draft.weight) || 0);
    } finally {
      setSaving(null);
    }
  };

  const sets = Array.from({ length: Math.max(item.sets, done) }, (_, i) => i + 1);

  return (
    <Panel className="overflow-hidden">
      <div className="flex items-center gap-3 border-b border-line p-3.5">
        <Link href={`/exercises/${item.exercise_id}`} aria-label={exercise ? text.name(exercise) : undefined}>
          <MiniThumb exercise={exercise} className="h-14 w-14 rounded-[10px]" />
        </Link>
        <div className="min-w-0 flex-1">
          <Link href={`/exercises/${item.exercise_id}`} className="block truncate text-[15px] font-semibold hover:text-accent">
            {exercise ? text.name(exercise) : 'Loading...'}
          </Link>
          <p className="text-[13px] text-muted tabular">
            {item.sets} x {item.reps}
            {item.target_weight ? ` at ${item.target_weight} kg` : ''}
          </p>
        </div>
        <Badge tone={done >= item.sets ? 'success' : 'neutral'}>
          {done}/{item.sets}
        </Badge>
      </div>

      <div className="px-3.5 py-2">
        <div className="grid grid-cols-[40px_1fr_1fr_44px] gap-2 px-1 py-1.5 text-xs font-medium text-faint">
          <span>Set</span>
          <span>Reps</span>
          <span>kg</span>
          <span className="sr-only">Done</span>
        </div>
        {sets.map((set) => {
          const logged = logs.find((l) => l.set_number === set);
          const draft = draftFor(set);
          const isNext = !logged && set === done + 1;
          return (
            <div
              key={set}
              className={cn(
                'grid grid-cols-[40px_1fr_1fr_44px] items-center gap-2 rounded-control px-1 py-1 transition-colors duration-300',
                logged && 'bg-success/[0.07]',
              )}
            >
              <span className={cn('text-sm font-medium tabular', isNext ? 'text-ink' : 'text-muted')}>{set}</span>
              {logged ? (
                <>
                  <span className="text-sm tabular">{logged.completed_reps}</span>
                  <span className="text-sm tabular">{formatNumber(logged.completed_weight)}</span>
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-success text-white">
                    <Check size={16} weight="bold" />
                  </span>
                </>
              ) : !editable ? (
                <>
                  <span className="text-sm text-faint">-</span>
                  <span className="text-sm text-faint">-</span>
                  <span className="text-xs text-faint">Skipped</span>
                </>
              ) : (
                <>
                  <input
                    aria-label={`Set ${set} reps`}
                    inputMode="numeric"
                    value={draft.reps}
                    disabled={!editable}
                    onChange={(e) => setDraft(set, { reps: e.target.value.replace(/[^\d]/g, '') })}
                    className="h-9 w-full rounded-control border border-line bg-surface px-2.5 text-sm tabular focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/25 disabled:opacity-50"
                  />
                  <input
                    aria-label={`Set ${set} weight in kg`}
                    inputMode="decimal"
                    placeholder="0"
                    value={draft.weight}
                    disabled={!editable}
                    onChange={(e) => setDraft(set, { weight: e.target.value.replace(/[^\d.]/g, '') })}
                    className="h-9 w-full rounded-control border border-line bg-surface px-2.5 text-sm tabular placeholder:text-faint focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/25 disabled:opacity-50"
                  />
                  <button
                    onClick={() => log(set)}
                    disabled={!editable || saving !== null}
                    aria-label={`Log set ${set}`}
                    className={cn(
                      'flex h-9 w-9 items-center justify-center rounded-full border transition-[background-color,border-color,color,transform] duration-200 active:scale-95 disabled:opacity-40',
                      isNext ? 'border-accent text-accent hover:bg-accent hover:text-accent-fg' : 'border-line text-faint hover:border-faint hover:text-ink',
                    )}
                  >
                    {saving === set ? (
                      <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-r-transparent" />
                    ) : (
                      <Check size={16} weight="bold" />
                    )}
                  </button>
                </>
              )}
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

export default function SessionPage({ params }: { params: { id: string } }) {
  const toast = useToast();
  const session = useApi<WorkoutSession>(`/workout-sessions/${params.id}`);
  const dayId = session.data?.workout_day_id;
  const items = useApi<{ items: WorkoutExercise[] }>(dayId ? `/workout-days/${dayId}/exercises` : null);
  const logs = useApi<{ items: WorkoutLog[] }>(`/workout-sessions/${params.id}/logs`);
  const [resting, setResting] = useState<number | null>(null);
  const [finishing, setFinishing] = useState<'finish' | 'cancel' | null>(null);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const s = session.data;
  const editable = s?.status === 'IN_PROGRESS';
  const ordered = useMemo(() => [...(items.data?.items ?? [])].sort((a, b) => a.order_index - b.order_index), [items.data]);
  const allLogs = logs.data?.items ?? [];
  const totalSets = ordered.reduce((sum, i) => sum + i.sets, 0);
  const volume = allLogs.reduce((sum, l) => sum + l.completed_reps * l.completed_weight, 0);

  const onLog = async (item: WorkoutExercise, set: number, reps: number, weight: number) => {
    try {
      const created = await api<WorkoutLog>(`/workout-sessions/${params.id}/logs`, {
        method: 'POST',
        body: { workout_exercise_id: item.id, set_number: set, completed_reps: reps, completed_weight: weight, is_completed: true },
      });
      logs.setData((data) => ({ items: [...(data?.items ?? []), created] }));
      setResting(item.rest_seconds || 90);
    } catch (err) {
      toast((err as Error).message, 'error');
    }
  };

  const submit = async () => {
    if (!finishing) return;
    setSubmitting(true);
    try {
      const updated = await api<WorkoutSession>(`/workout-sessions/${params.id}/${finishing}`, {
        method: 'POST',
        body: { notes: notes.trim() || null },
      });
      session.setData(updated);
      toast(finishing === 'finish' ? 'Workout saved. Nice work.' : 'Workout cancelled');
      setFinishing(null);
      setResting(null);
    } catch (err) {
      toast((err as Error).message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const back = (
    <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-sm font-medium text-muted transition-colors hover:text-ink">
      <ArrowLeft size={16} />
      Home
    </Link>
  );

  if (session.error) {
    return (
      <>
        <PageHeader title="Workout" back={back} />
        <ErrorNotice message={session.error} onRetry={session.reload} />
      </>
    );
  }

  return (
    <>
      <PageHeader
        back={back}
        title={s ? (editable ? 'Workout in progress' : formatDate(s.started_at, { weekday: 'long', day: 'numeric', month: 'long' })) : ' '}
        description={
          s &&
          (editable ? (
            <span>
              Started {new Date(s.started_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}. Time: <Elapsed since={s.started_at} />
            </span>
          ) : s.status === 'COMPLETED' ? (
            `Completed in ${s.duration_minutes} min`
          ) : (
            'This workout was cancelled'
          ))
        }
        actions={
          editable && (
            <>
              <Button variant="ghost" onClick={() => setFinishing('cancel')}>
                <X size={16} />
                Cancel
              </Button>
              <Button onClick={() => setFinishing('finish')}>
                <Check size={16} weight="bold" />
                Finish
              </Button>
            </>
          )
        }
      />

      <Reveal>
        <Panel className="mb-6 grid grid-cols-3 divide-x divide-line">
          {[
            { label: 'Sets done', value: logs.loading ? null : `${allLogs.length}/${totalSets}` },
            { label: 'Exercises', value: items.loading ? null : String(ordered.length) },
            { label: 'Volume (kg)', value: logs.loading ? null : Math.round(volume).toLocaleString() },
          ].map((stat) => (
            <div key={stat.label} className="px-4 py-4">
              <p className="text-[13px] text-muted">{stat.label}</p>
              {stat.value === null ? <Skeleton className="mt-1.5 h-6 w-12" /> : <p className="mt-0.5 text-xl font-semibold tabular">{stat.value}</p>}
            </div>
          ))}
        </Panel>
      </Reveal>

      {!s || items.loading || logs.loading ? (
        <div className="space-y-4">
          {[0, 1].map((i) => (
            <Skeleton key={i} className="h-56 rounded-card" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-[minmax(0,1fr)] gap-4 lg:grid-cols-2">
          {ordered.map((item, index) => (
            <Reveal key={item.id} delay={Math.min(index, 6) * 0.04}>
              <ExerciseBlock item={item} logs={allLogs.filter((l) => l.workout_exercise_id === item.id).sort((a, b) => a.set_number - b.set_number)} editable={editable} onLog={onLog} />
            </Reveal>
          ))}
        </div>
      )}

      {/* Room so the floating rest timer never covers the last set. */}
      {resting !== null && editable && <div className="h-20" aria-hidden />}
      <AnimatePresence>{resting !== null && editable && <RestTimer key={allLogs.length} seconds={resting} onDone={() => setResting(null)} />}</AnimatePresence>

      <Dialog
        open={finishing !== null}
        onClose={() => setFinishing(null)}
        title={finishing === 'finish' ? 'Finish workout?' : 'Cancel workout?'}
        description={finishing === 'finish' ? `${allLogs.length} of ${totalSets} sets logged.` : 'Sets you logged are kept, but the workout is marked as cancelled.'}
      >
        <div className="flex flex-col gap-4">
          <Field label="Notes" hint="Optional. How did it feel?">
            {(id) => <Textarea id={id} value={notes} onChange={(e) => setNotes(e.target.value)} />}
          </Field>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setFinishing(null)}>
              Keep going
            </Button>
            <Button onClick={submit} loading={submitting} className={finishing === 'cancel' ? 'bg-danger hover:bg-danger/90' : undefined}>
              {finishing === 'finish' ? 'Save workout' : 'Cancel workout'}
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  );
}
