'use client';

import { useEffect, useState } from 'react';
import { Check, MagnifyingGlass, Plus } from '@phosphor-icons/react';
import { Dialog } from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/feedback';
import type { Exercise, Paginated } from '@/lib/types';
import { useApi } from '@/lib/use-api';
import { rememberExercise } from '@/lib/use-exercises';
import { cn } from '@/lib/utils';
import { MiniThumb } from './exercise-media';
import { useExerciseText } from '@/lib/i18n';

/** Searchable list for adding exercises to a training day. Stays open so several can be added in a row. */
export function ExercisePicker({
  open,
  onClose,
  onPick,
  title,
}: {
  open: boolean;
  onClose: () => void;
  onPick: (exercise: Exercise) => Promise<void>;
  title: string;
}) {
  const [term, setTerm] = useState('');
  const [search, setSearch] = useState('');
  const [added, setAdded] = useState<string[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const text = useExerciseText();

  useEffect(() => {
    const id = setTimeout(() => setSearch(term.trim()), 250);
    return () => clearTimeout(id);
  }, [term]);
  useEffect(() => {
    if (!open) {
      setAdded([]);
      setTerm('');
    }
  }, [open]);

  const list = useApi<Paginated<Exercise>>(
    open ? '/exercises' : null,
    { query: { search, page_size: 30, is_active: true, has_media: true } },
    [search],
  );

  const pick = async (exercise: Exercise) => {
    setBusy(exercise.id);
    rememberExercise(exercise);
    try {
      await onPick(exercise);
      setAdded((list) => [...list, exercise.id]);
    } finally {
      setBusy(null);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} title={title} description="Pick as many as you like. Tap an exercise to add it." wide>
      <div className="relative mb-4">
        <MagnifyingGlass size={18} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
        <input
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          placeholder="Search exercises"
          aria-label="Search exercises"
          className="h-11 w-full rounded-control border border-line bg-surface pl-10 pr-3 text-[15px] placeholder:text-faint focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/25"
        />
      </div>
      <div className="flex flex-col gap-1">
        {list.loading && !list.data
          ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-14" />)
          : list.data?.items.length === 0
            ? <p className="py-8 text-center text-sm text-muted">No exercises match “{search}”.</p>
            : list.data?.items.map((exercise) => {
                const done = added.includes(exercise.id);
                return (
                  <button
                    key={exercise.id}
                    onClick={() => pick(exercise)}
                    disabled={busy === exercise.id}
                    className="group flex items-center gap-3 rounded-control p-2 text-left transition-colors hover:bg-sunken"
                  >
                    <MiniThumb exercise={exercise} className="h-12 w-12" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[15px] font-medium">{text.name(exercise)}</p>
                      <p className="truncate text-[13px] text-muted">
                        {[exercise.primary_muscles[0]?.name, exercise.equipment?.name].filter(Boolean).join(', ')}
                      </p>
                    </div>
                    <span
                      className={cn(
                        'flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-colors',
                        done ? 'bg-success/15 text-success' : 'bg-sunken text-muted group-hover:bg-accent group-hover:text-accent-fg',
                      )}
                    >
                      {busy === exercise.id ? (
                        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-r-transparent" />
                      ) : done ? (
                        <Check size={16} weight="bold" />
                      ) : (
                        <Plus size={16} weight="bold" />
                      )}
                    </span>
                  </button>
                );
              })}
      </div>
    </Dialog>
  );
}
