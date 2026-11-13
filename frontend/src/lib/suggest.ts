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

/**
 * The movement an exercise trains, from its name: "Decline Bench Press" and "Machine Bench Press" are both a
 * press, "Cable Crossover" and "Pec Deck" are both a fly. A suggested day uses each movement once. The order
 * matters: the first match wins ("Leg Curl" is a leg curl, not a biceps curl). `compound` says whether the
 * movement uses several joints; it overrides the library's flag, which is wrong for some exercises.
 */
const MOVEMENTS: { key: string; test: RegExp; compound: boolean }[] = [
  { key: 'leg-curl', test: /\bleg curl|hamstring curl|lying curl|seated curl\b/i, compound: false },
  { key: 'leg-extension', test: /\bleg extension/i, compound: false },
  { key: 'calf', test: /\bcalf|calves\b/i, compound: false },
  { key: 'fly', test: /\bfl(y|ye|yes|ies)\b|cable crossover|pec deck|butterfly/i, compound: false },
  { key: 'pullover', test: /pullover|straight-?arm/i, compound: false },
  { key: 'lateral-raise', test: /lateral raise|side raise|\by raise/i, compound: false },
  { key: 'front-raise', test: /front raise/i, compound: false },
  { key: 'rear-delt', test: /rear delt|reverse fly|face pull/i, compound: false },
  { key: 'shrug', test: /shrug/i, compound: false },
  { key: 'triceps', test: /pushdown|push-down|triceps?\b.*kickback|triceps? press|skull|triceps? extension|overhead extension|french press|tate press|jm press/i, compound: false },
  { key: 'curl', test: /\bcurl/i, compound: false },
  { key: 'wrist', test: /wrist/i, compound: false },
  { key: 'abs', test: /crunch|sit-?up|leg raise|knee raise|plank|rollout|russian twist|hollow|v-up|mountain climber|bicycle/i, compound: false },
  { key: 'hip-thrust', test: /hip thrust|glute bridge|bridge/i, compound: true },
  { key: 'abduction', test: /abduct|adduct|clamshell|fire hydrant|donkey kick|kickback/i, compound: false },
  { key: 'dip', test: /\bdips?\b/i, compound: true },
  { key: 'push-up', test: /push-?ups?|press-?ups?/i, compound: true },
  { key: 'pull-up', test: /pull-?ups?|chin-?ups?|pulldown|pull-down/i, compound: true },
  { key: 'row', test: /\brows?\b|rowing/i, compound: true },
  { key: 'deadlift', test: /deadlift|rdl|good morning|rack pull/i, compound: true },
  { key: 'lunge', test: /lunge|split squat|step-?up/i, compound: true },
  { key: 'squat', test: /squat|leg press|hack/i, compound: true },
  { key: 'overhead-press', test: /overhead press|shoulder press|military|arnold|push press/i, compound: true },
  { key: 'press', test: /press/i, compound: true },
];

// Stretches, foam rolling and jumps are not strength movements: no movement, so the library's label is used.
const SKIP = /stretch|smr|foam|jump|hop|bound/i;

function movement(exercise: Exercise) {
  return SKIP.test(exercise.name) ? undefined : MOVEMENTS.find((m) => m.test.test(exercise.name));
}

/** Several joints at once (presses, rows, squats) rather than one (curls, flyes, raises). */
export function isCompound(exercise: Exercise): boolean {
  return movement(exercise)?.compound ?? exercise.is_compound;
}

export function prescribe(goal: string, level: string, exercise: Exercise): Prescription {
  const table = PRESCRIPTIONS[goal] ?? PRESCRIPTIONS.general_fitness;
  const base = isCompound(exercise) ? table.compound : table.isolation;
  // Beginners start with one set less: same movements, less volume while they learn them.
  return level === 'beginner' ? { ...base, sets: Math.max(2, base.sets - 1) } : base;
}

// Niche variations and combined moves ("Front Raise And Pullover") rank below the staple version.
const ODD_VARIANT = /\b(with|on|and|ball|bosu|twist|band|bands|stability|swiss|single|one|alternating|kneeling|feet|guillotine|neck)\b/i;
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
  if (isCompound(exercise)) score += 1;
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
 * Picks a day of exercises for the chosen muscles: no moves above the plan's level, a different movement for
 * each pick (one press, one fly, one dip, not three bench presses), staple versions first, compound lifts before
 * isolation work. Shuffled, so "Suggest again" gives a new mix.
 */
export function suggestDay(goal: string, level: string, byMuscle: Exercise[][]): Exercise[] {
  const maxLevel = LEVELS.indexOf(level) < 0 ? 1 : LEVELS.indexOf(level);
  const total = DAY_SIZE[goal] ?? 5;
  const perMuscle = Math.max(2, Math.round(total / Math.max(1, byMuscle.length)));
  const picked: Exercise[] = [];
  const usedMovements = new Set<string>();
  for (const pool of byMuscle) {
    const fitting = pool.filter((e) => LEVELS.indexOf(e.difficulty_level) <= maxLevel && !picked.some((p) => p.id === e.id));
    // Staple movements first, shuffled within the same score so "Suggest again" still varies.
    const ranked = shuffle(fitting).sort((a, b) => staple(goal, b) - staple(goal, a));
    const mine: Exercise[] = [];
    const take = (exercise: Exercise) => {
      mine.push(exercise);
      usedMovements.add(movement(exercise)?.key ?? exercise.id);
    };
    const best = ranked.length ? staple(goal, ranked[0]) : 0;
    const staples = ranked.filter((e) => staple(goal, e) >= best - 3);
    const uses = (e: Exercise) => mine.filter((m) => (movement(m)?.key ?? m.id) === (movement(e)?.key ?? e.id)).length;
    // 1) one staple exercise per movement; 2) a second staple of a movement (two presses beat an odd variation);
    // 3) anything left, if a muscle still has too few exercises.
    for (const exercise of staples) {
      if (mine.length >= perMuscle) break;
      if (!usedMovements.has(movement(exercise)?.key ?? exercise.id)) take(exercise);
    }
    for (const exercise of staples) {
      if (mine.length >= perMuscle) break;
      if (!mine.includes(exercise) && uses(exercise) < 2) take(exercise);
    }
    for (const exercise of ranked) {
      if (mine.length >= perMuscle) break;
      if (!mine.includes(exercise)) take(exercise);
    }
    // Compound lifts first in the day.
    mine.sort((a, b) => Number(isCompound(b)) - Number(isCompound(a)));
    picked.push(...mine);
  }
  return picked;
}
