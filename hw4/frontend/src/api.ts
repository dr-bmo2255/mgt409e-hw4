// Thin client for the FastAPI backend (backend/main.py). Vite proxies /api and /media.

export type SizeStock = { size: string; quantity: number }

// A Handsome Dan category image (Problem 10): every product maps to one; chat searches return one.
export type DanImage = {
  asset_id: string
  image_url: string
  thumb_url: string
  caption: string
  category: string
  group: string
  aspect: number
}

export type Product = {
  product_id: string
  name: string
  garment_type: string
  category: string
  description: string
  colors: string[]
  search_tags: string[]
  image_file_path: string
  image_url: string
  price: number
  total_stock: number
  inventory?: SizeStock[]
  dan?: DanImage | null
  base_color?: string | null // the color shown in image_url (Part D)
  color_images?: Record<string, string> // a product photo for each colorway that has one
}

export type Category = { name: string; count: number }

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export function fetchProducts(params: { q?: string; category?: string } = {}) {
  const qs = new URLSearchParams()
  if (params.q) qs.set('q', params.q)
  if (params.category) qs.set('category', params.category)
  const suffix = qs.toString() ? `?${qs}` : ''
  return getJson<Product[]>(`/api/products${suffix}`)
}

export const fetchProduct = (id: string) => getJson<Product>(`/api/products/${encodeURIComponent(id)}`)

export const fetchCategories = () => getJson<Category[]>('/api/categories')

export const formatPrice = (price: number) =>
  price.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

// Product names in the catalogue are generated from slugs ("1 4 Zip", "T Shirt", "Ua Mens Tech L S").
export function displayName(name: string) {
  return name
    .replace(/\b1 4 Zip\b/gi, '1/4 Zip')
    .replace(/\bT Shirt\b/gi, 'T-Shirt')
    .replace(/\bL S\b/g, 'L/S')
    .replace(/\bUa Mens\b/g, "UA Men's")
    .replace(/\b2 0\b/g, '2.0')
    .replace(/\bVs\b/g, 'vs.')
}

// --- Chat ------------------------------------------------------------------------
// POST /api/chat → PydanticAI agent. Signed-in shoppers' history lives in the database;
// guests send their (text-only) history with each message.

export type Voice = 'brand' | 'dan'

export type ChatProduct = {
  product_id: string
  name: string
  category: string
  price: number
  image_url: string
  colors: string[]
  description: string
  total_stock: number
  inventory: SizeStock[]
  dan?: DanImage | null
}

export type ChatApiResponse = {
  reply: string
  products: ChatProduct[]
  results_title: string | null
  see_all_category: string | null
  dan?: DanImage | null
  design?: DraftedBrief | null
  go_to?: SitePage | null
  voice: Voice
}

// Pages the chat can take a shopper to (mirrors backend models.SitePage).
export type SitePage = 'home' | 'products' | 'design_with_dan' | 'bag' | 'about' | 'account' | 'login' | 'create_account'
export const SITE_PAGES: Record<SitePage, { path: string; label: string }> = {
  home: { path: '/', label: 'Home' },
  products: { path: '/products', label: 'All products' },
  design_with_dan: { path: '/custom', label: 'Design with Dan' },
  bag: { path: '/bag', label: 'Your bag' },
  about: { path: '/about', label: 'About Us' },
  account: { path: '/account', label: 'Your account' },
  login: { path: '/login', label: 'Log in' },
  create_account: { path: '/create-account', label: 'Create an account' },
}

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
  products?: ChatProduct[]
  voice?: Voice
  dan?: DanImage | null
  design?: DraftedBrief | null
  rival?: string | null // Part E: an Ivy rival named in the shopper's message → that rival's Dan image
  ask?: 'rival' // Part E: Dan asked "which school?" (shows the rival buttons)
  go_to?: SitePage | null // the page the chat took the shopper to
}

// Where the shopper is, so the agent can resolve "this" on a product page.
export type PageContext = { path: string; product_id?: string; category?: string; search?: string }

export async function sendChat(input: {
  message: string
  voice: Voice
  previous_voice: Voice | null
  history: { role: string; content: string }[]
  page: PageContext
  visitor?: string // Part E: who they said they are ("Yale alumnus from the 1960s"), self-reported
}): Promise<ChatApiResponse> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify(input),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'The assistant is unavailable right now.')
  return data
}

export const fetchChatHistory = () => getJson<ChatMessage[]>('/api/chat/history')

export const clearChatHistory = () =>
  fetch('/api/chat/history', { method: 'DELETE', credentials: 'same-origin' }).then(() => undefined)

// --- Accounts ----------------------------------------------------------------
// The session lives in an HttpOnly cookie set by the backend; JS never sees the token.

export type User = { id: number; first_name: string; last_name: string; name: string; email: string }

export type SignupInput = {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : 'Something went wrong. Please try again.'
    throw new Error(detail)
  }
  return data as T
}

export const authApi = {
  me: () => getJson<{ user: User | null }>('/api/auth/me').then((d) => d.user),
  login: (email: string, password: string) =>
    postJson<{ user: User }>('/api/auth/login', { email, password }).then((d) => d.user),
  signup: (input: SignupInput) => postJson<{ user: User }>('/api/auth/signup', input).then((d) => d.user),
  logout: () => postJson<{ ok: boolean }>('/api/auth/logout'),
}

// Most common Dan category among a set of products (mirrors backend dan_for_products), for saved chats.
export function danForProducts(products: { dan?: DanImage | null }[] | undefined): DanImage | null {
  const list = (products ?? []).map((p) => p.dan).filter((d): d is DanImage => !!d)
  if (!list.length) return null
  const counts = new Map<string, number>()
  list.forEach((d) => counts.set(d.asset_id, (counts.get(d.asset_id) ?? 0) + 1))
  const top = Math.max(...counts.values())
  return list.find((d) => counts.get(d.asset_id) === top) ?? null
}

export const DAN_AVATAR = '/media/dan/avatar_dan.webp'

// --- Custom Dan Gear (Problem 10 Part C) ---------------------------------------------
// Customers create a Handsome Dan image (or pick a classic one) and put it on blank gear.

export type PrintArea = { x: number; y: number; w: number; h: number } // fractions of the mockup photo

export type CustomProduct = {
  key: string
  name: string
  kind: string
  price: number
  sizes: string[]
  blurb: string
  color: string
  print: PrintArea
  bleed: boolean
  dark: boolean
  mockup_url: string
  xxl_upcharge: number
}

export type QtyBreak = { min_qty: number; percent_off: number }

export type DesignStyle = 'photo' | 'sticker'

export type DraftedBrief = { brief_id: number; title: string; scene: string; style: DesignStyle; text: string[] }

export type Design = {
  ref: string // "d:<id>" (theirs) or "starter:<asset>" (classic Dan)
  id?: number
  title: string
  style: DesignStyle
  status: 'queued' | 'generating' | 'ready' | 'failed'
  kind: 'mine' | 'starter'
  error?: string | null
  expires_at?: string // ISO date; customer designs are saved for 90 days (Part C2)
  days_left?: number
  image_url: string | null
  thumb_url: string | null
}

export type Placement = { scale: number; y: number }

export type Allowance = {
  signed_in: boolean
  daily_limit: number
  used_today: number
  remaining_today: number
  in_progress: boolean
  site_open: boolean
  mock: boolean
}

export type BagItem = {
  id: number
  product: CustomProduct
  design: Design
  size: string
  quantity: number
  placement: Placement
  unit_price: number
  line_total: number
}

export type Bag = { items: BagItem[]; count: number; subtotal: number }

async function sendJson<T>(method: string, url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Something went wrong. Please try again.')
  return data as T
}

export const customApi = {
  products: () => getJson<{ products: CustomProduct[]; qty_breaks: QtyBreak[] }>('/api/custom/products'),
  status: () => getJson<Allowance>('/api/custom/status'),
  designs: () => getJson<{ mine: Design[]; starters: Design[]; retention_days: number }>('/api/custom/designs'),
  design: (id: number) => getJson<Design>(`/api/custom/designs/${id}`),
  draft: (idea: string, style: DesignStyle | null) =>
    sendJson<{ reply: string; brief: DraftedBrief | null }>('POST', '/api/custom/briefs', { idea, style }),
  create: (brief_id: number) => sendJson<Design>('POST', '/api/custom/designs', { brief_id }),
}

export const bagApi = {
  get: () => getJson<Bag>('/api/bag'),
  add: (item: { product_key: string; design_ref: string; size: string; quantity: number; placement: Placement }) =>
    sendJson<Bag>('POST', '/api/bag', item),
  setQty: (id: number, quantity: number) => sendJson<Bag>('PATCH', `/api/bag/${id}`, { quantity }),
  remove: (id: number) => sendJson<Bag>('DELETE', `/api/bag/${id}`),
}

// Mirrors custom.unit_price on the server (which is the authority when adding to the bag).
export function customUnitPrice(p: CustomProduct, size: string, qty: number, breaks: QtyBreak[]): number {
  const base = p.price + (size === 'XXL' ? p.xxl_upcharge : 0)
  const off = [...breaks].sort((a, b) => b.min_qty - a.min_qty).find((b) => qty >= b.min_qty)?.percent_off ?? 0
  return Math.round(base * (1 - off / 100) * 100) / 100
}

// "Jan 16, 2027" from an ISO date (customer design expiry).
export const formatDate = (iso: string) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
