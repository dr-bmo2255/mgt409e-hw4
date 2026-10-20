import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { bagApi, colorName, formatDate, formatPrice } from '../api'
import Mockup from '../components/Mockup'
import { useAuth } from '../context/AuthContext'
import { useBag } from '../context/BagContext'

// The bag: store items (anyone, kept in this browser) and Custom Dan Gear (signed-in customers; the server
// recomputes those prices with quantity breaks and XXL). Checkout isn't part of the demo.
export default function Bag() {
  const { user, loading } = useAuth()
  const { bag, setBag, refresh, store, setStoreQty, removeStore, count, storeSubtotal } = useBag()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void refresh()
  }, [refresh])

  async function run(p: Promise<typeof bag>) {
    setError(null)
    try {
      setBag(await p)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const subtotal = Math.round((storeSubtotal + bag.subtotal) * 100) / 100
  const hasCustomOrder = store.some((l) => l.custom_order)

  return (
    <div className="container section">
      <div className="page-head">
        <h1>Your bag</h1>
        <p>{count} item{count === 1 ? '' : 's'}</p>
      </div>

      {count === 0 ? (
        <div className="bag-empty">
          <p className="muted">Your bag is empty. Handsome Dan is disappointed, but he believes in you.</p>
          <p className="era-actions">
            <Link to="/products" className="btn btn-primary">Shop all gear</Link>
            <Link to="/custom" className="btn btn-brass">Design with Dan</Link>
          </p>
          {!loading && !user && <p className="muted small"><Link to="/login">Log in</Link> to see the custom Dan gear saved to your account.</p>}
        </div>
      ) : (
        <div className="bag">
          <div>
            {store.length > 0 && (
              <>
                <h2 className="bag-section-title">From the store</h2>
                <ul className="bag-list">
                  {store.map((l) => (
                    <li key={l.key} className="bag-item">
                      <Link to={`/products/${l.product_id}${l.color ? `?color=${encodeURIComponent(l.color)}` : ''}`} className="bag-thumb" aria-label={`View ${l.name}`}>
                        <img src={l.image_url} alt="" />
                      </Link>
                      <div className="bag-info">
                        <b>{l.name}</b>
                        <span className="muted small">
                          {l.color ? `${colorName(l.color)} · ` : ''}Size {l.size}
                        </span>
                        {l.custom_order && <span className="small custom-order-tag">Custom order · ready for pickup or delivery in 2–3 weeks</span>}
                        <span className="small">{formatPrice(l.price)} each</span>
                        <div className="bag-actions">
                          <div className="qty" aria-label="Quantity">
                            <button onClick={() => setStoreQty(l.key, l.quantity - 1)} aria-label="Fewer" disabled={l.quantity <= 1}>−</button>
                            <input readOnly value={l.quantity} aria-label="Quantity" />
                            <button onClick={() => setStoreQty(l.key, l.quantity + 1)} aria-label="More" disabled={l.quantity >= l.max}>+</button>
                          </div>
                          <button className="link-btn" onClick={() => removeStore(l.key)}>Remove</button>
                        </div>
                        {!l.custom_order && l.quantity >= l.max && <span className="small muted">That's all we have in {l.size}.</span>}
                      </div>
                      <span className="price bag-line">{formatPrice(l.price * l.quantity)}</span>
                    </li>
                  ))}
                </ul>
              </>
            )}

            {bag.items.length > 0 && (
              <>
                <h2 className="bag-section-title">Custom Dan Gear</h2>
                <ul className="bag-list">
                  {bag.items.map((it) => (
                    <li key={it.id} className="bag-item">
                      <Link to={`/custom?product=${it.product.key}&design=${encodeURIComponent(it.design.ref)}`} className="bag-thumb" aria-label={`Edit ${it.product.name}`}>
                        <Mockup product={it.product} design={it.design} placement={it.placement} />
                      </Link>
                      <div className="bag-info">
                        <b>{it.product.name}</b>
                        <span className="muted small">
                          {it.product.color} · Size {it.size} · Design: {it.design.title}
                        </span>
                        {it.design.expires_at && (
                          <span className="small keep-line">Your design is saved until {formatDate(it.design.expires_at)} ({it.design.days_left} days)</span>
                        )}
                        <span className="small">{formatPrice(it.unit_price)} each</span>
                        <div className="bag-actions">
                          <div className="qty" aria-label="Quantity">
                            <button onClick={() => void run(bagApi.setQty(it.id, Math.max(1, it.quantity - 1)))} aria-label="Fewer" disabled={it.quantity <= 1}>−</button>
                            <input readOnly value={it.quantity} aria-label="Quantity" />
                            <button onClick={() => void run(bagApi.setQty(it.id, Math.min(144, it.quantity + 1)))} aria-label="More">+</button>
                          </div>
                          <button className="link-btn" onClick={() => void run(bagApi.remove(it.id))}>Remove</button>
                        </div>
                      </div>
                      <span className="price bag-line">{formatPrice(it.line_total)}</span>
                    </li>
                  ))}
                </ul>
              </>
            )}
            {!loading && !user && (
              <p className="muted small"><Link to="/login">Log in</Link> to add custom Dan gear or see what's saved to your account.</p>
            )}
          </div>

          <aside className="bag-summary">
            <h2>Summary</h2>
            <p className="bag-row"><span>Subtotal</span><b>{formatPrice(subtotal)}</b></p>
            <p className="muted small">
              Shipping and tax are calculated at checkout.{bag.items.length > 0 ? ' Quantity discounts are already applied.' : ''}
              {hasCustomOrder ? ' Custom-order colors are ready for pickup or delivery in 2–3 weeks.' : ''}
            </p>
            <button className="btn btn-brass btn-block" disabled>Checkout (not available in this demo)</button>
            <p className="muted small">
              This is a class demo, so orders can't be placed or paid for here.{bag.items.length > 0 ? ' Custom gear is made to order and can\'t be returned.' : ''}
            </p>
            <Link to="/products" className="link-arrow">Keep shopping →</Link>
          </aside>
        </div>
      )}
      {error && <p className="notice" role="alert">{error}</p>}
    </div>
  )
}
