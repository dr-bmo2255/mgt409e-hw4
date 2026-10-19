import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { bagApi, formatDate, formatPrice } from '../api'
import Mockup from '../components/Mockup'
import { useAuth } from '../context/AuthContext'
import { useBag } from '../context/BagContext'

// The bag for Custom Dan Gear. Prices are always recomputed by the server (quantity breaks, XXL).
export default function Bag() {
  const { user, loading } = useAuth()
  const { bag, setBag, refresh } = useBag()
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

  if (!loading && !user) {
    return (
      <div className="container section bag-empty">
        <h1>Your bag</h1>
        <p className="muted">Log in to see your bag and your custom Dan designs.</p>
        <Link to="/login" className="btn btn-primary">Log in</Link>
      </div>
    )
  }

  return (
    <div className="container section">
      <div className="page-head">
        <h1>Your bag</h1>
        <p>{bag.count} item{bag.count === 1 ? '' : 's'}</p>
      </div>

      {bag.items.length === 0 ? (
        <div className="bag-empty">
          <p className="muted">Your bag is empty. Put Handsome Dan on something!</p>
          <Link to="/custom" className="btn btn-brass">Design with Dan</Link>
        </div>
      ) : (
        <div className="bag">
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

          <aside className="bag-summary">
            <h2>Summary</h2>
            <p className="bag-row"><span>Subtotal</span><b>{formatPrice(bag.subtotal)}</b></p>
            <p className="muted small">Shipping and tax are calculated at checkout. Quantity discounts are already applied.</p>
            <button className="btn btn-brass btn-block" disabled>Checkout (coming soon)</button>
            <p className="muted small">
              Online checkout isn't available in this demo. Visit us at 57 Broadway or email orderdept@campuscustoms.com to place
              your order. Custom gear is made to order and can't be returned.
            </p>
            <Link to="/custom" className="link-arrow">Keep designing →</Link>
          </aside>
        </div>
      )}
      {error && <p className="notice" role="alert">{error}</p>}
    </div>
  )
}
