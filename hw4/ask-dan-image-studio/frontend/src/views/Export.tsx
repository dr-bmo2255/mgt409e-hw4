import { useState } from 'react'
import { file, post } from '../api'

type Result = { zip: string; folder: string; approved_pngs: string[]; remaining: string[] }

export default function Export() {
  const [r, setR] = useState<Result | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  return (
    <section className="card">
      <h2>Export</h2>
      <p>
        Packages <b>only approved</b> individual PNGs plus: product → Dan mapping (JSON + CSV), the audit workbook refreshed with a <i>Studio Status</i> sheet,
        an updated TXT checklist, and a review/cost report. Assets still missing or awaiting review are listed separately. Exports are scanned for credentials.
      </p>
      <button
        className="btn primary"
        disabled={busy}
        onClick={async () => {
          setBusy(true)
          setErr(null)
          try {
            setR(await post<Result>('/api/export'))
          } catch (e) {
            setErr((e as Error).message)
          } finally {
            setBusy(false)
          }
        }}
      >
        {busy ? 'Exporting…' : 'Create export ZIP'}
      </button>
      {err && <div className="banner error small">{err}</div>}
      {r && (
        <div className="export-result">
          <p>
            ✓ <a href={file(r.zip)}>Download {r.zip.split('/').pop()}</a> · folder <code>{r.folder}</code>
          </p>
          <p>
            <b>{r.approved_pngs.length}</b> approved PNG(s): {r.approved_pngs.join(', ') || 'none yet'}
          </p>
          <p className="small muted">
            Still to do ({r.remaining.length}): {r.remaining.join(', ')}
          </p>
        </div>
      )}
    </section>
  )
}
