import { LinkButton } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className="flex min-h-[100dvh] flex-col items-center justify-center px-6 text-center">
      <p className="text-sm font-medium text-accent">404</p>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight">This page doesn’t exist</h1>
      <p className="mt-2 max-w-sm text-[15px] text-muted">The link may be old, or the page was moved.</p>
      <LinkButton href="/dashboard" className="mt-6">
        Go to home
      </LinkButton>
    </div>
  );
}
