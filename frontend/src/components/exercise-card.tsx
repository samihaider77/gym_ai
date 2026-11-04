'use client';

import Link from 'next/link';
import type { Exercise } from '@/lib/types';
import { titleCase } from '@/lib/utils';
import { ExerciseThumb } from './exercise-media';
import { useExerciseText } from '@/lib/i18n';

export function ExerciseCard({ exercise }: { exercise: Exercise }) {
  const text = useExerciseText();
  const muscle = exercise.primary_muscles[0]?.name;
  return (
    <Link
      href={`/exercises/${exercise.id}`}
      className="group flex flex-col overflow-hidden rounded-card border border-line bg-surface shadow-card transition-[transform,box-shadow,border-color] duration-300 ease-out hover:-translate-y-0.5 hover:border-faint/50 hover:shadow-lift"
    >
      <ExerciseThumb exercise={exercise} className="border-b border-line" />
      <div className="flex flex-1 flex-col gap-1 p-3.5">
        <h3 className="line-clamp-2 text-[15px] font-medium leading-snug group-hover:text-accent">{text.name(exercise)}</h3>
        <p className="mt-auto truncate text-[13px] text-muted">
          {[muscle, exercise.equipment?.name, titleCase(exercise.difficulty_level)].filter(Boolean).join(', ')}
        </p>
      </div>
    </Link>
  );
}

export function ExerciseCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-card border border-line bg-surface">
      <div className="aspect-square animate-pulse bg-sunken" />
      <div className="space-y-2 p-3.5">
        <div className="h-4 w-3/4 animate-pulse rounded bg-sunken" />
        <div className="h-3 w-1/2 animate-pulse rounded bg-sunken" />
      </div>
    </div>
  );
}
