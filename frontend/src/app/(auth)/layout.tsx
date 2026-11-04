import { Brand } from '@/components/brand';
import { ThemeToggle } from '@/components/theme';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-[100dvh] lg:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
      <div className="flex flex-col px-5 py-6 sm:px-10">
        <div className="flex items-center justify-between">
          <Brand href="/login" />
          <ThemeToggle />
        </div>
        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-12">{children}</div>
      </div>

      <aside className="relative hidden overflow-hidden bg-[rgb(20_20_22)] lg:block">
        <video
          src="/brand/auth.mp4"
          poster="/brand/auth.webp"
          autoPlay
          muted
          loop
          playsInline
          className="absolute inset-0 h-full w-full object-cover"
          aria-hidden
        />
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[rgb(14_14_16)] via-[rgb(14_14_16/0.7)] to-transparent px-10 pb-10 pt-32">
          <p className="max-w-md text-2xl font-semibold leading-snug tracking-tight text-white">
            Hundreds of exercises with free demo videos, so every rep starts with good form.
          </p>
          <p className="mt-4 text-xs text-white/60">
            Front squat video by Goulart via wger.de, CC BY-SA 4.0
          </p>
        </div>
      </aside>
    </div>
  );
}
