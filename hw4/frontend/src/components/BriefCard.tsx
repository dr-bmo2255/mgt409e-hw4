import type { ReactNode } from 'react'
import type { DraftedBrief } from '../api'

// A drafted Custom Dan design (from the Design with Dan page or the chat), before it's created.
export default function BriefCard({
  brief,
  onCreate,
  busy = false,
  action = 'Create this Dan',
  note,
}: {
  brief: DraftedBrief
  onCreate?: () => void
  busy?: boolean
  action?: string
  note?: ReactNode
}) {
  return (
    <div className="brief-card">
      <div className="brief-head">
        <span className="brief-paw" aria-hidden>🎨</span>
        <div>
          <b>{brief.title}</b>
          <small>{brief.style === 'sticker' ? 'Sticker style · no background' : 'Photo style'}</small>
        </div>
      </div>
      <p>{brief.scene}</p>
      {brief.text.length > 0 && (
        <p className="brief-text">
          Printed words: {brief.text.map((t) => `“${t}”`).join(', ')}
        </p>
      )}
      {onCreate && (
        <button className="btn btn-brass btn-block" onClick={onCreate} disabled={busy}>
          {busy ? 'Sending to Dan…' : action}
        </button>
      )}
      {note && <p className="brief-note">{note}</p>}
    </div>
  )
}
