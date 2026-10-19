// Thin typed client for the studio backend.

export type Version = {
  id: number
  version: number
  parent_version: number | null
  kind: string
  provider: string
  model: string | null
  prompt: string | null
  feedback: string | null
  path: string
  thumb: string | null
  width: number | null
  height: number | null
  cost_usd: number
  cost_is_estimate: number
  decision: string
  qa_json: { ok?: boolean; errors?: string[]; warnings?: string[]; passed?: string[]; needs_review?: string[] } | null
  created_at: number
  settings: Record<string, unknown> | null
}

export type Asset = {
  asset_id: string
  group: string
  category: string
  display_name: string
  canonical_filename: string
  product_ids: string[]
  product_count: number
  existing_files: string[]
  status: string
  manifest_status: string
  pilot: boolean
  shield_slug: string | null
  shield_path: string | null
  setting: string | null
  outfit: string | null
  pose: string | null
  humor: string | null
  permitted_text: string[]
  qa_warnings: string[]
  attempts: number
  notes: string | null
  prompt_override: string | null
  shield_override: string | null
  approved_version: number | null
  version_count?: number
  latest_thumb?: string
  cost_usd?: number
}

export type AssetDetail = Asset & {
  versions: Version[]
  feedback: { id: number; version: number | null; kind: string; text: string; created_at: number }[]
  jobs: { id: number; status: string; error: string | null; kind: string; provider: string }[]
  dan_reference_paths: string[]
  shield_path_effective: string | null
  prompt_preview: string
  estimate_usd: number
}

export const thumb = (rel?: string | null) => (rel ? `/thumb/${rel.split('/').map(encodeURIComponent).join('/')}` : '')
export const file = (rel?: string | null) => (rel ? `/files/${rel.split('/').map(encodeURIComponent).join('/')}` : '')

async function req<T>(method: string, url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail ?? res.statusText))
  return data as T
}

export const get = <T,>(url: string) => req<T>('GET', url)
export const post = <T,>(url: string, body: unknown = {}) => req<T>('POST', url, body)

export const STATUS_COLORS: Record<string, string> = {
  EXISTING_REVIEWED: '#5b7c99',
  MISSING: '#9aa5b1',
  QUEUED: '#b7791f',
  GENERATING: '#d69e2e',
  PENDING_REVIEW: '#3182ce',
  REVISION_REQUESTED: '#805ad5',
  APPROVED: '#2f855a',
  REJECTED: '#c53030',
  FAILED: '#9b2c2c',
  OUT_OF_SCOPE: '#cbd5e0',
}

export const money = (n: number | undefined | null) => `$${(n ?? 0).toFixed(2)}`
