import { useEffect, useState } from 'react'
import { STATUS_COLORS, file, get, money, type Asset } from '../api'

type Go = (t: 'review', a?: string) => void

export default function Queue({ go }: { go: Go }) {
  const [assets, setAssets] = useState<Asset[]>([])
  const [scope, setScope] = useState<'missing' | 'all' | 'existing' | 'custom'>('missing')
  const [status, setStatus] = useState('')
  const [sort, setSort] = useState<'group' | 'products' | 'status'>('group')

  useEffect(() => {
    const load = () => get<Asset[]>('/api/assets').then(setAssets)
    load()
    const t = setInterval(load, 4000)
    return () => clearInterval(t)
  }, [])

  const shown = assets
    .filter((a) => scope === 'all' ? true : scope === 'custom' ? a.group === 'Custom' : a.group === 'Custom' ? false : scope === 'missing' ? a.manifest_status === 'MISSING' : a.manifest_status !== 'MISSING')
    .filter((a) => !status || a.status === status)
    .sort((a, b) =>
      sort === 'products' ? b.product_count - a.product_count : sort === 'status' ? a.status.localeCompare(b.status) : a.group.localeCompare(b.group) || a.asset_id.localeCompare(b.asset_id),
    )

  return (
    <section className="card">
      <div className="toolbar">
        <h2>Asset queue</h2>
        <select value={scope} onChange={(e) => setScope(e.target.value as typeof scope)}>
          <option value="missing">Scoped: 35 to create</option>
          <option value="existing">Existing / reuse</option>
          <option value="custom">One-off (chat)</option>
          <option value="all">All</option>
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Any status</option>
          {Object.keys(STATUS_COLORS).map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value as typeof sort)}>
          <option value="group">Sort: group</option>
          <option value="products">Sort: most products</option>
          <option value="status">Sort: status</option>
        </select>
        <span className="muted">{shown.length} assets</span>
      </div>
      <div className="asset-grid">
        {shown.map((a) => (
          <button key={a.asset_id} className="asset-card" onClick={() => go('review', a.asset_id)}>
            <div className="asset-thumb">
              {a.latest_thumb ? <img src={file(a.latest_thumb)} alt="" loading="lazy" /> : <span>{a.existing_files.length ? '📁 existing' : '—'}</span>}
              {a.pilot && <span className="badge-pilot">PILOT</span>}
            </div>
            <div className="asset-body">
              <span className="chip" style={{ borderColor: STATUS_COLORS[a.status], color: STATUS_COLORS[a.status] }}>
                {a.status.replace(/_/g, ' ')}
              </span>
              <b>{a.display_name}</b>
              <code className="small">{a.canonical_filename}</code>
              <span className="small muted">
                {a.group} · {a.product_count} product{a.product_count === 1 ? '' : 's'} · {a.version_count ?? 0} version(s)
                {a.cost_usd ? ` · ${money(a.cost_usd)}` : ''}
              </span>
              <span className="small">{a.shield_slug ? `🛡 ${a.shield_slug.replace(/_/g, ' ')}${a.shield_path ? '' : ' (missing!)'}` : 'no shield'}</span>
              {a.existing_files.length > 0 && <span className="small muted">Existing: {a.existing_files.join('; ')}</span>}
              {a.notes && <span className="small note">📝 {a.notes}</span>}
            </div>
          </button>
        ))}
      </div>
    </section>
  )
}
