import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  customApi,
  bagApi,
  customUnitPrice,
  formatPrice,
  type Allowance,
  type CustomProduct,
  type Design,
  type DesignStyle,
  type DraftedBrief,
  type QtyBreak,
  formatDate,
} from '../api'
import BriefCard from '../components/BriefCard'
import { DAN_ERRORS, isConnectionError, pick } from '../danVoice'
import Mockup, { DEFAULT_PLACEMENT } from '../components/Mockup'
import { useAuth } from '../context/AuthContext'
import { useBag } from '../context/BagContext'

type Tab = 'create' | 'mine' | 'classic'

const IDEAS = [
  'Dan as the Yale Bowl quarterback, mid-touchdown',
  'Dan rowing on the Housatonic at sunrise',
  'Dan studying in Sterling Library with tiny reading glasses',
  'Cartoon Dan giving a thumbs-up paw, sticker style',
]

// Problem 10 Part C: "Design with Dan", a focused, customer-facing Ask Dan Image Studio. Pick the gear,
// create (or choose) a Handsome Dan, place it, choose size and quantity, add to bag. Like CustomInk's design lab.
export default function CustomStudio() {
  const { user } = useAuth()
  const { setBag } = useBag()
  const [params, setParams] = useSearchParams()
  const [products, setProducts] = useState<CustomProduct[]>([])
  const [breaks, setBreaks] = useState<QtyBreak[]>([])
  const [designs, setDesigns] = useState<{ mine: Design[]; starters: Design[] }>({ mine: [], starters: [] })
  const [allowance, setAllowance] = useState<Allowance | null>(null)
  const [loadError, setLoadError] = useState(false)

  const productKey = params.get('product') ?? 'tee'
  const designRef = params.get('design') ?? 'starter:welcome_dan'
  const [tab, setTab] = useState<Tab>(designRef.startsWith('d:') ? 'mine' : 'create')
  const [placement, setPlacement] = useState(DEFAULT_PLACEMENT)
  const [size, setSize] = useState('M')
  const [qty, setQty] = useState(1)

  const [idea, setIdea] = useState('')
  const [style, setStyle] = useState<DesignStyle | null>(null)
  const [drafting, setDrafting] = useState(false)
  const [draft, setDraft] = useState<{ reply: string; brief: DraftedBrief | null } | null>(null)
  const [creating, setCreating] = useState(false)
  const [message, setMessage] = useState<{ kind: 'error' | 'ok'; text: string } | null>(null)
  const [adding, setAdding] = useState(false)
  const [danMsg, setDanMsg] = useState<string | null>(null) // refusals / errors while drafting or creating, in Dan's voice

  const product = products.find((p) => p.key === productKey) ?? products[0]
  const allDesigns = useMemo(() => [...designs.mine, ...designs.starters], [designs])
  const design = allDesigns.find((d) => d.ref === designRef) ?? null
  const pending = designs.mine.some((d) => d.status === 'queued' || d.status === 'generating')

  const select = useCallback(
    (next: { product?: string; design?: string }) => {
      const p = new URLSearchParams(params)
      if (next.product) p.set('product', next.product)
      if (next.design) p.set('design', next.design)
      setParams(p, { replace: true })
    },
    [params, setParams],
  )

  const reloadDesigns = useCallback(async () => {
    const [d, a] = await Promise.all([customApi.designs(), customApi.status()])
    setDesigns(d)
    setAllowance(a)
  }, [])

  useEffect(() => {
    customApi
      .products()
      .then((r) => {
        setProducts(r.products)
        setBreaks(r.qty_breaks)
      })
      .catch(() => setLoadError(true))
  }, [])

  useEffect(() => {
    reloadDesigns().catch(() => setLoadError(true))
  }, [reloadDesigns, user])

  // While Dan is "posing" (generating), poll until the image is ready or fails.
  useEffect(() => {
    if (!pending) return
    const t = setInterval(() => void reloadDesigns().catch(() => undefined), 2500)
    return () => clearInterval(t)
  }, [pending, reloadDesigns])

  // Keep the size valid when switching products (apparel S–XXL vs. one size).
  useEffect(() => {
    if (product && !product.sizes.includes(size)) setSize(product.sizes.includes('M') ? 'M' : product.sizes[0])
  }, [product, size])

  async function onDraft(e: FormEvent) {
    e.preventDefault()
    if (idea.trim().length < 3 || drafting) return
    setDrafting(true)
    setDanMsg(null)
    try {
      setDraft(await customApi.draft(idea.trim(), style))
    } catch (err) {
      setDanMsg(isConnectionError(err) ? pick(DAN_ERRORS) : (err as Error).message)
    } finally {
      setDrafting(false)
    }
  }

  async function onCreate(brief: DraftedBrief) {
    setCreating(true)
    setDanMsg(null)
    try {
      const d = await customApi.create(brief.brief_id)
      await reloadDesigns()
      select({ design: d.ref })
      setTab('mine')
      setDraft(null)
      setIdea('')
    } catch (err) {
      // Refusals arrive already written in Dan's voice; connection failures get one of Dan's error lines.
      setDanMsg(isConnectionError(err) ? pick(DAN_ERRORS) : (err as Error).message)
    } finally {
      setCreating(false)
    }
  }

  async function onAdd() {
    if (!product || !design || design.status !== 'ready') return
    setAdding(true)
    setMessage(null)
    try {
      setBag(await bagApi.add({ product_key: product.key, design_ref: design.ref, size, quantity: qty, placement }))
      setMessage({ kind: 'ok', text: `Added ${qty} × ${product.name} (${size}) to your bag.` })
    } catch (err) {
      setMessage({ kind: 'error', text: (err as Error).message })
    } finally {
      setAdding(false)
    }
  }

  if (loadError) {
    return (
      <div className="container section">
        <p className="notice">We couldn't reach the server. Make sure the backend is running on port 8000.</p>
      </div>
    )
  }
  if (!product) return <div className="container section"><p className="muted">Loading Dan's design studio…</p></div>

  const unit = customUnitPrice(product, size, qty, breaks)
  const left = allowance?.remaining_today ?? 0
  const designPending = design && (design.status === 'queued' || design.status === 'generating')

  return (
    <>
      <section className="custom-hero">
        <div className="container custom-hero-inner">
          <div>
            <p className="kicker light">Custom Dan Gear</p>
            <h1>
              Design with <em>Dan</em>
            </h1>
            <p>
              Describe any Handsome Dan you can imagine. Dan will pose for it, and we'll print him on a tee, crewneck, hoodie,
              mousepad, cup, notebook or folder. Made to order in New Haven.
            </p>
          </div>
          <ol className="custom-steps" aria-label="How it works">
            <li><b>1</b> Pick your gear</li>
            <li><b>2</b> Create your Dan</li>
            <li><b>3</b> Place it</li>
            <li><b>4</b> Add to bag</li>
          </ol>
        </div>
      </section>

      <div className="container studio">
        <div className="studio-preview">
          <div className="studio-stage">
            <Mockup product={product} design={design?.status === 'ready' ? design : null} placement={placement} showArea={!design || design.status !== 'ready'} />
            {designPending && (
              <div className="studio-posing" role="status">
                <span className="paws" aria-hidden><i>🐾</i><i>🐾</i><i>🐾</i></span>
                <b>Dan is posing for “{design.title}”…</b>
                <small>Usually 30–90 seconds. You can keep browsing.</small>
              </div>
            )}
          </div>
          <p className="studio-caption">
            <b>{product.name}</b> · {product.color}
            {design && <> · <span>{design.title}</span></>}
          </p>
        </div>

        <div className="studio-panel">
          <section className="studio-step">
            <h2><span>1</span> Choose your gear</h2>
            <div className="gear-grid">
              {products.map((p) => (
                <button key={p.key} className={`gear ${p.key === product.key ? 'active' : ''}`} onClick={() => select({ product: p.key })} aria-pressed={p.key === product.key}>
                  <img src={p.mockup_url} alt="" loading="lazy" />
                  <span>{p.name.replace('Custom Dan ', '')}</span>
                  <small>{formatPrice(p.price)}</small>
                </button>
              ))}
            </div>
            <p className="muted small">{product.blurb}</p>
          </section>

          <section className="studio-step">
            <h2><span>2</span> Pick your Dan</h2>
            <div className="tabs" role="tablist">
              {([['create', 'Create new'], ['mine', `My designs${designs.mine.length ? ` (${designs.mine.length})` : ''}`], ['classic', 'Classic Dan']] as [Tab, string][]).map(([k, label]) => (
                <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? 'active' : ''} onClick={() => setTab(k)}>
                  {label}
                </button>
              ))}
            </div>

            {tab === 'create' &&
              (!user ? (
                <div className="studio-guest">
                  <p>
                    <b>Log in to create your own Dan.</b> Every customer gets {allowance?.daily_limit ?? 3} free creations a day.
                    You can still try the Classic Dan designs on any gear.
                  </p>
                  <Link to="/login" className="btn btn-primary">Log in</Link>{' '}
                  <Link to="/create-account" className="btn btn-ghost-dark">Create account</Link>
                </div>
              ) : (
                <>
                  <form className="idea-form" onSubmit={onDraft}>
                    <label htmlFor="idea">Describe your Dan</label>
                    <textarea
                      id="idea"
                      value={idea}
                      onChange={(e) => setIdea(e.target.value)}
                      placeholder="e.g. Dan as a hockey goalie at Ingalls Rink, making a huge glove save"
                      maxLength={500}
                      rows={3}
                    />
                    <div className="idea-row">
                      <div className="seg" role="radiogroup" aria-label="Style">
                        {([[null, 'Dan decides'], ['photo', 'Photo'], ['sticker', 'Sticker']] as [DesignStyle | null, string][]).map(([k, label]) => (
                          <button type="button" key={label} role="radio" aria-checked={style === k} className={style === k ? 'active' : ''} onClick={() => setStyle(k)}>
                            {label}
                          </button>
                        ))}
                      </div>
                      <button className="btn btn-primary" disabled={drafting || idea.trim().length < 3}>
                        {drafting ? 'Sketching…' : 'Draft it'}
                      </button>
                    </div>
                    {!draft && (
                      <div className="idea-chips">
                        {IDEAS.map((i) => (
                          <button type="button" key={i} className="chip" onClick={() => setIdea(i)}>{i}</button>
                        ))}
                      </div>
                    )}
                  </form>
                  {draft && (
                    <div className="draft">
                      <p className={`draft-reply ${draft.brief ? '' : 'dan-says'}`}>🐶 {draft.reply}</p>
                      {draft.brief && (
                        <BriefCard
                          brief={draft.brief}
                          busy={creating}
                          onCreate={left > 0 && !pending && allowance?.site_open ? () => void onCreate(draft.brief!) : undefined}
                          note={
                            pending ? 'Dan is still working on your last design. One at a time!'
                            : !allowance?.site_open ? "Dan's studio is closed for today. Try a Classic Dan, or come back tomorrow."
                            : left > 0 ? `Uses 1 of your ${left} creation${left === 1 ? '' : 's'} left today. Saved in your account for 90 days. Not quite right? Edit the idea and draft again.`
                            : "You've used today's creations. Come back tomorrow, or pick from My designs or Classic Dan."
                          }
                        />
                      )}
                    </div>
                  )}
                  {danMsg && <p className="dan-says" role="alert">🐶 {danMsg}</p>}
                  <p className="allowance">
                    {Array.from({ length: allowance?.daily_limit ?? 3 }, (_, i) => (
                      <i key={i} className={i < (allowance?.used_today ?? 0) ? 'used' : ''} aria-hidden>🐾</i>
                    ))}
                    {left} of {allowance?.daily_limit ?? 3} creations left today
                    {allowance?.mock && <em> · test mode (no real images)</em>}
                  </p>
                </>
              ))}

            {tab === 'mine' && (
              <>
              {user && (
                <p className="keep-note">
                  🐾 Your Dans are saved in your account for <b>90 days</b> from the day you create them, so you can come back and
                  put them on more gear. After that they're deleted for good, along with any bag items using them.
                </p>
              )}
              <div className="design-grid">
                {!user && <p className="muted">Log in to see your designs.</p>}
                {user && designs.mine.length === 0 && <p className="muted">No designs yet. Create your first Dan!</p>}
                {designs.mine.map((d) => (
                  <DesignTile key={d.ref} d={d} active={d.ref === designRef} onPick={() => select({ design: d.ref })} />
                ))}
              </div>
              {designs.mine.filter((d) => d.status === 'failed').map((d) => (
                <p key={d.ref} className="dan-says" role="status"><b>Dan:</b> {d.error}</p>
              ))}
              </>
            )}

            {tab === 'classic' && (
              <div className="design-grid">
                {designs.starters.map((d) => (
                  <DesignTile key={d.ref} d={d} active={d.ref === designRef} onPick={() => select({ design: d.ref })} />
                ))}
              </div>
            )}
          </section>

          {!product.bleed && (
            <section className="studio-step">
              <h2><span>3</span> Place it</h2>
              <label className="range">
                <span>Size</span>
                <input type="range" min={0.4} max={1} step={0.05} value={placement.scale} onChange={(e) => setPlacement({ ...placement, scale: Number(e.target.value) })} />
                <output>{Math.round(placement.scale * 100)}%</output>
              </label>
              <label className="range">
                <span>Position</span>
                <input type="range" min={-1} max={1} step={0.1} value={placement.y} onChange={(e) => setPlacement({ ...placement, y: Number(e.target.value) })} />
                <output>{placement.y < -0.15 ? 'Higher' : placement.y > 0.15 ? 'Lower' : 'Centered'}</output>
              </label>
            </section>
          )}

          <section className="studio-step">
            <h2><span>{product.bleed ? 3 : 4}</span> Size & quantity</h2>
            {product.sizes.length > 1 ? (
              <div className="sizes" role="radiogroup" aria-label="Size">
                {product.sizes.map((s) => (
                  <button key={s} role="radio" aria-checked={size === s} className={`size ${size === s ? 'active' : ''}`} onClick={() => setSize(s)}>
                    {s}
                  </button>
                ))}
              </div>
            ) : (
              <p className="muted small">Size: {product.sizes[0]}</p>
            )}
            <div className="qty-row">
              <div className="qty" aria-label="Quantity">
                <button onClick={() => setQty((q) => Math.max(1, q - 1))} aria-label="Fewer">−</button>
                <input type="number" min={1} max={144} value={qty} onChange={(e) => setQty(Math.min(144, Math.max(1, Number(e.target.value) || 1)))} aria-label="Quantity" />
                <button onClick={() => setQty((q) => Math.min(144, q + 1))} aria-label="More">+</button>
              </div>
              <div className="price-box">
                <span className="price">{formatPrice(unit)}</span> <small>each</small>
                <b>{formatPrice(Math.round(unit * qty * 100) / 100)}</b>
              </div>
            </div>
            <p className="muted small">
              Order more, save more: {breaks.map((b) => `${b.percent_off}% off ${b.min_qty}+`).join(' · ')}
              {product.xxl_upcharge > 0 && ` · XXL +${formatPrice(product.xxl_upcharge)}`}
            </p>
            {user ? (
              <button className="btn btn-brass btn-block" onClick={() => void onAdd()} disabled={adding || !design || design.status !== 'ready'}>
                {adding ? 'Adding…' : design?.status === 'ready' ? 'Add to bag' : 'Choose a finished design first'}
              </button>
            ) : (
              <Link to="/login" className="btn btn-brass btn-block">Log in to add to bag</Link>
            )}
            {message && (
              <p className={message.kind === 'ok' ? 'studio-ok' : 'notice'} role="status">
                {message.text} {message.kind === 'ok' && <Link to="/bag">View bag →</Link>}
              </p>
            )}
            <p className="muted small">Custom gear is made to order and can't be returned. Officially licensed Campus Customs product.</p>
          </section>
        </div>
      </div>
    </>
  )
}

function DesignTile({ d, active, onPick }: { d: Design; active: boolean; onPick: () => void }) {
  const working = d.status === 'queued' || d.status === 'generating'
  return (
    <button className={`design-tile ${active ? 'active' : ''} ${d.status}`} onClick={onPick} disabled={d.status === 'failed'} title={d.expires_at ? `${d.title}: saved until ${formatDate(d.expires_at)}` : d.error ?? d.title}>
      {d.thumb_url ? <img src={d.thumb_url} alt="" loading="lazy" /> : <span className="design-ph">{working ? '🐾' : '✕'}</span>}
      <span>{d.title}</span>
      <small>
        {working ? 'Dan is posing…'
          : d.status === 'failed' ? "Dan passed on this one"
          : d.kind === 'starter' ? 'Classic · free'
          : `${d.style === 'sticker' ? 'Sticker' : 'Photo'} · ${d.days_left ?? 90}d left`}
      </small>
    </button>
  )
}
