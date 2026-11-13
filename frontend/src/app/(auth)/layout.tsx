import Link from 'next/link';
import { Barbell, ChartLineUp, MagicWand, Translate } from '@phosphor-icons/react/dist/ssr';
import { Brand } from '@/components/brand';
import { ThemeToggle } from '@/components/theme';

// A few of the app's own demo loops (Everkinetic drawings, credited on /credits).
const DEMOS = [
  { name: 'Squat', src: '/exercise-media/everkinetic/0122-loop/animation.mp4' },
  { name: 'Deadlift', src: '/exercise-media/everkinetic/0099-loop/animation.mp4' },
  { name: 'Bench press', src: '/exercise-media/everkinetic/0055-loop/animation.mp4' },
  { name: 'Push-up', src: '/exercise-media/everkinetic/0077-loop/animation.mp4' },
];

const FEATURES = [
  { icon: Barbell, text: 'Hundreds of exercises, each with a demo' },
  { icon: MagicWand, text: 'Workouts suggested for your goal and level' },
  { icon: ChartLineUp, text: 'Log every set and watch your progress' },
  { icon: Translate, text: 'Exercise steps in English or Roman Urdu' },
];

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

      {/* Brand panel: navy with a soft coral glow, a few live demos and what the app does. Same in both themes. */}
      <aside className="relative hidden overflow-hidden bg-[rgb(20_33_61)] lg:flex lg:flex-col lg:justify-center lg:px-12 xl:px-16">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              'radial-gradient(60% 50% at 85% 10%, rgb(255 107 91 / 0.28), transparent 70%), radial-gradient(50% 45% at 10% 95%, rgb(255 107 91 / 0.16), transparent 70%)',
          }}
        />
        <div className="relative max-w-lg">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-[rgb(255_107_91)]">Lift right. Eat right.</p>
          <h2 className="mt-3 text-4xl font-semibold leading-[1.1] tracking-tight text-[rgb(244_237_224)]">
            Train with good form, every rep.
          </h2>

          <div className="mt-8 grid grid-cols-2 gap-3">
            {DEMOS.map((demo) => (
              <figure key={demo.name} className="overflow-hidden rounded-card bg-white shadow-lift">
                <video src={demo.src} autoPlay muted loop playsInline aria-hidden className="aspect-[4/3] w-full object-contain" />
                <figcaption className="bg-[rgb(244_237_224)] px-3 py-1.5 text-xs font-medium text-[rgb(20_33_61)]">
                  {demo.name}
                </figcaption>
              </figure>
            ))}
          </div>

          <ul className="mt-8 space-y-3">
            {FEATURES.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-[15px] text-[rgb(244_237_224/0.85)]">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[rgb(255_107_91/0.15)] text-[rgb(255_107_91)]">
                  <Icon size={16} weight="bold" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </div>
  );
}
