/* eslint-disable @next/next/no-img-element */
import Link from 'next/link';

// Each logo comes in a light and a dark version (public/brand); CSS shows the one for the current theme.
function Themed({ light, dark, className, alt = '' }: { light: string; dark: string; className: string; alt?: string }) {
  return (
    <>
      <img src={light} alt={alt} className={`${className} dark:hidden`} />
      <img src={dark} alt={alt} className={`${className} hidden dark:block`} />
    </>
  );
}

/** The logo mark with the name beside it; `full` shows the complete logo with its tagline (sign-in pages). */
export function Brand({ href = '/dashboard', full = false }: { href?: string; full?: boolean }) {
  if (full) {
    return (
      <Link href={href} className="inline-flex rounded-control" aria-label="LiftAndPlate home">
        <Themed light="/brand/logo-light.png" dark="/brand/logo-dark.png" className="h-16 w-auto" alt="LiftAndPlate" />
      </Link>
    );
  }
  return (
    <Link href={href} className="flex items-center gap-2.5 rounded-control" aria-label="LiftAndPlate home">
      <Themed light="/brand/mark-light.png" dark="/brand/mark-dark.png" className="h-9 w-9 rounded-control" />
      <span className="text-[17px] font-semibold tracking-tight">LiftAndPlate</span>
    </Link>
  );
}
