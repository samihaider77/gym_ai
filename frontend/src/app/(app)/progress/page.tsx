'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { ChartLineUp, Plus } from '@phosphor-icons/react';
import { PageHeader, Panel, Reveal } from '@/components/page';
import { Button } from '@/components/ui/button';
import { Dialog } from '@/components/ui/dialog';
import { EmptyState, ErrorNotice, Skeleton } from '@/components/ui/feedback';
import { Field, Input, Textarea } from '@/components/ui/field';
import { useToast } from '@/components/ui/toast';
import { api } from '@/lib/api';
import type { BodyProgress, Paginated } from '@/lib/types';
import { useApi } from '@/lib/use-api';
import { formatDate, formatNumber } from '@/lib/utils';

function WeightChart({ entries }: { entries: BodyProgress[] }) {
  const [hover, setHover] = useState<number | null>(null);
  // Draw at the real pixel width so axis labels stay readable on phones.
  const [width, setWidth] = useState(640);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(240, Math.round(entry.contentRect.width))));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  const points = entries.slice().reverse();
  const height = width < 480 ? 170 : 200;
  const pad = { top: 16, right: 12, bottom: 28, left: 40 };
  const weights = points.map((p) => p.weight_kg);
  const min = Math.floor(Math.min(...weights) - 1);
  // Keep the range even so the middle grid line lands on a whole number.
  const max = Math.ceil(Math.max(...weights) + 1) + ((Math.ceil(Math.max(...weights) + 1) - min) % 2);
  const x = (i: number) => pad.left + (points.length === 1 ? (width - pad.left - pad.right) / 2 : (i / (points.length - 1)) * (width - pad.left - pad.right));
  const y = (w: number) => pad.top + (1 - (w - min) / (max - min || 1)) * (height - pad.top - pad.bottom);
  const path = points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.weight_kg).toFixed(1)}`).join(' ');
  const ticks = [min, (min + max) / 2, max];
  const active = hover !== null ? points[hover] : points[points.length - 1];

  return (
    <div ref={box}>
      <div className="mb-2 flex items-baseline gap-2">
        <span className="text-2xl font-semibold tabular tracking-tight">{formatNumber(active.weight_kg)} kg</span>
        <span className="text-sm text-muted">{formatDate(active.recorded_at, { day: 'numeric', month: 'short', year: 'numeric' })}</span>
      </div>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-auto w-full touch-none"
        role="img"
        aria-label={`Body weight over ${points.length} entries`}
        onPointerLeave={() => setHover(null)}
        onPointerMove={(event) => {
          const rect = (event.currentTarget as SVGSVGElement).getBoundingClientRect();
          const px = ((event.clientX - rect.left) / rect.width) * width;
          let nearest = 0;
          points.forEach((_, i) => {
            if (Math.abs(x(i) - px) < Math.abs(x(nearest) - px)) nearest = i;
          });
          setHover(nearest);
        }}
      >
        {ticks.map((t) => (
          <g key={t}>
            <line x1={pad.left} x2={width - pad.right} y1={y(t)} y2={y(t)} className="stroke-line" strokeWidth={1} />
            <text x={pad.left - 8} y={y(t)} dy="0.32em" textAnchor="end" className="fill-faint text-[11px] tabular">
              {formatNumber(t, 0)}
            </text>
          </g>
        ))}
        <path d={path} fill="none" className="stroke-accent" strokeWidth={2.25} strokeLinejoin="round" strokeLinecap="round" />
        {points.map((p, i) => (
          <circle
            key={p.id}
            cx={x(i)}
            cy={y(p.weight_kg)}
            r={hover === i || (hover === null && i === points.length - 1) ? 5 : 3}
            className="fill-surface stroke-accent transition-[r] duration-150"
            strokeWidth={2}
          />
        ))}
        {[0, points.length - 1].filter((v, i, a) => a.indexOf(v) === i).map((i) => (
          <text key={i} x={x(i)} y={height - 8} textAnchor={i === 0 && points.length > 1 ? 'start' : 'end'} className="fill-faint text-[11px]">
            {formatDate(points[i].recorded_at)}
          </text>
        ))}
      </svg>
    </div>
  );
}

function LogDialog({ open, onClose, onSaved }: { open: boolean; onClose: () => void; onSaved: () => void }) {
  const toast = useToast();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = Object.fromEntries(new FormData(event.currentTarget)) as Record<string, string>;
    const num = (v: string) => (v.trim() ? Number(v) : null);
    if (!num(form.weight_kg)) {
      setError('Enter your body weight.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api('/progress', {
        method: 'POST',
        body: {
          weight_kg: num(form.weight_kg),
          body_fat_percentage: num(form.body_fat_percentage),
          waist_cm: num(form.waist_cm),
          chest_cm: num(form.chest_cm),
          notes: form.notes.trim() || null,
          recorded_at: form.recorded_at ? new Date(form.recorded_at).toISOString() : null,
        },
      });
      toast('Measurement saved');
      onSaved();
      onClose();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title="Log measurement" description="Weight is required. Everything else is optional.">
      <form method="post" onSubmit={onSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Weight (kg)">{(id) => <Input id={id} name="weight_kg" inputMode="decimal" type="number" step="0.1" min={0} max={500} />}</Field>
          <Field label="Date">{(id) => <Input id={id} name="recorded_at" type="date" defaultValue={new Date().toISOString().slice(0, 10)} />}</Field>
          <Field label="Body fat (%)">{(id) => <Input id={id} name="body_fat_percentage" inputMode="decimal" type="number" step="0.1" min={0} max={100} />}</Field>
          <Field label="Waist (cm)">{(id) => <Input id={id} name="waist_cm" inputMode="decimal" type="number" step="0.1" min={0} max={300} />}</Field>
          <Field label="Chest (cm)">{(id) => <Input id={id} name="chest_cm" inputMode="decimal" type="number" step="0.1" min={0} max={300} />}</Field>
        </div>
        <Field label="Notes">{(id) => <Textarea id={id} name="notes" />}</Field>
        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={saving}>
            Save
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

export default function ProgressPage() {
  const [logging, setLogging] = useState(false);
  const history = useApi<Paginated<BodyProgress>>('/progress/history', { query: { page_size: 60 } });
  const entries = useMemo(
    () => [...(history.data?.items ?? [])].sort((a, b) => +new Date(b.recorded_at) - +new Date(a.recorded_at)),
    [history.data],
  );
  const latest = entries[0];
  const first = entries[entries.length - 1];
  const change = latest && first && entries.length > 1 ? latest.weight_kg - first.weight_kg : null;

  return (
    <>
      <PageHeader
        title="Progress"
        description="Track body weight and measurements over time."
        actions={
          entries.length > 0 && (
            <Button onClick={() => setLogging(true)}>
              <Plus size={16} weight="bold" />
              Log measurement
            </Button>
          )
        }
      />

      {history.error ? (
        <ErrorNotice message={history.error} onRetry={history.reload} />
      ) : history.loading ? (
        <Skeleton className="h-72 rounded-card" />
      ) : entries.length === 0 ? (
        <EmptyState
          icon={<ChartLineUp size={22} />}
          title="No measurements yet"
          body="Log your weight once a week and your trend shows up here."
          action={<Button onClick={() => setLogging(true)}>Log your first measurement</Button>}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
          <Reveal>
            <Panel className="p-5">
              <WeightChart entries={entries} />
              {change !== null && (
                <p className="mt-3 text-sm text-muted">
                  {change === 0 ? 'No change' : `${change > 0 ? 'Up' : 'Down'} ${formatNumber(Math.abs(change))} kg`} since{' '}
                  {formatDate(first.recorded_at, { day: 'numeric', month: 'long' })}
                </p>
              )}
            </Panel>
          </Reveal>

          <Reveal delay={0.06}>
            <Panel>
              <h2 className="border-b border-line px-5 py-3.5 text-sm font-semibold">History</h2>
              <ul className="max-h-[420px] divide-y divide-line overflow-y-auto">
                {entries.map((entry) => (
                  <li key={entry.id} className="flex items-center justify-between gap-3 px-5 py-3">
                    <div>
                      <p className="text-[15px] font-medium tabular">{formatNumber(entry.weight_kg)} kg</p>
                      <p className="text-[13px] text-muted">
                        {[
                          entry.body_fat_percentage !== null && `${formatNumber(entry.body_fat_percentage)}% fat`,
                          entry.waist_cm !== null && `waist ${formatNumber(entry.waist_cm)} cm`,
                          entry.bmi !== null && `BMI ${formatNumber(entry.bmi)}`,
                        ]
                          .filter(Boolean)
                          .join(', ') || 'Weight only'}
                      </p>
                    </div>
                    <span className="shrink-0 text-[13px] text-muted">{formatDate(entry.recorded_at, { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                  </li>
                ))}
              </ul>
            </Panel>
          </Reveal>
        </div>
      )}

      <LogDialog open={logging} onClose={() => setLogging(false)} onSaved={history.reload} />
    </>
  );
}
