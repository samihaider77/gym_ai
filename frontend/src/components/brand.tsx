/* eslint-disable @next/next/no-img-element */
import Link from 'next/link';

// The logo (mark + "LiftAndPlate" + tagline) in a light and a dark version, with transparent backgrounds
// (public/brand); CSS shows the one for the current theme.
const SIZES = { sm: 'h-8', md: 'h-11', lg: 'h-14' };

export function Brand({ href = '/dashboard', size = 'md' }: { href?: string; size?: keyof typeof SIZES }) {
  const className = `${SIZES[size]} w-auto max-w-full`;
  return (
    <Link href={href} className="inline-flex max-w-full rounded-control" aria-label="LiftAndPlate home">
      <img src="/brand/logo-wide-light.png" alt="LiftAndPlate" className={`${className} dark:hidden`} />
      <img src="/brand/logo-wide-dark.png" alt="LiftAndPlate" className={`${className} hidden dark:block`} />
    </Link>
  );
}
