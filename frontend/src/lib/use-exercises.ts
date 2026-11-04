'use client';

import { useEffect, useState } from 'react';
import { api } from './api';
import type { Exercise } from './types';

const cache = new Map<string, Exercise>();

/** Resolves exercise details for a list of ids, sharing one in-memory cache across pages. */
export function useExercises(ids: string[]) {
  const [, force] = useState(0);
  const key = Array.from(new Set(ids)).sort().join(',');

  useEffect(() => {
    const missing = key.split(',').filter((id) => id && !cache.has(id));
    if (!missing.length) return;
    let cancelled = false;
    Promise.all(missing.map((id) => api<Exercise>(`/exercises/${id}`).catch(() => null))).then((results) => {
      results.forEach((exercise) => exercise && cache.set(exercise.id, exercise));
      if (!cancelled) force((n) => n + 1);
    });
    return () => {
      cancelled = true;
    };
  }, [key]);

  return (id: string) => cache.get(id) ?? null;
}

export function rememberExercise(exercise: Exercise) {
  cache.set(exercise.id, exercise);
}
