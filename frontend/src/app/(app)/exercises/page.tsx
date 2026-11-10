'use client';

import { Suspense, useEffect, useState, useTransition } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { motion, useReducedMotion } from 'motion/react';
import { CaretLeft, CaretRight, CircleNotch, FunnelSimple, MagnifyingGlass, X } from '@phosphor-icons/react';
import { ExerciseCard, ExerciseCardSkeleton } from '@/components/exercise-card';
import { PageHeader } from '@/components/page';
import { Button } from '@/components/ui/button';
import { EmptyState, ErrorNotice } from '@/components/ui/feedback';
import { Select } from '@/components/ui/field';
import type { Equipment, Exercise, MuscleGroup, Paginated } from '@/lib/types';
import { useApi } from '@/lib/use-api';
import { cn, titleCase } from '@/lib/utils';

const PAGE_SIZE = 24;
const TYPES = ['strength', 'cardio', 'calisthenics', 'plyometrics', 'stretching', 'flexibility'];
const LEVELS = ['beginner', 'intermediate', 'advanced'];

type FacetCount = { value: string; count: number };
type Facets = Record<'muscles' | 'equipment' | 'types' | 'levels', FacetCount[]>;

// Only offer options that return exercises under the other filters; keep the current choice
// visible even if it no longer matches, so it can be seen and cleared.
function available<T>(items: T[], value: (item: T) => string, facet: FacetCount[] | undefined, selected: string) {
  if (!facet) return items.map((item) => ({ item, count: null as number | null }));
  const counts = new Map(facet.map((f) => [f.value, f.count]));
  return items
    .filter((item) => counts.has(value(item)) || value(item) === selected)
    .map((item) => ({ item, count: counts.get(value(item)) ?? 0 }));
}

const label = (name: string, count: number | null) => (count === null ? name : `${name} (${count})`);

function Library() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const reduce = useReducedMotion();
  const [showFilters, setShowFilters] = useState(false);
  // True while new filters are applied to the URL (a route change); the list fetch follows it.
  const [navigating, startNavigation] = useTransition();
  // The URL the last filter change asked for. Set in the same click, so the loading state shows at once,
  // even before the route change starts (on Vercel it can take a second or two).
  const [requested, setRequested] = useState<string | null>(null);
  const current = params.toString();
  useEffect(() => setRequested(null), [current]);

  const search = params.get('q') ?? '';
  const muscle = params.get('muscle') ?? '';
  const equipment = params.get('equipment') ?? '';
  const type = params.get('type') ?? '';
  const level = params.get('level') ?? '';
  const page = Math.max(1, Number(params.get('page') ?? 1));
  const [term, setTerm] = useState(search);

  const update = (changes: Record<string, string | null>, resetPage = true) => {
    const next = new URLSearchParams(params.toString());
    Object.entries(changes).forEach(([key, value]) => (value ? next.set(key, value) : next.delete(key)));
    if (resetPage) next.delete('page');
    if (next.toString() !== current) setRequested(next.toString());
    startNavigation(() => router.replace(`${pathname}${next.toString() ? `?${next}` : ''}`, { scroll: false }));
  };

  // Debounce typing into the URL so every keystroke doesn't fire a request.
  useEffect(() => {
    if (term === search) return;
    const id = setTimeout(() => update({ q: term.trim() || null }), 280);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [term]);

  const muscles = useApi<Paginated<MuscleGroup>>('/muscle-groups', { query: { page_size: 100, is_active: true } });
  const equipmentList = useApi<Paginated<Equipment>>('/equipment', { query: { page_size: 100, is_active: true } });
  const query = {
    page,
    page_size: PAGE_SIZE,
    search,
    muscle_group_id: muscle,
    equipment_id: equipment,
    exercise_type: type,
    difficulty_level: level,
    has_media: true, // only exercises with a demo are listed
    is_active: true,
  };
  const list = useApi<Paginated<Exercise>>('/exercises', { query }, [JSON.stringify(query)]);
  const busy = requested !== null || navigating || list.loading;
  const { page: _page, page_size: _size, ...facetQuery } = query;
  const facets = useApi<Facets>('/exercises/facets', { query: facetQuery }, [JSON.stringify(facetQuery)]);

  const byName = <T extends { name: string }>(items: T[] | undefined) => (items ?? []).slice().sort((a, b) => a.name.localeCompare(b.name));
  const muscleOptions = available(byName(muscles.data?.items), (m) => m.id, facets.data?.muscles, muscle);
  const equipmentOptions = available(byName(equipmentList.data?.items), (m) => m.id, facets.data?.equipment, equipment);
  const typeOptions = available(TYPES, (t) => t, facets.data?.types, type);
  const levelOptions = available(LEVELS, (t) => t, facets.data?.levels, level);

  const activeFilters = [muscle, equipment, type, level].filter(Boolean).length;
  const clearAll = () => {
    setTerm('');
    update({ q: null, muscle: null, equipment: null, type: null, level: null });
  };

  return (
    <>
      <PageHeader
        title="Exercises"
        description="Search the library and watch how each movement is done before you load the bar."
      />

      <div className="sticky top-14 z-20 -mx-4 mb-6 border-b border-line bg-canvas px-4 pb-4 pt-1 sm:-mx-6 sm:px-6 lg:top-0 lg:-mx-10 lg:px-10 lg:pt-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <MagnifyingGlass size={18} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
            <input
              value={term}
              onChange={(event) => setTerm(event.target.value)}
              placeholder="Search, e.g. squat"
              aria-label="Search exercises"
              className="h-11 w-full rounded-control border border-line bg-surface pl-10 pr-10 text-[15px] text-ink placeholder:text-faint transition-colors hover:border-faint/60 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/25"
            />
            {term && (
              <button
                onClick={() => setTerm('')}
                className="absolute right-2 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full text-faint hover:bg-sunken hover:text-ink"
                aria-label="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </div>
          <Button
            variant="secondary"
            className="h-11 md:hidden"
            onClick={() => setShowFilters((v) => !v)}
            aria-expanded={showFilters}
          >
            <FunnelSimple size={18} />
            Filters{activeFilters ? ` (${activeFilters})` : ''}
          </Button>
        </div>

        <div className={cn('mt-3 grid-cols-2 gap-2 md:grid md:grid-cols-4', showFilters ? 'grid' : 'hidden')}>
          <Select aria-label="Muscle" value={muscle} onChange={(e) => update({ muscle: e.target.value })}>
            <option value="">All muscles</option>
            {muscleOptions.map(({ item, count }) => (
              <option key={item.id} value={item.id}>
                {label(item.name, count)}
              </option>
            ))}
          </Select>
          <Select aria-label="Equipment" value={equipment} onChange={(e) => update({ equipment: e.target.value })}>
            <option value="">All equipment</option>
            {equipmentOptions.map(({ item, count }) => (
              <option key={item.id} value={item.id}>
                {label(item.name, count)}
              </option>
            ))}
          </Select>
          <Select aria-label="Type" value={type} onChange={(e) => update({ type: e.target.value })}>
            <option value="">All types</option>
            {typeOptions.map(({ item, count }) => (
              <option key={item} value={item}>
                {label(titleCase(item), count)}
              </option>
            ))}
          </Select>
          <Select aria-label="Level" value={level} onChange={(e) => update({ level: e.target.value })}>
            <option value="">All levels</option>
            {levelOptions.map(({ item, count }) => (
              <option key={item} value={item}>
                {label(titleCase(item), count)}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div className="mb-4 flex min-h-8 items-center justify-between gap-3 text-sm text-muted">
        <span className="tabular" aria-live="polite">
          {busy ? (
            <span className="inline-flex items-center gap-1.5">
              <CircleNotch size={14} className="animate-spin" aria-hidden />
              Loading exercises…
            </span>
          ) : list.data ? `${list.data.total.toLocaleString()} exercise${list.data.total === 1 ? '' : 's'}` :' '}
        </span>
        {(activeFilters > 0 || search) && (
          <button onClick={clearAll} className="font-medium text-accent hover:underline">
            Clear filters
          </button>
        )}
      </div>

      {list.error ? (
        <ErrorNotice message={list.error} onRetry={list.reload} />
      ) : busy ? (
        // New filters or page: the card skeleton replaces the previous results until the new ones arrive.
        <div className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <ExerciseCardSkeleton key={i} />
          ))}
        </div>
      ) : list.data && list.data.items.length === 0 ? (
        <EmptyState
          icon={<MagnifyingGlass size={22} />}
          title="No exercises match"
          body="Try a different search or clear some filters."
          action={
            <Button variant="secondary" onClick={clearAll}>
              Clear filters
            </Button>
          }
        />
      ) : (
        <div>
          <div className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 xl:grid-cols-4">
            {list.data?.items.map((exercise, index) => (
              <motion.div
                key={exercise.id}
                initial={reduce ? false : { opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: Math.min(index, 12) * 0.025, ease: [0.16, 1, 0.3, 1] }}
              >
                <ExerciseCard exercise={exercise} />
              </motion.div>
            ))}
          </div>

          {list.data && list.data.total_pages > 1 && (
            <nav className="mt-8 flex items-center justify-center gap-3" aria-label="Pagination">
              <Button
                variant="secondary"
                size="icon"
                disabled={page <= 1}
                onClick={() => {
                  update({ page: String(page - 1) }, false);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
                aria-label="Previous page"
              >
                <CaretLeft size={16} />
              </Button>
              <span className="tabular text-sm text-muted">
                Page {page} of {list.data.total_pages}
              </span>
              <Button
                variant="secondary"
                size="icon"
                disabled={page >= list.data.total_pages}
                onClick={() => {
                  update({ page: String(page + 1) }, false);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
                aria-label="Next page"
              >
                <CaretRight size={16} />
              </Button>
            </nav>
          )}
        </div>
      )}
    </>
  );
}

export default function ExercisesPage() {
  return (
    <Suspense>
      <Library />
    </Suspense>
  );
}
