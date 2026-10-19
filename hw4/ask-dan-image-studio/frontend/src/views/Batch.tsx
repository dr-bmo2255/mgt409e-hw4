import { useEffect, useState } from 'react'
import { STATUS_COLORS, get, money, post, type Asset } from '../api'
import type { OverviewData } from './Overview'

type Job = { id: number; asset_id: string; kind: string; provider: string; status: string; est_cost: number | null; error: string | null; created_at: number }
type Go = (t: 'review' | 'settings', a?: string) => void

const PILOT = ['dan_school_management', 'dan_sport_lacrosse', 'dan_hoodie']

export default function Batch({ overview, refresh, go }: { overview: OverviewData | null; refresh: () => void; go: Go }) {
  const [assets, setAssets] = useState<Asset[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [size, setSize] = useState(3)
  const [picked, setPicked] = useState<string[]>([])
  const [msg, setMsg] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)

  const load = () => {
    get<Asset[]>('/api/assets').then(setAssets)
    get<Job[]>('/api/jobs').then(setJobs)
  }
  useEffect(() => {
    load()
    const t = setInterval(load, 2500)
    return () => clearInterval(t)
  }, [])

  if (!overview) return <p>Loading…</p>
  const paid = overview.provider === 'openai'
  const per = overview.estimates.per_image
  const scoped = assets.filter((a) => a.manifest_status === 'MISSING' && a.group !== 'Custom')
  const waiting = scoped.filter((a) => a.status === 'MISSING' && !a.pilot)
  const suggestion = waiting.slice(0, size).map((a) => a.asset_id)
  const chosen = picked.length ? picked : suggestion
  const pilotAuth = overview.authorizations.find((a) => a.kind === 'pilot')
  const pilotDone = PILOT.every((id) => (scoped.find((a) => a.asset_id === id)?.version_count ?? 0) > 0)

  async function act(label: string, fn: () => Promise<unknown>) {
    setMsg(null)
    try {
      await fn()
      setMsg({ kind: 'ok', text: label })
      load()
      refresh()
    } catch (e) {
      setMsg({ kind: 'err', text: (e as Error).message })
    }
  }

  async function startPilot() {
    if (!paid) {
      return act('Mock pilot queued (3 placeholders, $0)', () => post('/api/batch/start', { asset_ids: PILOT, provider: 'mock' }))
    }
    const budget = Math.max(per * 3 * 1.5, 0.5)
    if (!window.confirm(`PAID PILOT: exactly 3 images (SOM, lacrosse, hoodie).\nEstimated ${money(per * 3)}; authorization budget ${money(budget)}.\nCap ${money(overview!.cost_cap_usd)}, spent ${money(overview!.spent_usd)}.\n\nThe studio will stop after these 3. Proceed?`)) return
    await act('Pilot authorized and queued: 3 paid images', async () => {
      if (!pilotAuth) await post('/api/authorize/pilot', { budget_usd: budget, confirm: true })
      const r = await post<{ errors: Record<string, string> }>('/api/batch/start', { asset_ids: PILOT })
      if (Object.keys(r.errors).length) throw new Error(Object.entries(r.errors).map(([k, v]) => `${k}: ${v}`).join('\n'))
    })
  }

  async function startBatch() {
    if (!chosen.length) return
    if (!paid) return act(`Mock batch queued: ${chosen.length} ($0)`, () => post('/api/batch/start', { asset_ids: chosen, provider: 'mock' }))
    const budget = Math.max(per * chosen.length * 1.5, 0.5)
    if (!window.confirm(`PAID SUPERVISED BATCH: ${chosen.length} image(s)\n${chosen.join('\n')}\n\nEstimated ${money(per * chosen.length)}; budget ${money(budget)}. The studio pauses after this batch. Proceed?`)) return
    await act(`Batch authorized and queued: ${chosen.length}`, async () => {
      await post('/api/authorize/batch', { asset_ids: chosen, budget_usd: budget, confirm: true })
      const r = await post<{ errors: Record<string, string> }>('/api/batch/start', { asset_ids: chosen })
      if (Object.keys(r.errors).length) throw new Error(Object.entries(r.errors).map(([k, v]) => `${k}: ${v}`).join('\n'))
    })
    setPicked([])
  }

  return (
    <div className="grid-2">
      <section className="card">
        <h2>Mode</h2>
        <div className="modes">
          <div className="mode on"><b>Manual</b><span>One image at a time from Generate / Review.</span></div>
          <div className="mode on"><b>Supervised batch</b><span>3 by default, max 5, then pause for your review.</span></div>
          <div className="mode off"><b>Automatic</b><span>OFF. Never enabled without your explicit approval; outputs are never auto-approved.</span></div>
        </div>
        <div className="controls">
          <button className="btn" onClick={() => act('Paused (finishes the current image, starts no more)', () => post('/api/batch/pause'))} disabled={overview.paused}>⏸ Pause</button>
          <button className="btn" onClick={() => act('Resumed', () => post('/api/batch/resume'))} disabled={!overview.paused}>▶ Resume</button>
          <button className="btn reject" onClick={() => act('Stopped: queued jobs cancelled', () => post('/api/batch/stop'))}>■ Stop (cancel queued)</button>
        </div>
        <p className="small muted">
          Provider: <b>{paid ? 'PAID (OpenAI GPT Image via ' + (overview.key.via ?? '?') + ')' : 'MOCK ($0)'}</b> ·{' '}
          <a href="#settings" onClick={() => go('settings')}>change in Settings</a>
        </p>
        {msg && <div className={`banner ${msg.kind === 'ok' ? 'info' : 'error'} small`} style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>}
      </section>

      <section className="card">
        <h2>Phase 1: three-image pilot</h2>
        <ol className="small">
          <li><b>dan_school_management</b>: Yale SOM identity, Evans Hall, executive humor, shield fidelity</li>
          <li><b>dan_sport_lacrosse</b>: action, anatomy, Dan's face</li>
          <li><b>dan_hoodie</b>: garment humor, identity, readable clothing</li>
        </ol>
        <p className="small">
          {paid ? `Estimated ${money(per * 3)} total.` : 'Mock run first is free; it exercises the whole review flow.'} The studio generates these three, then
          stops. Approve, revise or reject each one before any batch.
        </p>
        <button className="btn primary" onClick={startPilot} disabled={paid && (!overview.references_confirmed || !!pilotAuth && pilotAuth.used_images >= 3)}>
          {paid ? `Run PAID pilot (~${money(per * 3)})` : 'Run mock pilot ($0)'}
        </button>
        {paid && !overview.references_confirmed && <p className="small warn">Confirm the Dan references in Settings first.</p>}
        {pilotAuth && <p className="small">Pilot authorization: {pilotAuth.used_images}/3 used · {money(pilotAuth.spent_usd)} of {money(pilotAuth.budget_usd)}</p>}
        <p className="small">Pilot status: {overview.pilot_complete ? '✓ all three reviewed' : pilotDone ? 'generated; awaiting your review' : 'not run yet'}</p>
      </section>

      <section className="card span-2">
        <div className="toolbar">
          <h2>Phase 2: supervised batch</h2>
          <label>
            Size{' '}
            <select value={size} onChange={(e) => setSize(Number(e.target.value))}>
              {[1, 2, 3, 4, 5].map((n) => <option key={n}>{n}</option>)}
            </select>
          </label>
          <button className="btn primary" onClick={startBatch} disabled={paid && !overview.pilot_complete}>
            {paid ? `Authorize & run ${chosen.length} (~${money(per * chosen.length)})` : `Run mock batch of ${chosen.length}`}
          </button>
          {paid && !overview.pilot_complete && <span className="small warn">Review the pilot first</span>}
        </div>
        <p className="small muted">Click assets to choose a custom batch (max 5); otherwise the next {size} missing assets are used.</p>
        <div className="pick">
          {waiting.map((a) => {
            const on = chosen.includes(a.asset_id)
            return (
              <button
                key={a.asset_id}
                className={`pick-item ${on ? 'on' : ''}`}
                onClick={() =>
                  setPicked((p) => {
                    const base = p.length ? p : []
                    return base.includes(a.asset_id) ? base.filter((x) => x !== a.asset_id) : base.length < 5 ? [...base, a.asset_id] : base
                  })
                }
              >
                {a.asset_id.replace('dan_', '')}
              </button>
            )
          })}
          {waiting.length === 0 && <span className="muted">No missing assets waiting.</span>}
        </div>
      </section>

      <section className="card span-2">
        <h2>Jobs</h2>
        <table className="tbl">
          <thead>
            <tr><th>#</th><th>Asset</th><th>Kind</th><th>Provider</th><th>Est.</th><th>Status</th><th>Error</th></tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id}>
                <td>{j.id}</td>
                <td><a href={`#review/${j.asset_id}`}>{j.asset_id}</a></td>
                <td>{j.kind}</td>
                <td>{j.provider}</td>
                <td>{j.est_cost ? money(j.est_cost) : '—'}</td>
                <td><span className="chip" style={{ borderColor: STATUS_COLORS[j.status === 'done' ? 'APPROVED' : j.status === 'failed' ? 'FAILED' : 'QUEUED'] }}>{j.status}</span></td>
                <td className="small warn">{j.error}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
