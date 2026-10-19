import { useEffect, useMemo, useState } from 'react'
import { STATUS_COLORS, file, get, thumb } from '../api'

type Product = {
  product_id: string
  name: string
  garment_type: string
  price: number
  photo_file: string
  photo_present: boolean
  photo_rel: string
  dan_group: string
  dan_category: string
  dan_asset_id: string
  mapping_reason: string
  dan_status: string
}
type AssetLite = { asset_id: string; existing_files: string[]; latest_thumb?: string; status: string }
type Go = (t: 'review', a?: string) => void

export default function Mapping({ go }: { go: Go }) {
  const [products, setProducts] = useState<Product[]>([])
  const [assets, setAssets] = useState<Record<string, AssetLite>>({})
  const [danFiles, setDanFiles] = useState<Record<string, string>>({})
  const [q, setQ] = useState('')
  const [group, setGroup] = useState('')

  useEffect(() => {
    get<Product[]>('/api/products').then(setProducts)
    get<AssetLite[]>('/api/assets').then((a) => setAssets(Object.fromEntries(a.map((x) => [x.asset_id, x]))))
    get<{ dan_files: { filename: string; rel_path: string }[] }>('/api/inventory').then((inv) =>
      setDanFiles(Object.fromEntries(inv.dan_files.map((d) => [d.filename, d.rel_path]))),
    )
  }, [])

  const groups = useMemo(() => [...new Set(products.map((p) => p.dan_group))].sort(), [products])
  const shown = products.filter(
    (p) =>
      (!group || p.dan_group === group) &&
      (!q || `${p.product_id} ${p.name} ${p.dan_category} ${p.dan_asset_id}`.toLowerCase().includes(q.toLowerCase())),
  )

  return (
    <section className="card">
      <div className="toolbar">
        <h2>Catalogue → Dan mapping</h2>
        <input placeholder="Search product, category, asset…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={group} onChange={(e) => setGroup(e.target.value)}>
          <option value="">All groups</option>
          {groups.map((g) => (
            <option key={g}>{g}</option>
          ))}
        </select>
        <span className="muted">{shown.length} of {products.length} products</span>
      </div>
      <p className="muted small">
        Left: the actual merchandise photo (never altered). Right: the contextual Dan category image shared by every product in that
        category. Mapping is computed independently from the catalogue and checked against the previous audit.
      </p>
      <table className="tbl mapping">
        <thead>
          <tr>
            <th>Product photo</th>
            <th>Product</th>
            <th>Dan category</th>
            <th>Why</th>
            <th>Dan image</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {shown.map((p) => {
            const a = assets[p.dan_asset_id]
            const existing = a?.existing_files?.[0]
            const danThumb = a?.latest_thumb ? file(a.latest_thumb) : existing && danFiles[existing] ? thumb(danFiles[existing]) : ''
            return (
              <tr key={p.product_id}>
                <td>{p.photo_present ? <img className="mini" src={file(p.photo_rel)} alt="" loading="lazy" /> : '✗ missing'}</td>
                <td>
                  <b>{p.name}</b>
                  <br />
                  <code className="small">{p.product_id}</code>
                </td>
                <td>
                  {p.dan_group}: <b>{p.dan_category}</b>
                  <br />
                  <a href={`#review/${p.dan_asset_id}`} onClick={() => go('review', p.dan_asset_id)} className="small">
                    {p.dan_asset_id}
                  </a>
                </td>
                <td className="small muted">{p.mapping_reason}</td>
                <td>{danThumb ? <img className="mini" src={danThumb} alt="" loading="lazy" /> : <span className="muted small">none yet</span>}</td>
                <td>
                  <span className="chip" style={{ borderColor: STATUS_COLORS[p.dan_status], color: STATUS_COLORS[p.dan_status] }}>
                    {p.dan_status.replace(/_/g, ' ')}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </section>
  )
}
