import { STATUS_COLORS, money } from '../api'

export type OverviewData = {
  counts: Record<string, number>
  previous_audit_counts: Record<string, number | null>
  status_counts: Record<string, number>
  scoped_total: number
  scoped_approved: number
  pending_review: number
  spent_usd: number
  spent_includes_estimates_usd: number
  cost_cap_usd: number
  remaining_budget_usd: number
  estimates: { per_image: number; pilot_3: number; first_pass_35: number; worst_case: number }
  pilot_complete: boolean
  provider: string
  key: { present: boolean; via: string | null }
  paused: boolean
  references_confirmed: boolean
  current_job: { asset_id?: string; provider?: string; started?: number }
  authorizations: { id: number; kind: string; asset_ids: string[]; max_images: number; used_images: number; budget_usd: number; spent_usd: number }[]
  events: { id: number; ts: number; kind: string; asset_id: string | null; message: string }[]
  discrepancies: { product_id: string; issue: string; audit?: string; studio?: string }[]
}

type Go = (t: 'overview' | 'mapping' | 'queue' | 'review' | 'batch' | 'settings' | 'export', a?: string) => void

export default function Overview({ data, go }: { data: OverviewData | null; go: Go }) {
  if (!data) return <p>Loading…</p>
  const c = data.counts
  const p = data.previous_audit_counts
  const pct = data.scoped_total ? (data.scoped_approved / data.scoped_total) * 100 : 0
  const rows: [string, string, number, number | null][] = [
    ['Catalogue products', 'catalogue_products', c.catalogue_products, p.catalogue_products],
    ['Dan category assets required', 'dan_assets_required', c.dan_assets_required, p.dan_assets_required],
    ['Existing (reuse)', 'existing_assets', c.existing_assets, p.existing_assets],
    ['Missing (to generate)', 'missing_assets', c.missing_assets, p.missing_assets],
  ]
  return (
    <div className="grid-2">
      <section className="card span-2">
        <div className="progress-head">
          <h2>Catalogue Dan assets</h2>
          <span>
            {data.scoped_approved} of {data.scoped_total} new assets approved · {data.pending_review} awaiting review
          </span>
        </div>
        <div className="progress">
          <div style={{ width: `${pct}%` }} />
        </div>
        <div className="status-chips">
          {Object.entries(data.status_counts).map(([s, n]) => (
            <span key={s} className="chip" style={{ borderColor: STATUS_COLORS[s], color: STATUS_COLORS[s] }}>
              {s.replace(/_/g, ' ')} <b>{n}</b>
            </span>
          ))}
        </div>
      </section>

      <section className="card">
        <h3>Reconciled inventory</h3>
        <table className="tbl">
          <thead>
            <tr><th>Metric</th><th>Verified now</th><th>Previous audit</th></tr>
          </thead>
          <tbody>
            {rows.map(([label, , now, prev]) => (
              <tr key={label}>
                <td>{label}</td>
                <td><b>{now}</b></td>
                <td className={prev === now ? 'ok' : 'warn'}>{prev ?? '—'} {prev === now ? '✓' : '≠'}</td>
              </tr>
            ))}
            <tr><td>Product photos present</td><td><b>{c.product_photos_present}/{c.catalogue_products}</b></td><td /></tr>
            <tr><td>Official shields supplied</td><td><b>{c.shields_available}</b></td><td /></tr>
            <tr><td>Dan files in archive</td><td><b>{c.dan_files_in_archive}</b></td><td className="muted">{c.dan_files_out_of_scope} out of scope · {c.collages_excluded} collage excluded</td></tr>
          </tbody>
        </table>
        {data.discrepancies.length > 0 && (
          <>
            <h4>Corrections to the previous audit</h4>
            <ul className="small">
              {data.discrepancies.map((d, i) => (
                <li key={i}>
                  <code>{d.product_id}</code>: {d.issue}: <s>{d.audit}</s> → <b>{d.studio}</b>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className="card">
        <h3>Budget</h3>
        <div className="kpis">
          <div><span>Spent</span><b>{money(data.spent_usd)}</b><small>{data.spent_includes_estimates_usd > 0 ? 'includes estimates' : 'actual usage'}</small></div>
          <div><span>Hard cap</span><b>{money(data.cost_cap_usd)}</b></div>
          <div><span>Remaining</span><b>{money(data.remaining_budget_usd)}</b></div>
        </div>
        <h4>Estimates (official token prices, estimated token counts)</h4>
        <table className="tbl">
          <tbody>
            <tr><td>Per image</td><td><b>{money(data.estimates.per_image)}</b></td></tr>
            <tr><td>3-image pilot</td><td><b>{money(data.estimates.pilot_3)}</b></td></tr>
            <tr><td>First pass, all {data.scoped_total}</td><td><b>{money(data.estimates.first_pass_35)}</b></td></tr>
            <tr><td>Worst case (max attempts each)</td><td><b>{money(data.estimates.worst_case)}</b></td></tr>
          </tbody>
        </table>
        <div className="checks">
          <span className={data.key.present ? 'ok' : 'warn'}>{data.key.present ? `✓ API key present (${data.key.via})` : '✗ No API key'}</span>
          <span className={data.references_confirmed ? 'ok' : 'warn'}>{data.references_confirmed ? '✓ Dan references confirmed' : '✗ Dan references not yet confirmed'}</span>
          <span className={data.pilot_complete ? 'ok' : 'muted'}>{data.pilot_complete ? '✓ Pilot reviewed' : '○ Pilot not done'}</span>
        </div>
        <button className="btn" onClick={() => go('batch')}>Go to batch control →</button>
      </section>

      <section className="card span-2">
        <h3>Recent activity</h3>
        <ul className="events">
          {data.events.length === 0 && <li className="muted">Nothing yet.</li>}
          {data.events.map((e) => (
            <li key={e.id}>
              <time>{new Date(e.ts * 1000).toLocaleTimeString()}</time>
              <span className={`ev ev-${e.kind}`}>{e.kind}</span>
              {e.asset_id && (
                <a href={`#review/${e.asset_id}`}>{e.asset_id}</a>
              )}{' '}
              {e.message}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
