'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowCounterClockwise, Barbell, Pause, Play } from '@phosphor-icons/react';
import type { Exercise, ExerciseMedia } from '@/lib/types';
import { cn, isVideo, primaryMedia, visibleMedia } from '@/lib/utils';

function stillFor(media: ExerciseMedia) {
  return media.poster_url || media.thumbnail_url || (isVideo(media) ? null : media.media_url);
}

/** Real footage is wide; illustrations are square on white. */
function isFootage(media: ExerciseMedia) {
  return Boolean(media.width && media.height && media.width !== media.height);
}

function NoDemo({ compact }: { compact?: boolean }) {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-2 bg-sunken text-faint">
      <Barbell size={compact ? 26 : 40} />
      {!compact && <span className="text-sm">No demo for this exercise yet</span>}
    </div>
  );
}

/** Small square still for list rows; neutral placeholder when there's no demo. */
export function MiniThumb({ exercise, className }: { exercise: Exercise | null; className?: string }) {
  const media = exercise ? primaryMedia(exercise) : null;
  const still = media ? stillFor(media) : null;
  return (
    <div className={cn('flex shrink-0 items-center justify-center overflow-hidden rounded-[8px] border border-line', still ? 'bg-white' : 'bg-sunken text-faint', className)}>
      {still ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={still} alt="" loading="lazy" className={cn('h-full w-full', media && isFootage(media) ? 'object-cover' : 'object-contain')} />
      ) : (
        exercise && <Barbell size={18} />
      )}
    </div>
  );
}

/** Card thumbnail: shows the poster, plays the clip only while hovered (pointer devices). */
export function ExerciseThumb({ exercise, className }: { exercise: Exercise; className?: string }) {
  const media = primaryMedia(exercise);
  const video = useRef<HTMLVideoElement>(null);
  const [hovering, setHovering] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const el = video.current;
    if (!el) return;
    if (hovering) el.play().catch(() => {});
    else {
      el.pause();
      el.currentTime = 0;
    }
  }, [hovering]);

  const still = media ? stillFor(media) : null;
  const canHoverPlay =
    media && isVideo(media) && typeof window !== 'undefined' && window.matchMedia('(hover: hover)').matches;

  return (
    <div
      className={cn('relative aspect-square overflow-hidden bg-white', className)}
      onPointerEnter={() => setHovering(true)}
      onPointerLeave={() => setHovering(false)}
    >
      {!media || failed ? (
        <NoDemo compact />
      ) : (
        <>
          {still && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={still}
              alt={`${exercise.name} demonstration`}
              loading="lazy"
              decoding="async"
              onError={() => setFailed(true)}
              className={cn('h-full w-full', isFootage(media) ? 'object-cover' : 'object-contain')}
            />
          )}
          {canHoverPlay && (
            <video
              ref={video}
              src={hovering ? media.media_url : undefined}
              muted
              loop
              playsInline
              preload="none"
              className={cn(
                'absolute inset-0 h-full w-full transition-opacity duration-300',
                isFootage(media) ? 'object-cover' : 'object-contain',
                hovering ? 'opacity-100' : 'opacity-0',
              )}
            />
          )}
          {isVideo(media) && (
            <span className="absolute bottom-2 left-2 flex h-6 items-center gap-1 rounded-full bg-[rgb(20_33_61)] px-2 text-[11px] font-medium text-white">
              <Play size={10} weight="fill" />
              Demo
            </span>
          )}
        </>
      )}
    </div>
  );
}

function sourceLabel(media: ExerciseMedia) {
  if (media.camera_angle === 'Real video') return 'Video';
  if (isVideo(media)) return 'Animation';
  return 'Photo';
}

/** Full-size player with source switcher and playback controls. Credits for every demo live on /credits. */
export function ExercisePlayer({ exercise }: { exercise: Exercise }) {
  const all = useMemo(() => visibleMedia(exercise), [exercise]);
  const [failed, setFailed] = useState<string[]>([]);
  const sources = all.filter((m) => !failed.includes(m.id));
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const media = sources.find((m) => m.id === selectedId) ?? sources[0] ?? null;
  const video = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    if (video.current) video.current.playbackRate = speed;
  }, [speed, media?.id]);

  const toggle = () => {
    const el = video.current;
    if (!el) return;
    if (el.paused) el.play().catch(() => {});
    else el.pause();
  };

  return (
    <figure className="overflow-hidden rounded-card border border-line bg-surface shadow-card">
      <div
        className={cn('relative', media && isFootage(media) ? 'bg-[rgb(20_33_61)]' : 'aspect-square bg-white sm:aspect-[4/3]')}
        style={media && isFootage(media) ? { aspectRatio: `${media.width} / ${media.height}` } : undefined}
      >
        {!media ? (
          <NoDemo />
        ) : isVideo(media) ? (
          <video
            key={media.id}
            ref={video}
            src={media.media_url}
            poster={media.poster_url ?? undefined}
            autoPlay
            muted
            loop
            playsInline
            preload="metadata"
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onError={() => setFailed((list) => [...list, media.id])}
            aria-label={`${exercise.name} demonstration`}
            className="h-full w-full object-contain"
          />
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            key={media.id}
            src={media.media_url}
            alt={`${exercise.name} demonstration`}
            onError={() => setFailed((list) => [...list, media.id])}
            className="h-full w-full object-contain"
          />
        )}
      </div>

      {media && (
        <div className="flex flex-col gap-3 border-t border-line px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-1.5">
            {isVideo(media) && (
              <>
                <button
                  onClick={toggle}
                  className="flex h-9 w-9 items-center justify-center rounded-control bg-sunken text-ink transition-colors hover:bg-line"
                  aria-label={playing ? 'Pause' : 'Play'}
                >
                  {playing ? <Pause size={16} weight="fill" /> : <Play size={16} weight="fill" />}
                </button>
                <button
                  onClick={() => {
                    if (!video.current) return;
                    video.current.currentTime = 0;
                    video.current.play().catch(() => {});
                  }}
                  className="flex h-9 w-9 items-center justify-center rounded-control text-muted transition-colors hover:bg-sunken hover:text-ink"
                  aria-label="Replay"
                >
                  <ArrowCounterClockwise size={16} />
                </button>
                <div className="ml-1 flex rounded-control bg-sunken p-0.5" role="group" aria-label="Playback speed">
                  {[0.5, 1].map((value) => (
                    <button
                      key={value}
                      onClick={() => setSpeed(value)}
                      aria-pressed={speed === value}
                      className={cn(
                        'h-8 rounded-[8px] px-2.5 text-xs font-medium tabular transition-colors',
                        speed === value ? 'bg-surface text-ink shadow-sm' : 'text-muted hover:text-ink',
                      )}
                    >
                      {value === 1 ? 'Normal' : 'Slow'}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
          {sources.length > 1 && (
            <div className="flex gap-1 overflow-x-auto scrollbar-none" role="tablist" aria-label="Demo source">
              {sources.map((item) => (
                <button
                  key={item.id}
                  role="tab"
                  aria-selected={item.id === media.id}
                  onClick={() => setSelectedId(item.id)}
                  className={cn(
                    'h-8 shrink-0 rounded-full border px-3 text-xs font-medium transition-colors',
                    item.id === media.id
                      ? 'border-accent bg-accent-soft text-accent'
                      : 'border-line text-muted hover:border-faint/60 hover:text-ink',
                  )}
                >
                  {(() => {
                    const same = sources.filter((s) => sourceLabel(s) === sourceLabel(item));
                    return same.length > 1 ? `${sourceLabel(item)} ${same.indexOf(item) + 1}` : sourceLabel(item);
                  })()}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </figure>
  );
}
