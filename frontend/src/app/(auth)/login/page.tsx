'use client';

import { Suspense, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Field, Input } from '@/components/ui/field';
import { api, session } from '@/lib/api';
import type { TokenResponse } from '@/lib/types';

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setLoading(true);
    setError(null);
    try {
      const result = await api<TokenResponse>('/auth/login', {
        method: 'POST',
        body: { email: form.get('email'), password: form.get('password') },
      });
      session.save(result.access_token, result.user);
      const next = params.get('next');
      router.replace(next && next.startsWith('/') ? next : '/dashboard');
    } catch (err) {
      setError((err as Error).message.startsWith('Invalid email') ? 'That email and password don’t match.' : (err as Error).message);
      setLoading(false);
    }
  }

  return (
    <>
      <h1 className="text-2xl font-semibold tracking-tight">Welcome back</h1>
      <p className="mt-1.5 text-[15px] text-muted">Sign in to pick up where you left off.</p>

      <form method="post" onSubmit={onSubmit} className="mt-8 flex flex-col gap-4" noValidate>
        <Field label="Email">
          {(id) => <Input id={id} name="email" type="email" autoComplete="email" required placeholder="you@example.com" />}
        </Field>
        <Field label="Password">
          {(id) => <Input id={id} name="password" type="password" autoComplete="current-password" required />}
        </Field>
        {error && (
          <p role="alert" className="rounded-control bg-danger/10 px-3 py-2.5 text-sm text-danger">
            {error}
          </p>
        )}
        <Button type="submit" size="lg" loading={loading} className="mt-2 w-full">
          Sign in
        </Button>
      </form>

      <p className="mt-6 text-sm text-muted">
        New to GymAI?{' '}
        <Link href="/register" className="font-medium text-accent hover:underline">
          Create an account
        </Link>
      </p>
    </>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
