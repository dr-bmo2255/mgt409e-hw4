import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { customApi, fetchCategories, fetchProducts, formatPrice, type Category, type CustomProduct, type DanImage, type Design, type Product } from '../api'
import Mockup from '../components/Mockup'
import ProductCard from '../components/ProductCard'
import { useReveal } from '../hooks/useReveal'

// Hero "Dan stage": rotating Handsome Dan photos (crossfade + slow zoom), each linking to its products.
const STAGE = ['dan_sport_football', 'dan_hoodie', 'dan_school_management', 'dan_family_grandma', 'dan_sport_lacrosse']

// Shop categories illustrated by the Dan image that best represents them.
const CATEGORY_DAN: Record<string, string> = {
  Hoodies: 'dan_hoodie',
  Crewnecks: 'dan_crewneck',
  'T-Shirts': 'dan_tshirt',
  'Quarter-Zips': 'dan_school_law',
  'Jackets & Fleece': 'dan_jacket',
  'Long Sleeve': 'dan_performance',
}

const FEATURED_IDS = ['basic-hoodie-big-yale', 'super-heavyweight-crewneck-arched-yale-crest', 'yale-bowl-t-shirt', 'brooks-brothers-bomber-jacket-yale']

const RAILS: { group: string; title: string; blurb: string }[] = [
  { group: 'Colleges', title: 'Your residential college', blurb: 'Crests, crewnecks and quarter-zips for the college you call home.' },
  { group: 'Sports', title: 'Game day, every day', blurb: 'From the Yale Bowl to the squash courts. Pick your sport.' },
  { group: 'Family', title: 'Gifts for the whole family', blurb: 'Proud Mom, Dad, Grandpa, Aunt… Dan has already tried them all on.' },
  { group: 'Schools', title: 'For the grad schools', blurb: 'Law, Management, Medicine, Music and more.' },
]

const danSrc = (id: string, size: '' | '_sm' = '') => `/media/dan/${id}${size}.webp`

// Custom Dan Gear promo: three blanks wearing classic Dan designs (Problem 10 Part C).
const PROMO: [string, string, string][] = [
  ['tee', 'dan_sport_football', 'Game day vs. Harvard'],
  ['hoodie', 'welcome_dan', 'Welcome Dan'],
  ['cup', 'dan_sport_ice_hockey', 'Ice hockey Dan'],
]
const promoDesign = (asset: string, title: string): Design => ({
  ref: `starter:${asset}`, title, style: 'photo', status: 'ready', kind: 'starter', image_url: danSrc(asset), thumb_url: danSrc(asset),
})

export default function Home() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [error, setError] = useState(false)
  const [slide, setSlide] = useState(0)
  const [custom, setCustom] = useState<CustomProduct[]>([])
  useReveal([products.length, categories.length])

  useEffect(() => {
    fetchProducts().then(setProducts).catch(() => setError(true))
    fetchCategories().then(setCategories).catch(() => setError(true))
    customApi.products().then((r) => setCustom(r.products)).catch(() => undefined)
  }, [])

  useEffect(() => {
    const t = setInterval(() => setSlide((s) => (s + 1) % STAGE.length), 5000)
    return () => clearInterval(t)
  }, [])

  // One entry per Dan category image, with how many products it covers.
  const dans = useMemo(() => {
    const map = new Map<string, { dan: DanImage; count: number }>()
    for (const p of products) {
      if (!p.dan) continue
      const e = map.get(p.dan.asset_id)
      if (e) e.count += 1
      else map.set(p.dan.asset_id, { dan: p.dan, count: 1 })
    }
    return map
  }, [products])

  const byId = new Map(products.map((p) => [p.product_id, p]))
  const featured = FEATURED_IDS.map((id) => byId.get(id)).filter((p): p is Product => !!p)
  const current = dans.get(STAGE[slide])?.dan

  return (
    <>
      <section className="hero2">
        <div className="container hero2-inner">
          <div className="hero2-copy">
            <p className="eyebrow">Campus Customs · 57 Broadway, New Haven</p>
            <h1>
              Bulldog pride,
              <br />
              <em>handsomely</em> made.
            </h1>
            <p className="hero-sub">
              Officially licensed Yale apparel for students, alumni and families. Modeled (enthusiastically) by Handsome Dan himself.
            </p>
            <div className="hero-actions">
              <Link to="/products" className="btn btn-brass">Shop all gear</Link>
              <button className="btn btn-ghost" onClick={() => document.querySelector<HTMLButtonElement>('.chat-fab')?.click()}>
                🐶 Ask Dan
              </button>
            </div>
            <ul className="hero-proof">
              <li><b>102</b> styles</li>
              <li><b>XS–XXL</b> live stock</li>
              <li><b>30-day</b> returns</li>
            </ul>
          </div>

          <div className="dan-stage" aria-label="Handsome Dan photo carousel">
            {STAGE.map((id, i) => (
              <img
                key={id}
                src={danSrc(id)}
                alt=""
                className={`dan-stage-img ${i === slide ? 'on' : ''}`}
                loading={i === 0 ? 'eager' : 'lazy'}
              />
            ))}
            {current && (
              <Link to={`/products?dan=${current.asset_id}`} className="dan-stage-caption" key={current.asset_id}>
                <span>{current.caption}</span>
                <b>Shop it →</b>
              </Link>
            )}
            <div className="dan-stage-dots">
              {STAGE.map((id, i) => (
                <button key={id} aria-label={`Show photo ${i + 1}`} className={i === slide ? 'on' : ''} onClick={() => setSlide(i)} />
              ))}
            </div>
          </div>
        </div>
      </section>

      {error && (
        <div className="container">
          <p className="notice">We couldn't reach the product server. Make sure the backend is running on port 8000.</p>
        </div>
      )}

      <section className="container section">
        <div className="section-head reveal">
          <div>
            <p className="kicker">Shop by category</p>
            <h2>Find your fit</h2>
          </div>
          <Link to="/products" className="link-arrow">View all 102 →</Link>
        </div>
        <div className="cat-grid2">
          {categories.map((c, i) => (
            <Link key={c.name} to={`/products?category=${encodeURIComponent(c.name)}`} className="cat-tile2 reveal" style={{ transitionDelay: `${i * 60}ms` }}>
              {CATEGORY_DAN[c.name] && <img src={danSrc(CATEGORY_DAN[c.name], '_sm')} alt="" loading="lazy" />}
              <span className="cat-tile2-label">
                <b>{c.name}</b>
                <small>{c.count} styles</small>
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="seasonal reveal">
        <div className="container seasonal-inner">
          <img src={danSrc('dan_custom_dan_carves_a_trumbull_pumpkin')} alt="Handsome Dan carving a bulldog jack-o'-lantern in the Trumbull College courtyard" loading="lazy" />
          <div>
            <p className="kicker light">October special</p>
            <h2>Halloween at Trumbull</h2>
            <p>
              Dan spent the afternoon carving his own face into a pumpkin. Celebrate the season in residential-college colors: crest
              quarter-zips and crewnecks for every college.
            </p>
            <Link to="/products?dan=dan_college_trumbull" className="btn btn-brass">Shop Trumbull</Link>{' '}
            <Link to="/products?q=college" className="btn btn-ghost">All colleges</Link>
          </div>
        </div>
      </section>

      {custom.length > 0 && (
        <section className="container section design-promo reveal">
          <div className="design-promo-copy">
            <p className="kicker">New · Custom Dan Gear</p>
            <h2>Design your own Handsome Dan</h2>
            <p className="muted">
              Dream up a Dan (rowing, studying, carving pumpkins, side-eyeing Harvard) and we'll put him on a tee, hoodie, cup,
              notebook and more. Tees from $24.99.
            </p>
            <Link to="/custom" className="btn btn-brass">Start designing</Link>
          </div>
          <div className="design-promo-row">
            {PROMO.map(([key, asset, title]) => {
              const p = custom.find((c) => c.key === key)
              return p ? (
                <Link key={key} to={`/custom?product=${key}&design=starter:${asset}`} className="design-promo-card">
                  <Mockup product={p} design={promoDesign(asset, title)} />
                  <span>{p.name}<small>{formatPrice(p.price)}</small></span>
                </Link>
              ) : null
            })}
          </div>
        </section>
      )}

      <section className="container section">
        <div className="section-head reveal">
          <div>
            <p className="kicker">Bulldog favorites</p>
            <h2>Best sellers this week</h2>
          </div>
          <Link to="/products" className="link-arrow">See more →</Link>
        </div>
        <div className="grid grid-4">
          {featured.map((p, i) => (
            <div key={p.product_id} className="reveal" style={{ transitionDelay: `${i * 70}ms` }}>
              <ProductCard product={p} />
            </div>
          ))}
        </div>
      </section>

      {RAILS.map((r) => {
        const items = [...dans.values()].filter((d) => d.dan.group === r.group)
        if (!items.length) return null
        return (
          <section key={r.group} className="container section rail-section">
            <div className="section-head reveal">
              <div>
                <p className="kicker">Shop with Dan</p>
                <h2>{r.title}</h2>
                <p className="muted">{r.blurb}</p>
              </div>
            </div>
            <div className="rail" role="list">
              {items.map(({ dan, count }) => (
                <Link key={dan.asset_id} to={`/products?dan=${dan.asset_id}`} className="rail-card" role="listitem">
                  <img src={dan.thumb_url} alt={`Handsome Dan: ${dan.category}`} loading="lazy" />
                  <span>
                    <b>{dan.category}</b>
                    <small>{count} item{count === 1 ? '' : 's'}</small>
                  </span>
                </Link>
              ))}
            </div>
          </section>
        )
      })}

      <section className="container section perks2 reveal">
        {[
          ['Officially licensed', 'Authentic Yale marks and crests on every piece.'],
          ['Honest stock', 'Live counts for every size, XS through XXL.'],
          ['Easy returns', 'Unworn with tags? Send it back within 30 days.'],
          ['Ask Dan', 'Our chat finds the right fit, color and size in seconds.'],
        ].map(([t, d]) => (
          <div key={t}>
            <h3>{t}</h3>
            <p>{d}</p>
          </div>
        ))}
      </section>
    </>
  )
}
