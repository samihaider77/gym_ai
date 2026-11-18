'use client';

import { useCallback, useEffect, useState } from 'react';
import { ArrowSquareOut, ArrowsClockwise, WhatsappLogo } from '@phosphor-icons/react';
import { Panel } from '@/components/page';
import { Button, buttonStyles } from '@/components/ui/button';
import { Dialog } from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/feedback';
import { useToast } from '@/components/ui/toast';
import { api } from '@/lib/api';
import { useLanguage } from '@/lib/i18n';
import type { ChatLinkCode, ChatLinkStatus } from '@/lib/types';
import { cn } from '@/lib/utils';

function secondsLeft(expiresAt: string) {
  return Math.max(0, Math.round((new Date(expiresAt).getTime() - Date.now()) / 1000));
}

function Countdown({ seconds }: { seconds: number }) {
  const m = Math.floor(seconds / 60);
  const s = String(seconds % 60).padStart(2, '0');
  return <span className="tabular-nums">{`${m}:${s}`}</span>;
}

/** Profile card: link the member's WhatsApp with a one-time QR code, show the link, disconnect. */
export function WhatsAppConnect() {
  const toast = useToast();
  const { lang } = useLanguage();
  const [status, setStatus] = useState<ChatLinkStatus | null>(null);
  const [code, setCode] = useState<ChatLinkCode | null>(null);
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [left, setLeft] = useState(0);
  const [confirming, setConfirming] = useState(false);
  const [removing, setRemoving] = useState(false);

  const refresh = useCallback(() => api<ChatLinkStatus>('/messaging/link').then(setStatus), []);

  useEffect(() => {
    refresh().catch(() => setStatus(null));
  }, [refresh]);

  const newCode = useCallback(async () => {
    setCreating(true);
    try {
      const created = await api<ChatLinkCode>('/messaging/link', {
        method: 'POST',
        body: { language: lang, utc_offset_minutes: -new Date().getTimezoneOffset() },
      });
      setCode(created);
      setLeft(secondsLeft(created.expires_at));
      setOpen(true);
    } catch (err) {
      toast((err as Error).message, 'error');
    } finally {
      setCreating(false);
    }
  }, [lang, toast]);

  // While the QR is open: count down, and check every few seconds whether the member has sent the code.
  useEffect(() => {
    if (!open || !code) return;
    const tick = setInterval(() => setLeft(secondsLeft(code.expires_at)), 1000);
    const poll = setInterval(async () => {
      try {
        const latest = await api<ChatLinkStatus>('/messaging/link');
        if (latest.linked) {
          setStatus(latest);
          setOpen(false);
          setCode(null);
          toast(`WhatsApp connected (•••• ${latest.last4})`);
        }
      } catch {
        /* keep waiting */
      }
    }, 3000);
    return () => {
      clearInterval(tick);
      clearInterval(poll);
    };
  }, [open, code, toast]);

  async function disconnect() {
    setRemoving(true);
    try {
      await api('/messaging/link', { method: 'DELETE' });
      await refresh();
      setConfirming(false);
      toast('WhatsApp disconnected');
    } catch (err) {
      toast((err as Error).message, 'error');
    } finally {
      setRemoving(false);
    }
  }

  const expired = code !== null && left === 0;

  return (
    <Panel className="p-5">
      <div className="flex items-center gap-2">
        <WhatsappLogo size={20} weight="fill" className="text-[#1fa855]" aria-hidden />
        <p className="text-sm font-semibold">WhatsApp Coach</p>
      </div>

      {status === null ? (
        <Skeleton className="mt-4 h-16" />
      ) : status.linked ? (
        <div className="mt-3 flex flex-col gap-3">
          <p className="text-sm">
            Connected to <span className="font-medium tabular-nums">•••• {status.last4}</span>
          </p>
          <p className="text-[13px] text-muted">
            Send <b>today</b>, <b>diet</b> or <b>help</b> to LiftAndPlate on WhatsApp.
          </p>
          {confirming ? (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[13px] text-muted">Stop WhatsApp messages?</span>
              <Button size="sm" variant="danger" loading={removing} onClick={disconnect}>
                Disconnect
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setConfirming(false)}>
                Keep
              </Button>
            </div>
          ) : (
            <Button size="sm" variant="secondary" className="self-start" onClick={() => setConfirming(true)}>
              Disconnect
            </Button>
          )}
        </div>
      ) : status.bot_ready ? (
        <div className="mt-3 flex flex-col gap-3">
          <p className="text-[13px] text-muted">
            Ask for today&apos;s workout or your diet targets from WhatsApp, without opening the app.
          </p>
          <Button size="sm" className="self-start" loading={creating} onClick={newCode}>
            Connect WhatsApp
          </Button>
        </div>
      ) : (
        <p className="mt-3 text-[13px] text-muted">Coming soon: ask for your workout and diet from WhatsApp.</p>
      )}

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Connect WhatsApp"
        description="Scan with your phone camera, then tap Send in WhatsApp."
      >
        {code && (
          <div className="flex flex-col items-center gap-4">
            {code.qr_svg && (
              <div
                className={cn('w-56 max-w-full rounded-card bg-white p-2 transition-opacity [&>svg]:h-auto [&>svg]:w-full', expired && 'opacity-20')}
                aria-label="QR code that opens WhatsApp with your code"
                role="img"
                // The SVG is made by our own API from the wa.me link; it contains no user input.
                dangerouslySetInnerHTML={{ __html: code.qr_svg }}
              />
            )}
            <p className="text-center text-sm">
              It opens a chat with <b>LiftAndPlate</b> with <span className="font-mono">{code.message}</span> typed.
            </p>
            {expired ? (
              <Button loading={creating} onClick={newCode}>
                <ArrowsClockwise size={16} aria-hidden /> New code
              </Button>
            ) : (
              <>
                <p className="text-[13px] text-muted">
                  Works once · expires in <Countdown seconds={left} />
                </p>
                {code.wa_link && (
                  <a href={code.wa_link} target="_blank" rel="noreferrer" className={cn(buttonStyles({ variant: 'secondary' }))}>
                    On this phone? Open WhatsApp <ArrowSquareOut size={16} aria-hidden />
                  </a>
                )}
              </>
            )}
            <p className="text-center text-[12px] text-faint">Waiting for your message. This closes by itself once you&apos;re connected.</p>
          </div>
        )}
      </Dialog>
    </Panel>
  );
}
