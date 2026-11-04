'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowRight, ClipboardText, Plus } from '@phosphor-icons/react';
import { PageHeader, Reveal } from '@/components/page';
import { Button } from '@/components/ui/button';
import { Dialog } from '@/components/ui/dialog';
import { Badge, EmptyState, ErrorNotice, Skeleton } from '@/components/ui/feedback';
import { Field, Input, Select, Textarea } from '@/components/ui/field';
import { useToast } from '@/components/ui/toast';
import { api } from '@/lib/api';
import type { Paginated, WorkoutPlan } from '@/lib/types';
import { useApi } from '@/lib/use-api';
import { titleCase } from '@/lib/utils';

const GOALS =['muscle_gain', 'strength', 'fat_loss', 'endurance', 'general_fitness', 'rehab'];

function NewPlanDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const router = useRouter();
  const toast = useToast();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = Object.fromEntries(new FormData(event.currentTarget)) as Record<string, string>;
    if (!form.name.trim()) {
      setError('Give your plan a name.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const plan = await api<WorkoutPlan>('/workout-plans', {
        method: 'POST',
        body: {
          name: form.name.trim(),
          description: form.description.trim() || null,
          goal: form.goal,
          difficulty: form.difficulty,
          days_per_week: Number(form.days_per_week),
          duration_weeks: Number(form.duration_weeks),
          is_template: false,
        },
      });
      // Create the training days up front so the plan is ready to fill.
      for (let day = 1; day <= Number(form.days_per_week); day++) {
        await api(`/workout-plans/${plan.id}/days`, { method: 'POST', body: { day_number: day, title: `Day ${day}` } });
      }
      toast('Plan created');
      router.push(`/workouts/${plan.id}`);
    } catch (err) {
      setError((err as Error).message);
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title="New workout plan" description="You can rename days and add exercises next.">
      <form method="post" onSubmit={onSubmit} className="flex flex-col gap-4">
        <Field label="Plan name">{(id) => <Input id={id} name="name" placeholder="Upper / lower split" maxLength={100} />}</Field>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Goal">
            {(id) => (
              <Select id={id} name="goal" defaultValue="muscle_gain">
                {GOALS.map((g) => (
                  <option key={g} value={g}>
                    {titleCase(g)}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Level">
            {(id) => (
              <Select id={id} name="difficulty" defaultValue="beginner">
                {['beginner', 'intermediate', 'advanced'].map((d) => (
                  <option key={d} value={d}>
                    {titleCase(d)}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Days per week">
            {(id) => (
              <Select id={id} name="days_per_week" defaultValue="3">
                {[1, 2, 3, 4, 5, 6, 7].map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Length in weeks">
            {(id) => <Input id={id} name="duration_weeks" type="number" min={1} max={52} defaultValue={8} inputMode="numeric" />}
          </Field>
        </div>
        <Field label="Notes" hint="Optional">
          {(id) => <Textarea id={id} name="description" placeholder="What this plan is for" />}
        </Field>
        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="mt-1 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={saving}>
            Create plan
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

function Plans() {
  const params = useSearchParams();
  const router = useRouter();
  const [creating, setCreating] = useState(false);
  const plans = useApi<Paginated<WorkoutPlan>>('/workout-plans', { query: { page_size: 50, is_active: true } });

  useEffect(() => {
    if (params.get('new')) {
      setCreating(true);
      router.replace('/workouts');
    }
  }, [params, router]);

  return (
    <>
      <PageHeader
        title="Workouts"
        description="Your training plans. Open one to edit its days or start a session."
        actions={
          plans.data?.items.length ? (
            <Button onClick={() => setCreating(true)}>
              <Plus size={16} weight="bold" />
              New plan
            </Button>
          ) : null
        }
      />

      {plans.error ? (
        <ErrorNotice message={plans.error} onRetry={plans.reload} />
      ) : plans.loading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[0, 1].map((i) => (
            <Skeleton key={i} className="h-36 rounded-card" />
          ))}
        </div>
      ) : plans.data?.items.length === 0 ? (
        <EmptyState
          icon={<ClipboardText size={22} />}
          title="No plans yet"
          body="A plan holds your training days. Create one, then add exercises from the library."
          action={<Button onClick={() => setCreating(true)}>Create your first plan</Button>}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {plans.data?.items.map((plan, index) => (
            <Reveal key={plan.id} delay={index * 0.04}>
              <Link
                href={`/workouts/${plan.id}`}
                className="group flex h-full flex-col rounded-card border border-line bg-surface p-5 shadow-card transition-[transform,box-shadow,border-color] duration-300 ease-out hover:-translate-y-0.5 hover:border-faint/50 hover:shadow-lift"
              >
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-lg font-semibold tracking-tight group-hover:text-accent">{plan.name}</h2>
                  <ArrowRight size={18} className="mt-1 shrink-0 text-faint transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-ink" />
                </div>
                {plan.description && <p className="mt-1 line-clamp-2 text-sm text-muted">{plan.description}</p>}
                <div className="mt-auto flex flex-wrap gap-1.5 pt-4">
                  <Badge tone="accent">{titleCase(plan.goal)}</Badge>
                  <Badge>{titleCase(plan.difficulty)}</Badge>
                  <Badge>
                    {plan.days_per_week} day{plan.days_per_week === 1 ? '' : 's'} a week
                  </Badge>
                  <Badge>{plan.duration_weeks} weeks</Badge>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      )}

      <NewPlanDialog open={creating} onClose={() => setCreating(false)} />
    </>
  );
}

export default function WorkoutsPage() {
  return (
    <Suspense>
      <Plans />
    </Suspense>
  );
}
