// LiftAndPlate WhatsApp gateway (unofficial).
//
// Links one WhatsApp number as a "linked device" (like WhatsApp Web) with the Baileys library, passes each chat
// message to the backend (POST /messaging/gateway/incoming, signed with GATEWAY_SECRET) and sends back the reply.
// It only ever answers messages people send it: no bulk or first-contact messages, which keeps the ban risk low.
//
// Run: copy .env.example to .env, fill GATEWAY_SECRET, `npm install`, `npm start`, then scan the QR shown in the
// terminal (or at http://127.0.0.1:3100/qr) from the bot phone: WhatsApp → Settings → Linked devices → Link a device.
import { createHmac } from 'node:crypto'
import { rm } from 'node:fs/promises'
import { createServer } from 'node:http'
import makeWASocket, {
  Browsers, DisconnectReason, fetchLatestBaileysVersion, isJidBroadcast, isJidGroup, isJidNewsletter,
  isJidStatusBroadcast, jidDecode, normalizeMessageContent, useMultiFileAuthState,
} from 'baileys'
import pino from 'pino'
import QRCode from 'qrcode'

const BACKEND_URL = (process.env.BACKEND_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/+$/, '')
const SECRET = process.env.GATEWAY_SECRET || ''
const HOST = process.env.HOST || '127.0.0.1'
const PORT = Number(process.env.PORT || 3100)
const QR_PAGE_TOKEN = process.env.QR_PAGE_TOKEN || ''
const AUTH_DIR = process.env.AUTH_DIR || './auth'
const MAX_PER_MINUTE = 20 // per sender; anything above is ignored (spam or a loop)

if (!SECRET) {
  console.error('GATEWAY_SECRET is not set. Copy .env.example to .env and use the same value as the backend.')
  process.exit(1)
}

const log = pino({ level: process.env.LOG_LEVEL || 'info' })
const state = { status: 'starting', qr: null, number: null }
let sock = null

// Incoming messages -------------------------------------------------------------------------------------------

/** The member's address: phone digits when WhatsApp tells us the number, otherwise the stable LID ("lid:…"). */
function senderOf(key) {
  for (const jid of [key.remoteJidAlt, key.senderPn, key.remoteJid]) {
    if (jid && jid.endsWith('@s.whatsapp.net')) return jidDecode(jid)?.user?.replace(/\D/g, '') || null
  }
  const lid = jidDecode(key.remoteJid)?.user
  return lid ? `lid:${lid}` : null
}

function contentOf(message) {
  const m = normalizeMessageContent(message)
  if (!m) return null
  const text = m.conversation || m.extendedTextMessage?.text
  if (text) return { kind: 'text', text }
  if (m.imageMessage) return { kind: 'image', text: m.imageMessage.caption || '' }
  if (m.audioMessage) return { kind: 'audio', text: '' }
  if (m.videoMessage || m.documentMessage || m.stickerMessage || m.locationMessage || m.contactMessage) {
    return { kind: 'other', text: '' }
  }
  return null // reactions, edits, receipts, key exchanges: nothing to answer
}

const recent = new Map() // sender → timestamps of the last minute
function tooMany(sender) {
  const now = Date.now()
  const times = (recent.get(sender) || []).filter((t) => now - t < 60_000)
  times.push(now)
  recent.set(sender, times)
  return times.length > MAX_PER_MINUTE
}

async function askBackend(payload) {
  const body = JSON.stringify(payload)
  const signature = 'sha256=' + createHmac('sha256', SECRET).update(body).digest('hex')
  const response = await fetch(`${BACKEND_URL}/messaging/gateway/incoming`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Gateway-Signature': signature },
    body,
    signal: AbortSignal.timeout(20_000),
  })
  if (!response.ok) throw new Error(`backend answered HTTP ${response.status}`)
  return (await response.json()).reply || null
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function handle(msg) {
  const { key } = msg
  const jid = key?.remoteJid
  if (!jid || key.fromMe) return
  if (isJidGroup(jid) || isJidBroadcast(jid) || isJidStatusBroadcast(jid) || isJidNewsletter(jid)) return
  const content = contentOf(msg.message)
  const sender = senderOf(key)
  if (!content || !sender || !key.id) return
  if (tooMany(sender)) return log.warn({ last4: sender.slice(-4) }, 'too many messages, ignored')

  try {
    await sock.readMessages([key])
    await sock.sendPresenceUpdate('composing', jid)
    const reply = await askBackend({ message_id: key.id, sender, kind: content.kind, text: content.text.slice(0, 4000) })
    if (reply) {
      await sleep(600 + Math.random() * 900) // answer at a human pace
      await sock.sendMessage(jid, { text: reply })
    }
  } catch (error) {
    log.error({ err: error.message }, 'message failed')
  } finally {
    sock.sendPresenceUpdate('paused', jid).catch(() => {})
  }
}

// Connection --------------------------------------------------------------------------------------------------

async function start() {
  const { state: auth, saveCreds } = await useMultiFileAuthState(AUTH_DIR)
  const { version } = await fetchLatestBaileysVersion()
  sock = makeWASocket({
    version,
    auth,
    logger: log.child({ module: 'baileys' }, { level: 'warn' }),
    browser: Browsers.ubuntu('LiftAndPlate'),
    markOnlineOnConnect: false,
    syncFullHistory: false,
  })
  sock.ev.on('creds.update', saveCreds)
  sock.ev.on('messages.upsert', ({ messages, type }) => {
    if (type !== 'notify') return // skip history sync
    for (const msg of messages) handle(msg)
  })
  sock.ev.on('connection.update', async ({ connection, lastDisconnect, qr }) => {
    if (qr) {
      state.status = 'waiting_for_scan'
      state.qr = qr
      console.log('\nScan with the bot phone: WhatsApp → Settings → Linked devices → Link a device\n')
      console.log(await QRCode.toString(qr, { type: 'terminal', small: true }))
      console.log(`Or open http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}/qr\n`)
    }
    if (connection === 'open') {
      state.status = 'connected'
      state.qr = null
      state.number = jidDecode(sock.user?.id)?.user || null
      log.info({ last4: state.number?.slice(-4) }, 'WhatsApp connected')
    }
    if (connection === 'close') {
      const code = lastDisconnect?.error?.output?.statusCode
      if (code === DisconnectReason.loggedOut) {
        // Unlinked from the phone: forget the session and show a new QR.
        log.warn('logged out from the phone; a new QR will be shown')
        state.status = 'logged_out'
        state.number = null
        await rm(AUTH_DIR, { recursive: true, force: true })
      } else {
        state.status = 'reconnecting'
        log.warn({ code }, 'connection closed, reconnecting')
      }
      setTimeout(() => start().catch((error) => log.error(error, 'restart failed')), 3000)
    }
  })
}

// Status and QR page -----------------------------------------------------------------------------------------

createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost')
  if (url.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' })
    return res.end(JSON.stringify({ status: state.status, last4: state.number?.slice(-4) || null }))
  }
  if (url.pathname === '/qr') {
    if (QR_PAGE_TOKEN && url.searchParams.get('token') !== QR_PAGE_TOKEN) {
      res.writeHead(403)
      return res.end('Forbidden')
    }
    const qr = state.qr ? await QRCode.toString(state.qr, { type: 'svg', margin: 2, width: 320 }) : ''
    const note = state.status === 'connected'
      ? `Connected ✅ (number ending ${state.number?.slice(-4) || '?'})`
      : qr ? 'Scan with the bot phone: WhatsApp → Settings → Linked devices → Link a device. The code changes every few seconds.'
        : `Status: ${state.status}…`
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' })
    return res.end(`<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="5">
<title>LiftAndPlate WhatsApp</title><body style="font-family:system-ui;text-align:center;padding:24px">
<h2>LiftAndPlate WhatsApp gateway</h2><p>${note}</p><div style="display:inline-block">${qr}</div></body>`)
  }
  res.writeHead(404)
  res.end()
}).listen(PORT, HOST, () => log.info(`status page on http://${HOST}:${PORT}/qr`))

start().catch((error) => {
  log.error(error, 'could not start')
  process.exit(1)
})
