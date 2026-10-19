import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { STATUS_COLORS, file, get, money, post, thumb, type Asset, type AssetDetail, type Version } from '../api'
import type { OverviewData } from './Overview'

type Go = (t: 'review' | 'settings' | 'batch', a?: string) => void

export default function Review({ assetId, go, overview, refresh }: { assetId?: string; go: Go; overview: OverviewData | null; refresh: () => void }) {
  const [list, setList] = useState<Asset[]>([])
  const [a, setA] = useState<AssetDetail | null>(null)
  const [sel, setSel] = useState<number | null>(null)
  const [cmp, setCmp] = useState<number | null>(null)
  const [feedback, setFeedback] = useState('')
  const [msg, setMsg] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [showPrompt, setShowPrompt] = useState(false)
  const [override, setOverride] = useState('')
  const [comp, setComp] = useState({ on: false, cx: 0.5, cy: 0.55, w: 0.16, rot: 0, occlusion: true, fabric: 0.85 })
  const [products, setProducts] = useState<Record<string, { photo_rel: string; name: string }>>({})
  const [danFiles, setDanFiles] = useState<Record<string, string>>({})
  const [loadErr, setLoadErr] = useState<string | null>(null)
  const seenLatest = useRef(0)

  useEffect(() => {
    get<Asset[]>('/api/assets').then(setList)
    get<{ product_id: string; photo_rel: string; name: string }[]>('/api/products').then((ps) =>
      setProducts(Object.fromEntries(ps.map((p) => [p.product_id, p]))),
    )
    get<{ dan_files: { filename: string; rel_path: string }[] }>('/api/inventory').then((inv) =>
      setDanFiles(Object.fromEntries(inv.dan_files.map((d) => [d.filename, d.rel_path]))),
    )
  }, [])

  const scoped = useMemo(() => list.filter((x) => x.manifest_status === 'MISSING' && x.group !== 'Custom'), [list])
  const id = assetId || scoped.find((x) => x.pilot)?.asset_id || scoped[0]?.asset_id

  const load: () => void = useCallback(() => {
    if (!id) return
    get<AssetDetail>(`/api/assets/${id}`)
      .then((d) => {
        setA(d)
        setLoadErr(null)
        setOverride((o) => (o === '' ? d.prompt_override ?? '' : o))
        const latest = d.versions.at(-1)?.version ?? null
        // A newly arrived version is shown automatically; otherwise keep the reviewer's selection.
        const isNew = latest !== null && latest > seenLatest.current // decide now: setState updaters run later
        seenLatest.current = latest ?? 0
        setSel((s) => (isNew ? latest : s && d.versions.some((v) => v.version === s) ? s : latest))
      })
      .catch((e) => {
        setLoadErr(String((e as Error).message))
        setTimeout(load, 2000) // transient (e.g. worker busy): retry
      })
  }, [id]) // eslint-disable-line

  useEffect(() => {
    setA(null)
    seenLatest.current = Infinity
    setSel(null)
    setCmp(null)
    setOverride('')
    setFeedback('')
    setMsg(null)
    setComp((c) => ({ ...c, on: false }))
    load()
  }, [id, load])

  const active = a?.jobs.some((j) => j.status === 'queued' || j.status === 'running')
  useEffect(() => {
    if (!active) return
    const t = setInterval(load, 1500)
    return () => clearInterval(t)
  }, [active, load])

  if (!id) return <p>Loading…</p>
  if (!a) return <p>Loading {id}…{loadErr && <span className="warn small"> ({loadErr}; retrying)</span>}</p>

  const idx = scoped.findIndex((x) => x.asset_id === a.asset_id)
  const prev = idx > 0 ? scoped[idx - 1] : null
  const next = idx >= 0 && idx < scoped.length - 1 ? scoped[idx + 1] : null
  const v: Version | undefined = a.versions.find((x) => x.version === sel)
  const vc: Version | undefined = a.versions.find((x) => x.version === cmp)
  const paid = overview?.provider === 'openai'
  const lastJob = a.jobs[0]

  async function run(label: string, fn: () => Promise<unknown>) {
    setBusy(true)
    setMsg(null)
    try {
      await fn()
      setMsg({ kind: 'ok', text: label })
      load()
      refresh()
    } catch (e) {
      setMsg({ kind: 'err', text: String((e as Error).message) })
    } finally {
      setBusy(false)
    }
  }

  async function generate(revise: boolean) {
    const body = revise && v ? { feedback, parent_version: v.version } : {}
    const doIt = () => post('/api/assets/' + a!.asset_id + '/generate', body)
    if (!paid) return run(revise ? 'Revision queued (mock, $0)' : 'Generation queued (mock, $0)', doIt)
    try {
      setBusy(true)
      await doIt()
      setMsg({ kind: 'ok', text: `Paid request queued (~${money(a!.estimate_usd)})` })
      load()
      refresh()
    } catch (e) {
      const text = String((e as Error).message)
      if (/authorization/i.test(text) && overview?.authorizations !== undefined) {
        const ok = window.confirm(
          `This will make ONE paid image request to ${'gpt-image'} (~${money(a!.estimate_usd)} estimated).\n\n` +
            `Spent so far ${money(overview?.spent_usd)} of the ${money(overview?.cost_cap_usd)} cap.\n\nAuthorize and generate?`,
        )
        if (ok) {
          await run('Authorized 1 paid image and queued', async () => {
            await post('/api/authorize/single', { asset_ids: [a!.asset_id], budget_usd: Math.max(0.05, a!.estimate_usd * 1.5), confirm: true })
            await doIt()
          })
          return
        }
      }
      setMsg({ kind: 'err', text })
    } finally {
      setBusy(false)
    }
  }

  const existingSrc = a.existing_files[0] && danFiles[a.existing_files[0]] ? file(danFiles[a.existing_files[0]]) : ''
  const mainSrc = v ? file(v.path) : existingSrc
  const qa = v?.qa_json

  return (
    <div className="review">
      <div className="review-nav">
        <button className="btn ghost" disabled={!prev} onClick={() => prev && go('review', prev.asset_id)}>
          ← Previous
        </button>
        <select value={a.asset_id} onChange={(e) => go('review', e.target.value)}>
          {list.map((x) => (
            <option key={x.asset_id} value={x.asset_id}>
              {x.group === 'Custom' ? '(one-off) ' : x.manifest_status === 'MISSING' ? '' : '(existing) '}
              {x.pilot ? '★ ' : ''}
              {x.asset_id} — {x.status}
            </option>
          ))}
        </select>
        <button className="btn ghost" disabled={!next} onClick={() => next && go('review', next.asset_id)}>
          Next →
        </button>
        <span className="muted small">{idx >= 0 ? `${idx + 1} / ${scoped.length} in scope` : 'not in generation scope'}</span>
      </div>

      <div className="review-grid">
        <section className="card stage">
          <div className="stage-head">
            <div>
              <h2>
                {a.display_name} {a.pilot && <span className="badge-pilot inline">PILOT</span>}
              </h2>
              <code>{a.canonical_filename}</code> · {a.group} · {a.product_count} product(s)
            </div>
            <span className="chip big" style={{ borderColor: STATUS_COLORS[a.status], color: STATUS_COLORS[a.status] }}>
              {a.status.replace(/_/g, ' ')}
            </span>
          </div>

          <div className={`viewer ${vc ? 'split' : ''}`}>
            <figure>
              {mainSrc ? (
                <div className="img-wrap">
                  <a href={mainSrc} target="_blank" rel="noreferrer">
                    <img src={mainSrc} alt={a.display_name} />
                  </a>
                  {comp.on && a.shield_path_effective && v && (
                    <img
                      className="shield-overlay"
                      src={file(a.shield_path_effective)}
                      style={{ left: `${comp.cx * 100}%`, top: `${comp.cy * 100}%`, width: `${comp.w * 100}%`, transform: `translate(-50%,-50%) rotate(${-comp.rot}deg)` }}
                      alt=""
                    />
                  )}
                </div>
              ) : (
                <div className="empty-stage">{active ? '⏳ Generating…' : 'No image yet: press Generate.'}</div>
              )}
              <figcaption>
                {v ? (
                  <>
                    v{v.version} · {v.kind} · {v.provider}
                    {v.provider === 'openai' ? ` · ${money(v.cost_usd)}${v.cost_is_estimate ? ' est.' : ''}` : ''} · {v.width}×{v.height} ·{' '}
                    <b>{v.decision}</b>
                  </>
                ) : existingSrc ? (
                  <>Existing asset: {a.existing_files.join('; ')} (reused, not regenerated)</>
                ) : null}
              </figcaption>
            </figure>
            {vc && (
              <figure>
                <div className="img-wrap">
                  <img src={file(vc.path)} alt="" />
                </div>
                <figcaption>
                  compare: v{vc.version} · {vc.kind} · <b>{vc.decision}</b>{' '}
                  <button className="link" onClick={() => setCmp(null)}>
                    close
                  </button>
                </figcaption>
              </figure>
            )}
          </div>

          {a.versions.length > 0 && (
            <div className="versions">
              {a.versions.map((x) => (
                <div key={x.version} className={`ver ${x.version === sel ? 'sel' : ''} dec-${x.decision}`}>
                  <button onClick={() => setSel(x.version)} title={`v${x.version} ${x.kind}`}>
                    <img src={file(x.thumb)} alt="" />
                    <span>
                      v{x.version} {x.decision === 'approved' ? '✓' : x.decision === 'rejected' ? '✗' : ''}
                    </span>
                  </button>
                  {x.version !== sel && (
                    <button className="link small" onClick={() => setCmp(x.version)}>
                      compare
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {lastJob?.status === 'failed' && <div className="banner error small">Last job failed: {lastJob.error}</div>}
          {active && <div className="banner info small">⏳ Job {lastJob?.status} via {lastJob?.provider}… the dashboard stays usable.</div>}
        </section>

        <aside className="card side">
          <h3>Review</h3>
          <textarea
            placeholder='Feedback for a revision, e.g. "make Dan look like the Babe Ruth photo; correct the SOM shield"'
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            rows={3}
          />
          <div className="actions">
            <button className="btn primary" disabled={busy || !!active} onClick={() => generate(false)}>
              {a.versions.length ? 'Generate new attempt' : 'Generate'} {paid ? `(~${money(a.estimate_usd)})` : '(mock $0)'}
            </button>
            <button className="btn approve" disabled={busy || !v || v.decision === 'approved'} onClick={() => run(`Approved v${v!.version}`, () => post(`/api/assets/${a.asset_id}/approve`, { version: v!.version }))}>
              ✓ Approve v{v?.version ?? ''}
            </button>
            <button
              className="btn revise"
              disabled={busy || !v || !feedback.trim() || !!active}
              onClick={async () => {
                await run('Feedback saved', () => post(`/api/assets/${a.asset_id}/revise`, { version: v!.version, text: feedback }))
                await generate(true)
              }}
            >
              ✎ Revise with feedback
            </button>
            <button
              className="btn reject"
              disabled={busy || !v || v.decision === 'rejected'}
              onClick={() => {
                const reason = feedback.trim() || window.prompt('Reason for rejecting (used to improve the next attempt):') || ''
                run(`Rejected v${v!.version}`, () => post(`/api/assets/${a.asset_id}/reject`, { version: v!.version, text: reason }))
              }}
            >
              ✗ Reject
            </button>
            <button className="btn ghost" disabled={!next} onClick={() => next && go('review', next.asset_id)}>
              Next asset →
            </button>
          </div>
          {msg && <div className={`banner ${msg.kind === 'ok' ? 'info' : 'error'} small`}>{msg.text}</div>}
          {!paid && <p className="small muted">Provider is MOCK: images are labeled placeholders, no API cost. Switch in Settings once the pilot is approved.</p>}

          {a.shield_path_effective && v && (
            <div className="composite">
              <label className="row">
                <input type="checkbox" checked={comp.on} onChange={(e) => setComp({ ...comp, on: e.target.checked })} /> Place exact supplied shield
              </label>
              {comp.on && (
                <>
                  {(['cx', 'cy', 'w', 'rot'] as const).map((k) => (
                    <label key={k} className="slider">
                      {{ cx: 'Horizontal', cy: 'Vertical', w: 'Size', rot: 'Rotate' }[k]}
                      <input
                        type="range"
                        min={k === 'rot' ? -30 : k === 'w' ? 0.04 : 0}
                        max={k === 'rot' ? 30 : k === 'w' ? 0.45 : 1}
                        step={k === 'rot' ? 1 : 0.005}
                        value={comp[k]}
                        onChange={(e) => setComp({ ...comp, [k]: Number(e.target.value) })}
                      />
                    </label>
                  ))}
                  <label className="row small">
                    <input type="checkbox" checked={comp.occlusion} onChange={(e) => setComp({ ...comp, occlusion: e.target.checked })} /> Keep objects in front
                    (pumpkin, scarf, fur stay over the shield)
                  </label>
                  <label className="slider">
                    Fabric blend
                    <input type="range" min={0} max={1} step={0.05} value={comp.fabric} onChange={(e) => setComp({ ...comp, fabric: Number(e.target.value) })} />
                  </label>
                  <p className="small muted">The preview shows placement only; occlusion and fabric blend are applied when the version is created.</p>
                  <button
                    className="btn"
                    disabled={busy}
                    onClick={() =>
                      run('Composited exact shield into a new version', () =>
                        post(`/api/assets/${a.asset_id}/composite`, { version: v.version, cx: comp.cx, cy: comp.cy, width_frac: comp.w, rotation: comp.rot, occlusion: comp.occlusion, fabric: comp.fabric }).then(() =>
                          setComp({ ...comp, on: false }),
                        ),
                      )
                    }
                  >
                    Create composite version (free)
                  </button>
                </>
              )}
            </div>
          )}

          {qa && (
            <details open={!qa.ok}>
              <summary>
                Automated QA: {qa.ok ? '✓ passed' : '✗ problems'} · human review required
              </summary>
              <ul className="small">
                {qa.errors?.map((x) => <li key={x} className="warn">✗ {x}</li>)}
                {qa.warnings?.map((x) => <li key={x} className="warn">! {x}</li>)}
                {qa.passed?.map((x) => <li key={x} className="ok">✓ {x}</li>)}
                {qa.needs_review?.map((x) => <li key={x} className="muted">☐ {x}</li>)}
              </ul>
            </details>
          )}

          <h4>References sent with requests</h4>
          <div className="refs">
            {a.dan_reference_paths.map((p) => (
              <a key={p} href={file(p)} target="_blank" rel="noreferrer" title={p}>
                <img src={thumb(p)} alt="" />
              </a>
            ))}
            {a.shield_path_effective ? (
              <a href={file(a.shield_path_effective)} target="_blank" rel="noreferrer" className="shield-ref" title="Official supplied shield">
                <img src={file(a.shield_path_effective)} alt="" />
              </a>
            ) : (
              <span className="small muted">{a.shield_slug ? '⚠ shield missing' : 'No shield for this asset'}</span>
            )}
          </div>
          {a.permitted_text.length > 0 && (
            <p className="small">
              Only these words may appear: {a.permitted_text.map((w) => <code key={w}>{w}</code>)}
            </p>
          )}

          <h4>Catalogue products using this image</h4>
          <div className="refs products">
            {a.product_ids.slice(0, 8).map((pid) => (
              <img key={pid} src={file(products[pid]?.photo_rel)} title={products[pid]?.name ?? pid} alt="" />
            ))}
          </div>

          <h4>Brief</h4>
          <dl className="brief small">
            <dt>Setting</dt><dd>{a.setting ?? '—'}</dd>
            <dt>Outfit</dt><dd>{a.outfit ?? '—'}</dd>
            <dt>Pose</dt><dd>{a.pose ?? '—'}</dd>
            <dt>Humor</dt><dd>{a.humor ?? '—'}</dd>
          </dl>
          <button className="link small" onClick={() => setShowPrompt((s) => !s)}>
            {showPrompt ? 'Hide' : 'Show / edit'} full prompt
          </button>
          {showPrompt && (
            <>
              <pre className="prompt">{v?.prompt ?? a.prompt_preview}</pre>
              <textarea
                rows={3}
                placeholder="Optional: replace the SCENE part of the prompt for this asset"
                value={override}
                onChange={(e) => setOverride(e.target.value)}
              />
              <button className="btn small" onClick={() => run('Scene override saved', () => post(`/api/assets/${a.asset_id}/meta`, { prompt_override: override }))}>
                Save scene override
              </button>
            </>
          )}

          {a.feedback.length > 0 && (
            <>
              <h4>History</h4>
              <ul className="small history">
                {a.feedback.map((f) => (
                  <li key={f.id}>
                    <b>{f.kind}</b> {f.version ? `v${f.version}` : ''} {f.text && `— ${f.text}`}
                  </li>
                ))}
              </ul>
            </>
          )}
        </aside>
      </div>
    </div>
  )
}
