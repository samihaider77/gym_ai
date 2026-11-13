import Link from 'next/link';
import { Brand } from '@/components/brand';
import { ThemeToggle } from '@/components/theme';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-[100dvh] lg:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
      <div className="flex flex-col px-5 py-6 sm:px-10">
        <div className="flex items-center justify-between">
          <Brand href="/login" size="lg" />
          <ThemeToggle />
        </div>
        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-12">{children}</div>
        <Link href="/credits" className="self-start text-xs text-faint transition-colors hover:text-muted">
          Credits
        </Link>
      </div>

      {/* Empty gym (Pexels, free licence), tinted navy so it matches the brand in both themes. */}
      <aside className="relative hidden overflow-hidden bg-[rgb(20_33_61)] lg:block">
        <video
          src="/brand/auth-gym.mp4"
          poster="/brand/auth-gym.webp"
          autoPlay
          muted
          loop
          playsInline
          className="absolute inset-0 h-full w-full object-cover"
          aria-hidden
        />
        <div aria-hidden className="absolute inset-0 bg-[rgb(20_33_61/0.45)]" />
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[rgb(14_23_44)] via-[rgb(14_23_44/0.75)] to-transparent px-10 pb-10 pt-32">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-[rgb(255_107_91)]">Lift right. Eat right.</p>
          <p className="mt-2 max-w-md text-2xl font-semibold leading-snug tracking-tight text-[rgb(244_237_224)]">
            Your workouts, your form, your progress, in one place.
          </p>
        </div>
      </aside>
    </div>
  );
}
