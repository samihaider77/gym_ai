import type { Exercise } from './types';

/** Sets, reps and rest for one exercise, chosen from the plan's goal. */
export type Prescription = { sets: number; reps: number; rest_seconds: number };

// Common gym guidance per goal: heavier and fewer reps for strength, 8-12 for size, short rests and higher reps
// for fat loss and endurance. Compound lifts get an extra set where it matters.
const PRESCRIPTIONS: Record<string, { compound: Prescription; isolation: Prescription }> = {
  muscle_gain: { compound: { sets: 4, reps: 8, rest_seconds: 120 }, isolation: { sets: 3, reps: 12, rest_seconds: 60 } },
  strength: { compound: { sets: 5, reps: 5, rest_seconds: 180 }, isolation: { sets: 3, reps: 8, rest_seconds: 120 } },
  fat_loss: { compound: { sets: 3, reps: 12, rest_seconds: 45 }, isolation: { sets: 3, reps: 15, rest_seconds: 30 } },
  endurance: { compound: { sets: 3, reps: 15, rest_seconds: 45 }, isolation: { sets: 3, reps: 20, rest_seconds: 30 } },
  general_fitness: { compound: { sets: 3, reps: 10, rest_seconds: 90 }, isolation: { sets: 3, reps: 12, rest_seconds: 60 } },
  rehab: { compound: { sets: 2, reps: 12, rest_seconds: 90 }, isolation: { sets: 2, reps: 15, rest_seconds: 60 } },
};

/** How many exercises a day gets for each goal. */
const DAY_SIZE: Record<string, number> = {
  muscle_gain: 6, strength: 5, fat_loss: 6, endurance: 6, general_fitness: 5, rehab: 4,
};

const LEVELS = ['beginner', 'intermediate', 'advanced'];

export function prescribe(goal: string, level: string, exercise: Exercise): Prescription {
  const table = PRESCRIPTIONS[goal] ?? PRESCRIPTIONS.general_fitness;
  const base = exercise.is_compound ? table.compound : table.isolation;
  // Beginners start with one set less: same movements, less volume while they learn them.
  return level === 'beginner' ? { ...base, sets: Math.max(2, base.sets - 1) } : base;
}

const ODD_VARIANT = /\b(with|on|ball|bosu|twist|band|bands|stability|swiss|single|one|alternating|kneeling|feet|guillotine|pullover)\b/i;
const LOADED = /barbell|dumbbell|cable|machine|smith|e-z|ez|kettlebell|lever/i;

/**
 * Higher for the staple version of a movement ("Barbell Bench Press") than for a niche variation ("Incline
 * Dumbbell Flyes - With A Twist"). For size and strength goals, loaded lifts beat bodyweight ones.
 */
function staple(goal: string, exercise: Exercise): number {
  const name = exercise.name;
  let score = 10 - Math.max(0, name.split(/\s+/).length - 3);
  if (/[-–(/]/.test(name)) score -= 3;
  if (ODD_VARIANT.test(name)) score -= 3;
  if ((goal === 'muscle_gain' || goal === 'strength') && !LOADED.test(`${name} ${exercise.equipment?.name ?? ''}`)) score -= 3;
  if (exercise.is_compound) score += 1;
  return score;
}

function shuffle<T>(items: T[]): T[] {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

/**
 * Picks a day of exercises for the chosen muscles: no moves above the plan's level, compound lifts first, then
 * isolation work, spreading the picks over different equipment. Shuffled, so "Suggest again" gives a new mix.
 */
export function suggestDay(goal: string, level: string, byMuscle: Exercise[][]): Exercise[] {
  const maxLevel = LEVELS.indexOf(level) < 0 ? 1 : LEVELS.indexOf(level);
  const total = DAY_SIZE[goal] ?? 5;
  const perMuscle = Math.max(2, Math.round(total / Math.max(1, byMuscle.length)));
  const picked: Exercise[] = [];
  for (const pool of byMuscle) {
    const fitting = pool.filter((e) => LEVELS.indexOf(e.difficulty_level) <= maxLevel && !picked.some((p) => p.id === e.id));
    // Staple movements first (shuffled within the same score, so "Suggest again" still varies), then compounds
    // before isolation work in the final order.
    const ranked = shuffle(fitting).sort((a, b) => staple(goal, b) - staple(goal, a));
    const ordered = [...ranked.filter((e) => e.is_compound), ...ranked.filter((e) => !e.is_compound)];
    const mine: Exercise[] = [];
    // First pass: one exercise per piece of equipment, among the staple movements only (so variety never pulls
    // in a niche variation); second pass fills any gap in staple order.
    const best = ranked.length ? staple(goal, ranked[0]) : 0;
    for (const exercise of ordered.filter((e) => staple(goal, e) >= best - 2)) {
      if (mine.length >= perMuscle) break;
      if (!mine.some((m) => m.equipment_id === exercise.equipment_id)) mine.push(exercise);
    }
    for (const exercise of ranked) {
      if (mine.length >= perMuscle) break;
      if (!mine.includes(exercise)) mine.push(exercise);
    }
    // Compound lifts first in the day, as the ordered list had them.
    mine.sort((a, b) => Number(b.is_compound) - Number(a.is_compound));
    picked.push(...mine);
  }
  return picked;
}
