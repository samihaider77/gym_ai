'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Dialog } from '@/components/ui/dialog';
import { Field, Input, Select } from '@/components/ui/field';
import { useToast } from '@/components/ui/toast';
import { api } from '@/lib/api';
import type { Paginated, WorkoutDay, WorkoutPlan } from '@/lib/types';
import { useApi } from '@/lib/use-api';

export function AddToWorkoutDialog({
  open,
  onClose,
  exerciseId,
  exerciseName,
}: {
  open: boolean;
  onClose: () => void;
  exerciseId: string;
  exerciseName: string;
}) {
  const toast = useToast();
  const plans = useApi<Paginated<WorkoutPlan>>(open ? '/workout-plans' : null, { query: { page_size: 100, is_active: true } });
  const [planId, setPlanId] = useState('');
  const days = useApi<{ items: WorkoutDay[] }>(planId ? `/workout-plans/${planId}/days` : null);
  const [dayId, setDayId] = useState('');
  const [sets, setSets] = useState('3');
  const [reps, setReps] = useState('10');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (plans.data?.items.length && !planId) setPlanId(plans.data.items[0].id);
  }, [plans.data, planId]);
  useEffect(() => {
    setDayId(days.data?.items[0]?.id ?? '');
  }, [days.data]);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const existing = await api<{ items: { order_index: number }[] }>(`/workout-days/${dayId}/exercises`);
      const orderIndex = existing.items.reduce((max, i) => Math.max(max, i.order_index + 1), 0);
      await api(`/workout-days/${dayId}/exercises`, {
        method: 'POST',
        body: { exercise_id: exerciseId, order_index: orderIndex, sets: Number(sets), reps: Number(reps) },
      });
      const day = days.data?.items.find((d) => d.id === dayId);
      toast(`Added to ${day?.title ?? 'your workout'}`);
      onClose();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  const noPlans = plans.data && plans.data.items.length === 0;
  const noDays = days.data && days.data.items.length === 0;

  return (
    <Dialog open={open} onClose={onClose} title="Add to workout" description={exerciseName}>
      {noPlans ? (
        <div className="text-sm text-muted">
          You don’t have a workout plan yet.{' '}
          <Link href="/workouts?new=1" className="font-medium text-accent hover:underline">
            Create one
          </Link>{' '}
          and come back.
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <Field label="Plan">
            {(id) => (
              <Select id={id} value={planId} onChange={(e) => setPlanId(e.target.value)} disabled={plans.loading}>
                {plans.data?.items.map((plan) => (
                  <option key={plan.id} value={plan.id}>
                    {plan.name}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Day" hint={noDays ? 'This plan has no days yet. Add one from the plan page.' : undefined}>
            {(id) => (
              <Select id={id} value={dayId} onChange={(e) => setDayId(e.target.value)} disabled={!days.data?.items.length}>
                {days.data?.items.map((day) => (
                  <option key={day.id} value={day.id}>
                    {day.title && day.title !== `Day ${day.day_number}` ? `Day ${day.day_number}: ${day.title}` : `Day ${day.day_number}`}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Sets">
              {(id) => <Input id={id} type="number" min={1} max={20} inputMode="numeric" value={sets} onChange={(e) => setSets(e.target.value)} />}
            </Field>
            <Field label="Reps">
              {(id) => <Input id={id} type="number" min={1} max={100} inputMode="numeric" value={reps} onChange={(e) => setReps(e.target.value)} />}
            </Field>
          </div>
          {error && <p className="text-sm text-danger">{error}</p>}
          <div className="mt-1 flex justify-end gap-2">
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={save} loading={saving} disabled={!dayId || !(Number(sets) >= 1 && Number(sets) <= 20) || !(Number(reps) >= 1 && Number(reps) <= 100)}>
              Add exercise
            </Button>
          </div>
        </div>
      )}
    </Dialog>
  );
}
