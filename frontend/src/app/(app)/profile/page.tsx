'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { PageHeader, Panel, Reveal } from '@/components/page';
import { Button } from '@/components/ui/button';
import { ErrorNotice, Skeleton } from '@/components/ui/feedback';
import { Field, Input, Select } from '@/components/ui/field';
import { useToast } from '@/components/ui/toast';
import { ApiError, api, session } from '@/lib/api';
import type { User, UserProfile } from '@/lib/types';
import { titleCase } from '@/lib/utils';

const GOALS = ['muscle_gain', 'strength', 'fat_loss', 'endurance', 'general_fitness'];
const ACTIVITY = ['sedentary', 'lightly_active', 'moderately_active', 'very_active'];
const EXPERIENCE = ['beginner', 'intermediate', 'advanced'];
const GENDERS = ['male', 'female', 'other'];

function Options({ values }: { values: string[] }) {
  return (
    <>
      <option value="">Not set</option>
      {values.map((v) => (
        <option key={v} value={v}>
          {titleCase(v)}
        </option>
      ))}
    </>
  );
}

function ProfileForm() {
  const params = useSearchParams();
  const toast = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [exists, setExists] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setUser(session.user());
    api<UserProfile>('/profile/me')
      .then((p) => {
        setProfile(p);
        setExists(true);
      })
      .catch((err: ApiError) => {
        if (err.status !== 404) setError(err.message);
      })
      .finally(() => setLoading(false));
  }, []);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = Object.fromEntries(new FormData(event.currentTarget)) as Record<string, string>;
    const body = {
      date_of_birth: form.date_of_birth || null,
      gender: form.gender || null,
      height_cm: form.height_cm ? Number(form.height_cm) : null,
      weight_kg: form.weight_kg ? Number(form.weight_kg) : null,
      fitness_goal: form.fitness_goal || null,
      activity_level: form.activity_level || null,
      experience_level: form.experience_level || null,
    };
    setSaving(true);
    try {
      const saved = await api<UserProfile>('/profile', { method: exists ? 'PUT' : 'POST', body });
      setProfile(saved);
      setExists(true);
      toast('Profile saved');
    } catch (err) {
      toast((err as Error).message, 'error');
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <PageHeader
        title={params.get('welcome') ? `Welcome${user ? `, ${user.first_name}` : ''}` : 'Profile'}
        description={
          params.get('welcome')
            ? 'Tell us a little about you. It helps when planning your training. You can skip this.'
            : 'Your details and training preferences.'
        }
      />

      {error && (
        <div className="mb-6">
          <ErrorNotice message={error} />
        </div>
      )}

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
        <Reveal>
          <Panel className="p-5">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent-soft text-lg font-semibold text-accent">
              {(user?.first_name?.[0] ?? '') + (user?.last_name?.[0] ?? '')}
            </div>
            <p className="mt-4 text-lg font-semibold tracking-tight">{user ? `${user.first_name} ${user.last_name}` : ' '}</p>
            <p className="text-sm text-muted">{user?.email}</p>
            {user && <p className="mt-4 text-[13px] text-faint">Member since {new Date(user.created_at).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })}</p>}
          </Panel>
        </Reveal>

        <Reveal delay={0.06}>
          <Panel className="p-5 sm:p-6">
            {loading ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-16" />
                ))}
              </div>
            ) : (
              <form method="post" onSubmit={onSubmit} className="flex flex-col gap-6">
                <fieldset className="grid gap-4 sm:grid-cols-2">
                  <legend className="mb-3 text-sm font-semibold">About you</legend>
                  <Field label="Date of birth">{(id) => <Input id={id} name="date_of_birth" type="date" defaultValue={profile?.date_of_birth ?? ''} />}</Field>
                  <Field label="Gender">
                    {(id) => (
                      <Select id={id} name="gender" defaultValue={profile?.gender ?? ''}>
                        <Options values={GENDERS} />
                      </Select>
                    )}
                  </Field>
                  <Field label="Height (cm)">{(id) => <Input id={id} name="height_cm" type="number" step="0.1" min={0} max={300} inputMode="decimal" defaultValue={profile?.height_cm ?? ''} />}</Field>
                  <Field label="Weight (kg)">{(id) => <Input id={id} name="weight_kg" type="number" step="0.1" min={0} max={500} inputMode="decimal" defaultValue={profile?.weight_kg ?? ''} />}</Field>
                </fieldset>
                <fieldset className="grid gap-4 border-t border-line pt-6 sm:grid-cols-2">
                  <legend className="sr-only">Training</legend>
                  <p className="text-sm font-semibold sm:col-span-2">Training</p>
                  <Field label="Main goal">
                    {(id) => (
                      <Select id={id} name="fitness_goal" defaultValue={profile?.fitness_goal ?? ''}>
                        <Options values={GOALS} />
                      </Select>
                    )}
                  </Field>
                  <Field label="Experience">
                    {(id) => (
                      <Select id={id} name="experience_level" defaultValue={profile?.experience_level ?? ''}>
                        <Options values={EXPERIENCE} />
                      </Select>
                    )}
                  </Field>
                  <Field label="Activity level" className="sm:col-span-2">
                    {(id) => (
                      <Select id={id} name="activity_level" defaultValue={profile?.activity_level ?? ''}>
                        <Options values={ACTIVITY} />
                      </Select>
                    )}
                  </Field>
                </fieldset>
                <div className="flex justify-end border-t border-line pt-5">
                  <Button type="submit" loading={saving}>
                    Save profile
                  </Button>
                </div>
              </form>
            )}
          </Panel>
        </Reveal>
      </div>
    </>
  );
}

export default function ProfilePage() {
  return (
    <Suspense>
      <ProfileForm />
    </Suspense>
  );
}
