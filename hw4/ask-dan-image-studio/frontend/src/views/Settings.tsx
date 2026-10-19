import { useEffect, useState } from 'react'
import { file, get, money, post, thumb } from '../api'

type S = {
  settings: Record<string, unknown> & {
    provider: string; model: string; size: string; quality: string; cost_cap_usd: number; per_job_cap_usd: number
    max_attempts_per_asset: number; batch_size: number; references_confirmed: boolean; shields_confirmed: boolean
    dan_reference_files?: string[]; automatic_mode: boolean
  }
  key: { present: boolean; via: string | null; base_url: string | null }
  dan_reference_candidates: { filename: string; rel_path: string; disposition: string }[]
  dan_references_default: { name: string; path: string }[]
  shields: { slug: string; label: string; path: string; source: string }[]
  output_dir: string
}

export default function Settings({ refresh }: { refresh: () => void }) {
  const [s, setS] = useState<S | null>(null)
  const [msg, setMsg] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)
  const load = () => get<S>('/api/settings').then(setS)
  useEffect(() => {
    load()
  }, [])
  if (!s) return <p>Loading…</p>
  const st = s.settings
  const refs = st.dan_reference_files ?? s.dan_references_default.map((r) => r.path)

  async function save(patch: Record<string, unknown>, label = 'Saved') {
    setMsg(null)
    try {
      setS(await post<S>('/api/settings', patch))
      setMsg({ kind: 'ok', text: label })
      refresh()
    } catch (e) {
      setMsg({ kind: 'err', text: (e as Error).message })
    }
  }

  const candidates = [
    ...s.dan_references_default.filter((r) => r.name.toLowerCase().startsWith('welcome')).map((r) => ({ label: r.name, path: r.path })),
    ...s.dan_reference_candidates.map((d) => ({ label: d.filename, path: d.rel_path })),
  ]

  return (
    <div className="grid-2">
      <section className="card">
        <h2>Provider & cost controls</h2>
        <label className="field">
          Provider
          <select value={st.provider} onChange={(e) => {
            const v = e.target.value
            if (v === 'openai' && !window.confirm('Switch to the PAID OpenAI provider? Nothing is generated until you authorize the pilot or a batch.')) return
            save({ provider: v }, `Provider: ${v}`)
          }}>
            <option value="mock">Mock: free placeholders</option>
            <option value="openai">OpenAI GPT Image (paid)</option>
          </select>
        </label>
        <label className="field">
          Model
          <select value={st.model} onChange={(e) => save({ model: e.target.value })}>
            <option value="gpt-image-2.5-sunburst">gpt-image-2.5-sunburst (recommended, edits + references)</option>
            <option value="gpt-image-2.5-flare">gpt-image-2.5-flare</option>
            <option value="gpt-image-2">gpt-image-2</option>
          </select>
        </label>
        <div className="row2">
          <label className="field">
            Size
            <select value={st.size} onChange={(e) => save({ size: e.target.value })}>
              <option>1024x1024</option>
              <option>1536x1536</option>
              <option>2048x2048</option>
            </select>
          </label>
          <label className="field">
            Quality
            <select value={st.quality} onChange={(e) => save({ quality: e.target.value })}>
              {['low', 'medium', 'high', 'xhigh', 'max'].map((q) => <option key={q}>{q}</option>)}
            </select>
          </label>
        </div>
        <div className="row2">
          <label className="field">
            Hard spending cap (USD)
            <input type="number" step="1" min="0" defaultValue={st.cost_cap_usd} onBlur={(e) => save({ cost_cap_usd: Number(e.target.value) }, `Cap ${money(Number(e.target.value))}`)} />
          </label>
          <label className="field">
            Per-image cap (USD)
            <input type="number" step="0.05" min="0" defaultValue={st.per_job_cap_usd} onBlur={(e) => save({ per_job_cap_usd: Number(e.target.value) })} />
          </label>
        </div>
        <label className="field">
          Max paid attempts per asset
          <input type="number" min="1" max="10" defaultValue={st.max_attempts_per_asset} onBlur={(e) => save({ max_attempts_per_asset: Number(e.target.value) })} />
        </label>
        <p className="small">
          API key: {s.key.present ? <span className="ok">✓ present via {s.key.via}</span> : <span className="warn">✗ not found</span>} (never shown). Set
          <code>OPENAI_API_KEY</code> or <code>PORTKEY_API_KEY</code> in a local <code>.env</code>, never in this dashboard.
        </p>
        <p className="small muted">Automatic mode: <b>OFF</b> (locked). Output folder: <code>{s.output_dir}</code></p>
        <button
          className="btn small"
          onClick={async () => {
            if (!window.confirm('Remove all MOCK placeholder versions (and composites made from them)? They are archived in output/rejected/mock_demo. Paid images are never touched.')) return
            try {
              const r = await post<{ assets: Record<string, number> }>('/api/admin/clear-mock', { confirm: true })
              setMsg({ kind: 'ok', text: `Cleared mock results for ${Object.keys(r.assets).length} asset(s)` })
              refresh()
            } catch (e) {
              setMsg({ kind: 'err', text: (e as Error).message })
            }
          }}
        >
          Clear mock demo results
        </button>
        {msg && <div className={`banner ${msg.kind === 'ok' ? 'info' : 'error'} small`}>{msg.text}</div>}
      </section>

      <section className="card">
        <h2>Dan identity references</h2>
        <p className="small">
          Only approved ORIGINAL Dan images (never Dan2). Up to 4 are sent with each request. Paid generation stays blocked until you confirm.
        </p>
        <div className="ref-pick">
          {candidates.map((c) => {
            const on = refs.includes(c.path)
            return (
              <button
                key={c.path}
                className={`ref-item ${on ? 'on' : ''}`}
                onClick={() => save({ dan_reference_files: on ? refs.filter((r) => r !== c.path) : [...refs, c.path], references_confirmed: false }, 'References changed; please re-confirm')}
              >
                <img src={thumb(c.path)} alt="" loading="lazy" />
                <span>{c.label}</span>
              </button>
            )
          })}
        </div>
        <p className="small">Selected: {refs.length} (first 4 used)</p>
        <button className={`btn ${st.references_confirmed ? 'approve' : 'primary'}`} onClick={() => save({ references_confirmed: !st.references_confirmed, dan_reference_files: refs })}>
          {st.references_confirmed ? '✓ References confirmed (click to un-confirm)' : 'Confirm these Dan references'}
        </button>
      </section>

      <section className="card span-2">
        <div className="toolbar">
          <h2>Official shields ({s.shields.length})</h2>
          <button className={`btn small ${st.shields_confirmed ? 'approve' : ''}`} onClick={() => save({ shields_confirmed: !st.shields_confirmed })}>
            {st.shields_confirmed ? '✓ Mapping confirmed' : 'Confirm shield names'}
          </button>
        </div>
        <p className="small muted">
          Cropped from your labeled screenshots (label text removed, background transparent). Names come from the label printed under each shield; check them before
          paid use. These exact pixels are what gets composited.
        </p>
        <div className="shields">
          {s.shields.map((sh) => (
            <figure key={sh.slug}>
              <img src={file(sh.path)} alt={sh.label} />
              <figcaption>{sh.label}</figcaption>
            </figure>
          ))}
        </div>
      </section>
    </div>
  )
}
