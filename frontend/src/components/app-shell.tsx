'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { motion } from 'motion/react';
import {
  Barbell,
  ChartLineUp,
  ClipboardText,
  House,
  SignOut,
  UserCircle,
  type Icon,
} from '@phosphor-icons/react';
import { session } from '@/lib/api';
import type { User } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Brand } from './brand';
import { LanguageToggle } from './language';
import { ThemeToggle } from './theme';

const NAV: { href: string; label: string; icon: Icon }[] = [
  { href: '/dashboard', label: 'Home', icon: House },
  { href: '/exercises', label: 'Exercises', icon: Barbell },
  { href: '/workouts', label: 'Workouts', icon: ClipboardText },
  { href: '/progress', label: 'Progress', icon: ChartLineUp },
  { href: '/profile', label: 'Profile', icon: UserCircle },
];

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`) || (href === '/workouts' && pathname.startsWith('/sessions'));
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!session.token()) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    setUser(session.user());
    setReady(true);
  }, [pathname, router]);

  const signOut = () => {
    session.clear();
    router.replace('/login');
  };

  if (!ready) return <div className="min-h-[100dvh] bg-canvas" />;

  return (
    <div className="min-h-[100dvh] lg:grid lg:grid-cols-[248px_1fr]">
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-[100dvh] flex-col border-r border-line bg-surface px-4 py-5 lg:flex">
        <div className="px-2">
          <Brand />
        </div>
        <nav className="mt-8 flex flex-col gap-1" aria-label="Main">
          {NAV.map(({ href, label, icon: NavIcon }) => {
            const active = isActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'relative flex h-10 items-center gap-3 rounded-control px-3 text-sm font-medium transition-colors duration-150',
                  active ? 'text-ink' : 'text-muted hover:bg-sunken hover:text-ink',
                )}
                aria-current={active ? 'page' : undefined}
              >
                {active && (
                  <motion.span
                    layoutId="nav-active"
                    className="absolute inset-0 rounded-control bg-sunken"
                    transition={{ type: 'spring', stiffness: 500, damping: 40 }}
                  />
                )}
                <NavIcon size={19} weight={active ? 'fill' : 'regular'} className={cn('relative', active && 'text-accent')} />
                <span className="relative">{label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto border-t border-line pt-4">
          <div className="flex items-center gap-3 px-2">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent-soft text-sm font-semibold text-accent">
              {(user?.first_name?.[0] ?? '') + (user?.last_name?.[0] ?? '')}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">
                {user ? `${user.first_name} ${user.last_name}` : 'Athlete'}
              </p>
              <p className="truncate text-xs text-muted">{user?.email}</p>
            </div>
          </div>
          <LanguageToggle className="mt-3" />
          <div className="mt-2 flex items-center gap-1">
            <ThemeToggle />
            <button
              onClick={signOut}
              className="flex h-9 flex-1 items-center gap-2 rounded-control px-2.5 text-sm text-muted transition-colors hover:bg-sunken hover:text-ink"
            >
              <SignOut size={18} />
              Sign out
            </button>
          </div>
          <Link href="/credits" className="mt-2 block px-2.5 text-xs text-faint transition-colors hover:text-muted">
            Credits
          </Link>
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-line bg-surface px-4 lg:hidden">
        <Brand />
        <div className="flex items-center gap-1">
          <LanguageToggle compact />
          <ThemeToggle />
          <button
            onClick={signOut}
            className="flex h-9 w-9 items-center justify-center rounded-control text-muted hover:bg-sunken hover:text-ink"
            aria-label="Sign out"
          >
            <SignOut size={18} />
          </button>
        </div>
      </header>

      <main className="min-w-0 pb-24 lg:pb-0">
        <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-10 lg:py-10">{children}</div>
      </main>

      {/* Mobile tab bar */}
      <nav
        className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-line bg-surface pb-[env(safe-area-inset-bottom)] lg:hidden"
        aria-label="Main"
      >
        {NAV.map(({ href, label, icon: NavIcon }) => {
          const active = isActive(pathname, href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex h-16 flex-col items-center justify-center gap-1 text-[11px] font-medium transition-colors',
                active ? 'text-accent' : 'text-muted',
              )}
              aria-current={active ? 'page' : undefined}
            >
              <NavIcon size={22} weight={active ? 'fill' : 'regular'} />
              {label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
