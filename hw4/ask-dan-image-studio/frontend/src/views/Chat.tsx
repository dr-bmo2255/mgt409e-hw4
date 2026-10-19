import { useCallback, useEffect, useRef, useState } from 'react'
import { STATUS_COLORS, file, get, money, post, type Asset, type AssetDetail } from '../api'
import type { OverviewData } from './Overview'

type Brief = {
  display_name: string
  setting: string
  outfit: string
  pose: string
  humor: string
  permitted_text: string[]
  shield_slug: string | null
}
type Msg = { id: number; role: 'user' | 'assistant' | 'system'; content: string; brief: Brief | null; revise_feedback: string | null; asset_id: string | null }
type Shield = { slug: string; label: string; path: string }
type Go = (t: 'review', a?: string) => void

const SUGGESTIONS = [
  'Dan as a Yale cheerleader at the Yale Bowl, pom-poms flying',
  'Dan reading in Sterling Memorial Library wearing reading glasses',
  'Dan in a Santa hat with a Yale scarf by a fireplace, for a holiday promo',
]

export default function Chat({ overview, refresh, go }: { overview: OverviewData | null; refresh: () => void; go: Go }) {
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [shields, setShields] = useState<Shield[]>([])
  const [customs, setCustoms] = useState<Asset[]>([])
  const [focus, setFocus] = useState<string>('')
  const listRef = useRef<HTMLDivElement>(null)
  const paid = overview?.provider === 'openai'

  const loadCustoms = useCallback(() => get<Asset[]>('/api/assets').then((a) => setCustoms(a.filter((x) => x.group === 'Custom'))), [])
  useEffect(() => {
    get<Msg[]>('/api/chat').then(setMsgs)
    get<{ shields: Shield[] }>('/api/settings').then((s) => setShields(s.shields))
    loadCustoms()
    const t = setInterval(loadCustoms, 3000)
    return () => clearInterval(t)
  }, [loadCustoms])
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [msgs, busy])

  async function send(text: string) {
    const message = text.trim()
    if (!message || busy) return
    setBusy(true)
    setErr(null)
    setMsgs((m) => [...m, { id: -Date.now(), role: 'user', content: message, brief: null, revise_feedback: null, asset_id: focus || null }])
    setInput('')
    try {
      await post('/api/chat', { message, focus_asset: focus || null })
      setMsgs(await get<Msg[]>('/api/chat'))
    } catch (e) {
      setErr((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  // Paid generation always shows the cost and asks first; mock is free.
  async function generateFor(assetId: string, body: Record<string, unknown> = {}) {
    const detail = await get<AssetDetail>(`/api/assets/${assetId}`)
    if (paid) {
      const ok = window.confirm(
        `Generate ONE paid image for "${detail.display_name}"?\n\nEstimated ${money(detail.estimate_usd)} (calibrated from actual usage). ` +
          `Spent so far ${money(overview?.spent_usd)} of the ${money(overview?.cost_cap_usd)} cap.`,
      )
      if (!ok) return false
      await post('/api/authorize/single', { asset_ids: [assetId], budget_usd: Math.max(0.05, detail.estimate_usd * 1.5), confirm: true })
    }
    await post(`/api/assets/${assetId}/generate`, body)
    refresh()
    loadCustoms()
    return true
  }

  async function createAndGenerate(brief: Brief) {
    setErr(null)
    try {
      const a = await post<Asset>('/api/custom', brief)
      setFocus(a.asset_id)
      setMsgs(await get<Msg[]>('/api/chat'))
      await generateFor(a.asset_id)
    } catch (e) {
      setErr((e as Error).message)
    }
  }

  async function revise(assetId: string, feedback: string) {
    setErr(null)
    try {
      const d = await get<AssetDetail>(`/api/assets/${assetId}`)
      const v = d.versions.at(-1)
      if (!v) return setErr('That image has no version yet. Generate it first.')
      await post(`/api/assets/${assetId}/revise`, { version: v.version, text: feedback })
      await generateFor(assetId, { feedback, parent_version: v.version })
    } catch (e) {
      setErr((e as Error).message)
    }
  }

  return (
    <div className="chat-layout">
      <section className="card chat-main">
        <div className="toolbar">
          <h2>Ask Dan chat: one-off images</h2>
          <label className="small">
            “this” refers to{' '}
            <select value={focus} onChange={(e) => setFocus(e.target.value)}>
              <option value="">(nothing selected)</option>
              {customs.map((c) => (
                <option key={c.asset_id} value={c.asset_id}>
                  {c.display_name}
                </option>
              ))}
            </select>
          </label>
          <button
            className="btn small ghost"
            onClick={async () => {
              if (!window.confirm('Clear the chat transcript? (Images are kept.)')) return
              await fetch('/api/chat', { method: 'DELETE' })
              setMsgs([])
            }}
          >
            Clear chat
          </button>
        </div>
        <p className="small muted">
          Describe any Dan image, even one the catalogue doesn't need yet. The agent drafts a brief (editable) using the same identity references,
          exact-text rules and official shields. Nothing is generated or charged until you click <b>Create &amp; generate</b>
          {paid ? ' (you see the cost first)' : ' (mock provider: free placeholders)'}.
        </p>

        <div className="chat-list-studio" ref={listRef}>
          {msgs.length === 0 && (
            <div className="chat-suggest">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="pick-item" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}
          {msgs.map((m) => (
            <div key={m.id} className={`cmsg cmsg-${m.role}`}>
              <div className="cbubble">{m.content}</div>
              {m.brief && <BriefCard brief={m.brief} shields={shields} paid={paid} onCreate={createAndGenerate} />}
              {m.revise_feedback && m.asset_id && (
                <div className="brief-card revise-card">
                  <b>Proposed revision for {m.asset_id}</b>
                  <p className="small">{m.revise_feedback}</p>
                  <button className="btn revise" onClick={() => revise(m.asset_id!, m.revise_feedback!)}>
                    ✎ Generate revision {paid ? '(cost shown first)' : '(mock $0)'}
                  </button>
                </div>
              )}
            </div>
          ))}
          {busy && <div className="cmsg cmsg-assistant"><div className="cbubble muted">🐶 sketching a brief…</div></div>}
        </div>
        {err && <div className="banner error small">{err}</div>}
        <form
          className="chat-input"
          onSubmit={(e) => {
            e.preventDefault()
            void send(input)
          }}
        >
          <textarea
            rows={2}
            value={input}
            placeholder={focus ? `Describe a new image, or a change to "${customs.find((c) => c.asset_id === focus)?.display_name}"…` : 'Describe a Dan image…'}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                void send(input)
              }
            }}
          />
          <button className="btn primary" disabled={busy || !input.trim()}>
            Send
          </button>
        </form>
      </section>

      <aside className="card chat-side">
        <h3>One-off images ({customs.length})</h3>
        {customs.length === 0 && <p className="small muted">None yet. They'll appear here as you create them.</p>}
        <div className="custom-list">
          {[...customs].reverse().map((c) => (
            <div key={c.asset_id} className={`custom-item ${focus === c.asset_id ? 'on' : ''}`}>
              <button className="custom-thumb" onClick={() => setFocus(c.asset_id)} title="Make this what “this” refers to">
                {c.latest_thumb ? <img src={file(c.latest_thumb)} alt="" /> : <span>{c.status === 'QUEUED' || c.status === 'GENERATING' ? '⏳' : '—'}</span>}
              </button>
              <div>
                <b className="small">{c.display_name}</b>
                <span className="chip" style={{ borderColor: STATUS_COLORS[c.status], color: STATUS_COLORS[c.status] }}>
                  {c.status.replace(/_/g, ' ')}
                </span>
                <div className="row-actions">
                  <button className="link small" onClick={() => go('review', c.asset_id)}>
                    Open in Review
                  </button>
                  {c.status === 'MISSING' || c.status === 'FAILED' ? (
                    <button className="link small" onClick={() => generateFor(c.asset_id).catch((e) => setErr((e as Error).message))}>
                      Generate
                    </button>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
        <p className="small muted">
          Approve, compare versions, place exact shields and reject in <b>Generate / Review</b>. Approved one-offs export to <code>custom_png/</code>, separate from the catalogue set.
        </p>
      </aside>
    </div>
  )
}

function BriefCard({ brief, shields, paid, onCreate }: { brief: Brief; shields: Shield[]; paid: boolean; onCreate: (b: Brief) => void }) {
  const [b, setB] = useState<Brief>(brief)
  const [done, setDone] = useState(false)
  const field = (k: 'display_name' | 'setting' | 'outfit' | 'pose' | 'humor', rows = 1) => (
    <label className="bf">
      <span>{k.replace('_', ' ')}</span>
      {rows > 1 ? (
        <textarea rows={rows} value={b[k]} onChange={(e) => setB({ ...b, [k]: e.target.value })} />
      ) : (
        <input value={b[k]} onChange={(e) => setB({ ...b, [k]: e.target.value })} />
      )}
    </label>
  )
  return (
    <div className="brief-card">
      <b>Draft brief</b>
      {field('display_name')}
      {field('setting', 2)}
      {field('outfit', 2)}
      {field('pose', 2)}
      {field('humor', 2)}
      <label className="bf">
        <span>allowed text</span>
        <input value={b.permitted_text.join(', ')} onChange={(e) => setB({ ...b, permitted_text: e.target.value.split(',').map((w) => w.trim()).filter(Boolean) })} />
      </label>
      <label className="bf">
        <span>official shield</span>
        <select value={b.shield_slug ?? ''} onChange={(e) => setB({ ...b, shield_slug: e.target.value || null })}>
          <option value="">none</option>
          {shields.map((s) => (
            <option key={s.slug} value={s.slug}>
              {s.label}
            </option>
          ))}
        </select>
      </label>
      <button
        className="btn primary"
        disabled={done}
        onClick={() => {
          setDone(true)
          onCreate(b)
        }}
      >
        {done ? '✓ Created' : `Create & generate ${paid ? '(cost shown first)' : '(mock $0)'}`}
      </button>
    </div>
  )
}
