import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { Exercise, ExerciseMedia } from './types';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function titleCase(value: string | null | undefined) {
  if (!value) return '';
  return value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatDate(value: string, options: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' }) {
  return new Date(value).toLocaleDateString(undefined, options);
}

export function formatNumber(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined) return '-';
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits });
}

const HIDDEN = new Set(['failed', 'deprecated', 'rejected']);

/** Visible media for an exercise, primary first, then videos before stills. */
export function visibleMedia(exercise: Pick<Exercise, 'media'>): ExerciseMedia[] {
  return [...(exercise.media ?? [])]
    .filter((m) => m.media_url && !HIDDEN.has(m.status.toLowerCase()))
    .sort(
      (a, b) =>
        Number(b.is_primary) - Number(a.is_primary) ||
        Number(b.media_type === 'video') - Number(a.media_type === 'video'),
    );
}

export function primaryMedia(exercise: Pick<Exercise, 'media'>): ExerciseMedia | null {
  return visibleMedia(exercise)[0] ?? null;
}

export function isVideo(media: ExerciseMedia) {
  return ['video', 'animation', 'mp4', 'webm'].includes(media.media_type);
}

export function greeting(date = new Date()) {
  const hour = date.getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}
