import Link from 'next/link';
import { Barbell } from '@phosphor-icons/react/dist/ssr';

export function Brand({ href = '/dashboard' }: { href?: string }) {
  return (
    <Link href={href} className="flex items-center gap-2.5 rounded-control" aria-label="RepRight home">
      <span className="flex h-8 w-8 items-center justify-center rounded-control bg-accent text-accent-fg">
        <Barbell size={18} weight="bold" />
      </span>
      <span className="text-[17px] font-semibold tracking-tight">RepRight</span>
    </Link>
  );
}
