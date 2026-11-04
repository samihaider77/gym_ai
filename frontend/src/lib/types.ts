export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type User = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
};

export type MuscleSummary = { id: string; name: string; slug: string; body_region: string };
export type EquipmentSummary = { id: string; name: string; slug: string; category: string };

export type ExerciseMedia = {
  id: string;
  media_type: string;
  media_url: string;
  thumbnail_url: string | null;
  poster_url: string | null;
  provider: string | null;
  license: string | null;
  attribution: string | null;
  width: number | null;
  height: number | null;
  duration: number | null;
  camera_angle: string | null;
  format: string | null;
  status: string;
  is_primary: boolean;
};

export type Exercise = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  instructions: string | null;
  name_ur: string | null;
  instructions_ur: string | null;
  difficulty_level: string;
  exercise_type: string;
  force_type: string | null;
  mechanic_type: string | null;
  equipment_id: string | null;
  is_compound: boolean;
  is_active: boolean;
  equipment: EquipmentSummary | null;
  primary_muscles: MuscleSummary[];
  secondary_muscles: MuscleSummary[];
  media: ExerciseMedia[];
};

export type MuscleGroup = MuscleSummary & { description: string | null; is_active: boolean };
export type Equipment = EquipmentSummary & { description: string | null; is_active: boolean };

export type WorkoutPlan = {
  id: string;
  name: string;
  description: string | null;
  goal: string;
  difficulty: string;
  duration_weeks: number;
  days_per_week: number;
  is_template: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type WorkoutDay = {
  id: string;
  workout_plan_id: string;
  day_number: number;
  title: string;
  notes: string | null;
  estimated_duration_minutes: number | null;
};

export type WorkoutExercise = {
  id: string;
  workout_day_id: string;
  exercise_id: string;
  order_index: number;
  sets: number;
  reps: number;
  target_weight: number | null;
  rest_seconds: number | null;
  notes: string | null;
};

export type WorkoutSession = {
  id: string;
  workout_plan_id: string;
  workout_day_id: string;
  started_at: string;
  completed_at: string | null;
  duration_minutes: number;
  calories_burned: number | null;
  status: string;
  notes: string | null;
};

export type WorkoutLog = {
  id: string;
  workout_session_id: string;
  workout_exercise_id: string;
  set_number: number;
  completed_reps: number;
  completed_weight: number;
  is_completed: boolean;
};

export type BodyProgress = {
  id: string;
  weight_kg: number;
  body_fat_percentage: number | null;
  bmi: number | null;
  chest_cm: number | null;
  waist_cm: number | null;
  hips_cm: number | null;
  notes: string | null;
  recorded_at: string;
};

export type UserProfile = {
  id: string;
  date_of_birth: string | null;
  gender: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  fitness_goal: string | null;
  activity_level: string | null;
  experience_level: string | null;
};
