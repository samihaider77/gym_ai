'use client';

import { useCallback, useMemo, useRef, useState } from 'react';
import { Camera, CaretLeft, CaretRight, ForkKnife, Minus, Plus, Sparkle, Trash } from '@phosphor-icons/react';
import { PageHeader, Panel, Reveal } from '@/components/page';
import { Button } from '@/components/ui/button';
import { Dialog } from '@/components/ui/dialog';
import { EmptyState, ErrorNotice, Skeleton } from '@/components/ui/feedback';
import { Select } from '@/components/ui/field';
import { useToast } from '@/components/ui/toast';
import { api, ApiError } from '@/lib/api';
import { useLanguage } from '@/lib/i18n';
import type { Food, Meal, MealAnalysis, MealDay } from '@/lib/types';
import { useApi } from '@/lib/use-api';
import { cn } from '@/lib/utils';

/** A line in the meal editor: a food from the table, how many of which unit. */
type Line = { food_key: string; quantity: number; unit: string; confidence?: number | null };

function dayBounds(offset: number) {
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  start.setDate(start.getDate() + offset);
  const end = new Date(start);
  end.setDate(end.getDate() + 1);
  return { start: start.toISOString(), end: end.toISOString(), label: start };
}

function lineMacros(line: Line, foods: Map<string, Food>) {
  const food = foods.get(line.food_key);
  if (!food) return { kcal: 0, protein_g: 0, grams: 0 };
  const unit = food.units.find((u) => u.label === line.unit) ?? food.units[0];
  const grams = line.quantity * unit.grams;
  return { kcal: (food.per_100g.kcal * grams) / 100, protein_g: (food.per_100g.protein_g * grams) / 100, grams };
}

/** Shrinks the photo before upload: phone pictures are 3-8 MB, the model needs about 1000 px. */
async function photoToJpeg(file: File): Promise<{ base64: string; preview: string }> {
  const url = URL.createObjectURL(file);
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image();
      el.onload = () => resolve(el);
      el.onerror = () => reject(new Error('That file isn’t a photo we can read.'));
      el.src = url;
    });
    const scale = Math.min(1, 1024 / Math.max(img.naturalWidth, img.naturalHeight));
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(img.naturalWidth * scale);
    canvas.height = Math.round(img.naturalHeight * scale);
    canvas.getContext('2d')!.drawImage(img, 0, 0, canvas.width, canvas.height);
    const preview = canvas.toDataURL('image/jpeg', 0.82);
    return { base64: preview.split(',')[1], preview };
  } finally {
    URL.revokeObjectURL(url);
  }
}

function Bar({ label, value, target, unit }: { label: string; value: number; target: number | null; unit: string }) {
  const pct = target ? Math.min(100, (value / target) * 100) : 0;
  const over = target !== null && value > target * 1.05;
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-sm tabular text-muted">
          <span className="font-semibold text-ink">{Math.round(value)}</span>
          {target ? ` / ${target}` : ''} {unit}
        </span>
      </div>
      <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-sunken">
        <div
          className={cn('h-full rounded-full transition-[width] duration-500', over ? 'bg-danger' : 'bg-accent')}
          style={{ width: `${target ? pct : 0}%` }}
        />
      </div>
    </div>
  );
}

function MealEditor({
  open,
  onClose,
  onSaved,
  foods,
  initial,
}: {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  foods: Food[];
  initial: { lines: Line[]; preview: string | null; source: 'photo' | 'manual'; notice: string | null; others: string[] };
}) {
  const toast = useToast();
  const { lang } = useLanguage();
  const ur = lang === 'ur';
  const byKey = useMemo(() => new Map(foods.map((f) => [f.key, f])), [foods]);
  const [lines, setLines] = useState<Line[]>(initial.lines);
  const [adding, setAdding] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const total = lines.reduce(
    (acc, line) => {
      const m = lineMacros(line, byKey);
      return { kcal: acc.kcal + m.kcal, protein_g: acc.protein_g + m.protein_g };
    },
    { kcal: 0, protein_g: 0 },
  );

  const update = (index: number, patch: Partial<Line>) =>
    setLines((all) => all.map((line, i) => (i === index ? { ...line, ...patch } : line)));

  function addFood(key: string) {
    const food = byKey.get(key);
    if (!food) return;
    setLines((all) => [...all, { food_key: key, quantity: 1, unit: food.units[0].label }]);
    setAdding('');
  }

  async function save() {
    setSaving(true);
    setError(null);
    try {
      await api('/ai/meals', {
        method: 'POST',
        body: { source: initial.source, items: lines.map(({ food_key, quantity, unit }) => ({ food_key, quantity, unit })) },
      });
      toast('Meal saved');
      onSaved();
      onClose();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={initial.source === 'photo' ? 'Check your meal' : 'Add a meal'}
      description="Fix any portion before saving. Calories come from the food table, not a guess."
    >
      <div className="flex flex-col gap-4">
        {initial.preview && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={initial.preview} alt="Your meal" className="max-h-48 w-full rounded-control object-cover" />
        )}
        {initial.notice && <p className="rounded-control bg-sunken px-3 py-2 text-sm text-muted">{initial.notice}</p>}
        {initial.others.length > 0 && (
          <p className="text-sm text-muted">
            Not in our food list yet: <span className="text-ink">{initial.others.join(', ')}</span>. Add the closest match below.
          </p>
        )}

        {lines.length > 0 ? (
          <ul className="divide-y divide-line rounded-card border border-line">
            {lines.map((line, index) => {
              const food = byKey.get(line.food_key);
              if (!food) return null;
              const m = lineMacros(line, byKey);
              return (
                <li key={`${line.food_key}-${index}`} className="flex flex-wrap items-center gap-3 px-3 py-3">
                  <div className="min-w-0 flex-1 basis-40">
                    <p className="truncate text-[15px] font-medium">{ur ? food.name_ur : food.name}</p>
                    <p className="text-[13px] tabular text-muted">
                      {Math.round(m.kcal)} kcal · {m.protein_g.toFixed(1)} g protein
                      {line.confidence !== undefined && line.confidence !== null && line.confidence < 0.5 && (
                        <span className="text-accent"> · check this one</span>
                      )}
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Button
                      size="icon"
                      variant="secondary"
                      className="h-8 w-8"
                      aria-label={`Less ${food.name}`}
                      onClick={() => update(index, { quantity: Math.max(0.5, line.quantity - 0.5) })}
                    >
                      <Minus size={14} weight="bold" />
                    </Button>
                    <span className="w-9 text-center text-[15px] font-semibold tabular">{line.quantity}</span>
                    <Button
                      size="icon"
                      variant="secondary"
                      className="h-8 w-8"
                      aria-label={`More ${food.name}`}
                      onClick={() => update(index, { quantity: Math.min(20, line.quantity + 0.5) })}
                    >
                      <Plus size={14} weight="bold" />
                    </Button>
                    {food.units.length > 1 ? (
                      <Select
                        aria-label={`Unit for ${food.name}`}
                        value={line.unit}
                        onChange={(e) => update(index, { unit: e.target.value })}
                        className="h-8 w-[104px] text-[13px]"
                      >
                        {food.units.map((u) => (
                          <option key={u.label} value={u.label}>
                            {ur ? u.label_ur : u.label}
                          </option>
                        ))}
                      </Select>
                    ) : (
                      <span className="w-[104px] text-[13px] text-muted">{ur ? food.units[0].label_ur : food.units[0].label}</span>
                    )}
                    <button
                      onClick={() => setLines((all) => all.filter((_, i) => i !== index))}
                      className="flex h-8 w-8 items-center justify-center rounded-control text-muted hover:bg-sunken hover:text-danger"
                      aria-label={`Remove ${food.name}`}
                    >
                      <Trash size={16} />
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="text-sm text-muted">No foods yet. Pick one below.</p>
        )}

        <Select aria-label="Add a food" value={adding} onChange={(e) => addFood(e.target.value)}>
          <option value="">+ Add a food…</option>
          {foods.map((f) => (
            <option key={f.key} value={f.key}>
              {ur ? `${f.name_ur} (${f.name})` : f.name}
            </option>
          ))}
        </Select>

        <div className="flex items-center justify-between rounded-control bg-sunken px-3 py-2.5 text-sm">
          <span className="text-muted">This meal</span>
          <span className="tabular">
            <span className="font-semibold">{Math.round(total.kcal)} kcal</span> · {total.protein_g.toFixed(1)} g protein
          </span>
        </div>
        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={save} loading={saving} disabled={lines.length === 0}>
            Save meal
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

function mealTitle(meal: Meal, ur: boolean) {
  return meal.items.map((i) => `${ur ? i.name_ur : i.name} (${i.quantity} ${ur ? i.unit_ur : i.unit})`).join(', ');
}

export default function FoodPage() {
  const toast = useToast();
  const { lang } = useLanguage();
  const ur = lang === 'ur';
  const [offset, setOffset] = useState(0);
  const bounds = useMemo(() => dayBounds(offset), [offset]);
  const day = useApi<MealDay>('/ai/meals/day', { query: { start: bounds.start, end: bounds.end } }, [bounds.start]);
  const foods = useApi<Food[]>('/ai/foods');
  const fileInput = useRef<HTMLInputElement>(null);
  const [reading, setReading] = useState<string | null>(null);
  const [editor, setEditor] = useState<{
    key: number;
    lines: Line[];
    preview: string | null;
    source: 'photo' | 'manual';
    notice: string | null;
    others: string[];
  } | null>(null);

  const openManual = useCallback(() => {
    setEditor({ key: Date.now(), lines: [], preview: null, source: 'manual', notice: null, others: [] });
  }, []);

  async function onPhoto(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    let photo: { base64: string; preview: string };
    try {
      photo = await photoToJpeg(file);
    } catch (err) {
      toast((err as Error).message);
      return;
    }
    setReading(photo.preview);
    try {
      const result = await api<MealAnalysis>('/ai/meals/analyze', {
        method: 'POST',
        body: { image_base64: photo.base64, mime_type: 'image/jpeg' },
      });
      setEditor({
        key: Date.now(),
        lines: result.items.map((i) => ({ food_key: i.food_key, quantity: i.quantity, unit: i.unit, confidence: i.confidence })),
        preview: photo.preview,
        source: 'photo',
        notice: !result.is_food
          ? 'This doesn’t look like food. Add the foods by hand if it is.'
          : result.items.length === 0
            ? 'Couldn’t spot any foods from our list. Add them by hand.'
            : null,
        others: result.other_foods,
      });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Couldn’t read the photo. Add the foods by hand.';
      setEditor({ key: Date.now(), lines: [], preview: photo.preview, source: 'manual', notice: message, others: [] });
    } finally {
      setReading(null);
    }
  }

  const data = day.data;
  // Until a Gemini key is set, the photo button still works but falls back to manual entry, so manual leads.
  const canSnap = data?.photo_recognition !== false;
  const dayName =
    offset === 0 ? 'Today' : offset === -1 ? 'Yesterday' : bounds.label.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'short' });

  return (
    <>
      <PageHeader
        title="Food"
        description="Snap your meal to see calories and protein. Numbers come from a desi food table built on USDA data."
        actions={
          <>
            <Button variant={canSnap ? 'secondary' : 'primary'} onClick={openManual} disabled={!foods.data}>
              <Plus size={16} weight="bold" />
              Add by hand
            </Button>
            <Button variant={canSnap ? 'primary' : 'secondary'} onClick={() => fileInput.current?.click()} disabled={!foods.data}>
              <Camera size={16} weight="bold" />
              Snap a meal
            </Button>
          </>
        }
      />
      <input ref={fileInput} type="file" accept="image/*" capture="environment" className="hidden" onChange={onPhoto} />

      <div className="mb-5 flex items-center gap-2">
        <Button size="icon" variant="ghost" aria-label="Previous day" onClick={() => setOffset((o) => o - 1)}>
          <CaretLeft size={18} />
        </Button>
        <span className="min-w-[9rem] text-center text-[15px] font-semibold">{dayName}</span>
        <Button size="icon" variant="ghost" aria-label="Next day" disabled={offset >= 0} onClick={() => setOffset((o) => o + 1)}>
          <CaretRight size={18} />
        </Button>
      </div>

      {day.error ? (
        <ErrorNotice message={day.error} onRetry={day.reload} />
      ) : day.loading && !data ? (
        <Skeleton className="h-60 rounded-card" />
      ) : data ? (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)]">
          <Reveal>
            <Panel className="flex flex-col gap-5 p-5">
              <Bar label="Calories" value={data.totals.kcal} target={data.targets?.kcal ?? null} unit="kcal" />
              <Bar label="Protein" value={data.totals.protein_g} target={data.targets?.protein_g ?? null} unit="g" />
              <p className="text-[13px] tabular text-muted">
                Carbs {Math.round(data.totals.carbs_g)} g · Fat {Math.round(data.totals.fat_g)} g
              </p>
              <div className="flex gap-3 rounded-control bg-sunken p-3.5">
                <Sparkle size={18} weight="fill" className="mt-0.5 shrink-0 text-accent" aria-hidden />
                <p className="text-[15px] leading-relaxed">{ur ? data.tip.ur : data.tip.en}</p>
              </div>
              {!data.photo_recognition && (
                <p className="text-[13px] text-muted">Photo recognition isn’t switched on yet, so add meals by hand for now.</p>
              )}
            </Panel>
          </Reveal>

          <Reveal delay={0.06}>
            {data.meals.length === 0 ? (
              <EmptyState
                icon={<ForkKnife size={22} />}
                title={`No meals ${offset === 0 ? 'yet today' : 'on this day'}`}
                body="Take a photo of your plate, or add what you ate by hand."
                action={
                  offset === 0 ? (
                    <Button onClick={() => fileInput.current?.click()} disabled={!foods.data}>
                      <Camera size={16} weight="bold" />
                      Snap a meal
                    </Button>
                  ) : undefined
                }
              />
            ) : (
              <Panel>
                <h2 className="border-b border-line px-5 py-3.5 text-sm font-semibold">Meals</h2>
                <ul className="divide-y divide-line">
                  {data.meals.map((meal) => (
                    <li key={meal.id} className="flex items-start justify-between gap-3 px-5 py-3.5">
                      <div className="min-w-0">
                        <p className="text-[15px] font-medium">{mealTitle(meal, ur)}</p>
                        <p className="text-[13px] tabular text-muted">
                          {new Date(meal.eaten_at).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })} ·{' '}
                          {Math.round(meal.kcal)} kcal · {meal.protein_g.toFixed(1)} g protein
                          {meal.source === 'photo' && ' · from photo'}
                        </p>
                      </div>
                      <button
                        onClick={async () => {
                          try {
                            await api(`/ai/meals/${meal.id}`, { method: 'DELETE' });
                            toast('Meal deleted');
                            day.reload();
                          } catch (err) {
                            toast((err as Error).message);
                          }
                        }}
                        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-control text-muted hover:bg-sunken hover:text-danger"
                        aria-label="Delete meal"
                      >
                        <Trash size={16} />
                      </button>
                    </li>
                  ))}
                </ul>
              </Panel>
            )}
          </Reveal>
        </div>
      ) : null}

      <Dialog open={reading !== null} onClose={() => {}} title="Reading your plate…" description="This takes a few seconds.">
        <div className="flex flex-col items-center gap-4">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {reading && <img src={reading} alt="Your meal" className="max-h-56 w-full rounded-control object-cover opacity-80" />}
          <span className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-r-transparent" aria-hidden />
        </div>
      </Dialog>

      {editor && foods.data && (
        <MealEditor
          key={editor.key}
          open
          onClose={() => setEditor(null)}
          onSaved={day.reload}
          foods={foods.data}
          initial={editor}
        />
      )}
    </>
  );
}
