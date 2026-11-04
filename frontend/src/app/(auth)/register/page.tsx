'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Field, Input } from '@/components/ui/field';
import { api, session } from '@/lib/api';
import type { TokenResponse } from '@/lib/types';

type Errors = Partial<Record<'first_name' | 'last_name' | 'email' | 'password' | 'form', string>>;

export default function RegisterPage() {
  const router = useRouter();
  const [errors, setErrors] = useState<Errors>({});
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = Object.fromEntries(new FormData(event.currentTarget)) as Record<string, string>;
    const next: Errors = {};
    if (!form.first_name.trim()) next.first_name = 'Enter your first name.';
    if (!form.last_name.trim()) next.last_name = 'Enter your last name.';
    if (!/^\S+@\S+\.\S+$/.test(form.email)) next.email = 'Enter a valid email address.';
    if (form.password.length < 8) next.password = 'Use at least 8 characters.';
    setErrors(next);
    if (Object.keys(next).length) return;

    setLoading(true);
    try {
      await api('/users', { method: 'POST', body: form });
      const result = await api<TokenResponse>('/auth/login', {
        method: 'POST',
        body: { email: form.email, password: form.password },
      });
      session.save(result.access_token, result.user);
      router.replace('/profile?welcome=1');
    } catch (err) {
      setErrors({ form: (err as Error).message });
      setLoading(false);
    }
  }

  return (
    <>
      <h1 className="text-2xl font-semibold tracking-tight">Create your account</h1>
      <p className="mt-1.5 text-[15px] text-muted">Free to use. Takes under a minute.</p>

      <form method="post" onSubmit={onSubmit} className="mt-8 flex flex-col gap-4" noValidate>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="First name" error={errors.first_name}>
            {(id, describedBy) => (
              <Input id={id} name="first_name" autoComplete="given-name" aria-invalid={!!errors.first_name} aria-describedby={describedBy} />
            )}
          </Field>
          <Field label="Last name" error={errors.last_name}>
            {(id, describedBy) => (
              <Input id={id} name="last_name" autoComplete="family-name" aria-invalid={!!errors.last_name} aria-describedby={describedBy} />
            )}
          </Field>
        </div>
        <Field label="Email" error={errors.email}>
          {(id, describedBy) => (
            <Input id={id} name="email" type="email" autoComplete="email" aria-invalid={!!errors.email} aria-describedby={describedBy} />
          )}
        </Field>
        <Field label="Password" hint="At least 8 characters." error={errors.password}>
          {(id, describedBy) => (
            <Input
              id={id}
              name="password"
              type="password"
              autoComplete="new-password"
              aria-invalid={!!errors.password}
              aria-describedby={describedBy}
            />
          )}
        </Field>
        {errors.form && (
          <p role="alert" className="rounded-control bg-danger/10 px-3 py-2.5 text-sm text-danger">
            {errors.form}
          </p>
        )}
        <Button type="submit" size="lg" loading={loading} className="mt-2 w-full">
          Create account
        </Button>
      </form>

      <p className="mt-6 text-sm text-muted">
        Already have an account?{' '}
        <Link href="/login" className="font-medium text-accent hover:underline">
          Sign in
        </Link>
      </p>
    </>
  );
}
