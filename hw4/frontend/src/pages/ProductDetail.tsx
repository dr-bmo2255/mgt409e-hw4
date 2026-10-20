import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { DAN_AVATAR, colorName, displayName, fetchProduct, formatPrice, type Product } from '../api'
import { phraseFor } from '../danVoice'
import { swatch } from '../components/ProductCard'
import { useBag } from '../context/BagContext'

export default function ProductDetail() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [status, setStatus] = useState<'loading' | 'ok' | 'missing' | 'error'>('loading')
  const [size, setSize] = useState<string | null>(null)
  const [view, setView] = useState<'photo' | 'dan'>('photo')
  const [searchParams] = useSearchParams()
  const [color, setColor] = useState<string | null>(null) // Part D: chosen colorway (null = the original photo's)
  const { addStore } = useBag()
  const [added, setAdded] = useState<string | null>(null) // confirmation after "Add to bag"

  useEffect(() => {
    setStatus('loading')
    setSize(null)
    setView('photo')
    setAdded(null)
    setColor(searchParams.get('color'))
    fetchProduct(productId)
      .then((p) => {
        setProduct(p)
        setStatus('ok')
      })
      .catch((e: Error) => setStatus(e.message.startsWith('404') ? 'missing' : 'error'))
  }, [productId])

  if (status === 'loading') return <div className="container section"><p>Loading…</p></div>
  if (status !== 'ok' || !product) {
    return (
      <div className="container section">
        <p className="notice">
          {status === 'missing' ? "We couldn't find that product." : "We couldn't reach the product server."}
        </p>
        <Link to="/products" className="btn btn-primary">Back to products</Link>
      </div>
    )
  }

  const inventory = product.inventory ?? []
  const selected = inventory.find((s) => s.size === size)
  const shownColor = (color && product.colors.includes(color) ? color : null) ?? product.base_color ?? null
  // The photo for the chosen color, falling back to the original photo while a colorway has none yet.
  const photo = (shownColor && product.color_images?.[shownColor]) || product.image_url
  // Only the original (photographed) color is in inventory; the other colorways are custom orders (Part D).
  const customOrder = !!(product.base_color && shownColor && shownColor !== product.base_color)

  return (
    <div className="container section">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/products">Products</Link> /{' '}
        <Link to={`/products?category=${encodeURIComponent(product.category)}`}>{product.category}</Link> /{' '}
        <span>{displayName(product.name)}</span>
      </nav>

      <div className="detail">
        <div className="detail-gallery">
          <div className={`detail-img ${view === 'dan' ? 'show-dan' : ''}`}>
            <img key={photo} className="detail-photo colorway-in" src={photo} alt={`${displayName(product.name)}${shownColor ? ` in ${shownColor}` : ''}`} />
            {product.dan && <img className="detail-dan" src={product.dan.image_url} alt={`Handsome Dan: ${product.dan.category}`} />}
          </div>
          {product.dan && (
            <div className="detail-thumbs" role="tablist" aria-label="Product images">
              <button role="tab" aria-selected={view === 'photo'} className={view === 'photo' ? 'on' : ''} onClick={() => setView('photo')}>
                <img src={photo} alt="" />
                <span>The item</span>
              </button>
              <button role="tab" aria-selected={view === 'dan'} className={view === 'dan' ? 'on' : ''} onClick={() => setView('dan')}>
                <img src={product.dan.thumb_url} alt="" />
                <span>Dan's take</span>
              </button>
            </div>
          )}
          {product.dan && (
            <p className="dan-quote">
              <img src={DAN_AVATAR} alt="" /> <span>“{product.dan.caption}. {phraseFor(product.product_id)}” <small>— Handsome Dan</small></span>
            </p>
          )}
        </div>

        <div className="detail-info">
          <span className="card-cat">{product.garment_type}</span>
          <h1>{displayName(product.name)}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>
          <p className="detail-desc">{product.description}</p>

          {product.colors.length > 0 && (
            <div className="detail-row">
              <h3>
                Color: <span className="color-name">{shownColor ?? product.colors[0]}</span>
              </h3>
              <div className="swatches" role="radiogroup" aria-label="Color">
                {product.colors.map((c) => (
                  <button
                    key={c}
                    role="radio"
                    aria-checked={shownColor === c}
                    className={`swatch-btn ${shownColor === c ? 'on' : ''} ${product.color_images?.[c] ? '' : 'no-photo'}`}
                    onClick={() => {
                      setColor(c)
                      setView('photo')
                    }}
                    title={product.color_images?.[c] ? c : `${c} (photo coming soon)`}
                  >
                    <i style={{ background: swatch(c) }} />
                    <span>{c}</span>
                    {product.base_color && c !== product.base_color && <small className="swatch-custom">custom</small>}
                  </button>
                ))}
              </div>
              {shownColor && !product.color_images?.[shownColor] && (
                <p className="fine">A photo of the {shownColor} version is coming soon.</p>
              )}
              {customOrder && (
                <div className="custom-order" role="status">
                  <b>🧵 Custom order</b>
                  <span>
                    {shownColor && shownColor[0].toUpperCase() + shownColor.slice(1)} isn't on our shelves yet, so we'll make it for you in any size.
                    It will be <b>ready for pickup at 57 Broadway or delivery in 2–3 weeks</b>.
                  </span>
                  <button className="link-btn" onClick={() => setColor(product.base_color!)}>
                    In stock now: {product.base_color}
                  </button>
                </div>
              )}
            </div>
          )}

          <div className="detail-row">
            <h3>{customOrder ? 'Size (made to order)' : <>Size &amp; stock</>}</h3>
            <div className="sizes">
              {inventory.map((s) => (
                <button
                  key={s.size}
                  className={`size ${size === s.size ? 'active' : ''} ${s.quantity === 0 && !customOrder ? 'sold-out' : ''}`}
                  onClick={() => setSize(s.size)}
                  aria-pressed={size === s.size}
                >
                  {s.size}
                </button>
              ))}
            </div>
            {customOrder ? (
              <p className="stock-msg">
                {selected ? `${selected.size} in ${shownColor}: made to order, ready in 2–3 weeks.` : 'Every size is made to order in this color. Pick your size.'}
              </p>
            ) : (
            <>
            <p className="stock-msg">
              {selected
                ? selected.quantity === 0
                  ? `Sorry — size ${selected.size} is sold out.`
                  : selected.quantity <= 5
                    ? `Only ${selected.quantity} left in ${selected.size}.`
                    : `${selected.quantity} in stock in ${selected.size}.`
                : `${product.total_stock} in stock across all sizes. Pick a size to check availability.`}
            </p>
            <div className="stock-meters" aria-label="Stock by size">
              {inventory.map((s) => {
                const pct = Math.min(100, (s.quantity / 25) * 100)
                return (
                  <div key={s.size} className={`meter ${s.quantity === 0 ? 'zero' : s.quantity <= 5 ? 'low' : ''}`}>
                    <span className="meter-size">{s.size}</span>
                    <span className="meter-track"><span style={{ width: `${pct}%` }} /></span>
                    <span className="meter-qty">{s.quantity === 0 ? 'Sold out' : s.quantity <= 5 ? `${s.quantity} left` : `${s.quantity}`}</span>
                  </div>
                )
              })}
            </div>
            </>
            )}
          </div>

          <button
            className="btn btn-primary btn-block"
            disabled={!selected || (selected.quantity === 0 && !customOrder)}
            onClick={() => {
              if (!selected) return
              addStore({
                product_id: product.product_id,
                name: displayName(product.name),
                image_url: photo,
                price: product.price,
                size: selected.size,
                color: shownColor,
                custom_order: customOrder,
                max: customOrder ? 24 : selected.quantity,
              })
              setAdded(`${displayName(product.name)} · ${shownColor ? `${colorName(shownColor)} · ` : ''}Size ${selected.size}`)
            }}
          >
            {!selected ? 'Select a size' : customOrder ? 'Add custom order · ready in 2–3 weeks' : selected.quantity === 0 ? 'Sold out' : 'Add to bag'}
          </button>
          {added && (
            <p className="added-note" role="status">
              ✓ Added to your bag: {added}. <Link to="/bag">View bag →</Link>
            </p>
          )}
          <p className="fine">Checkout isn't part of this demo — ask the chat assistant about anything else.</p>

          {product.search_tags.length > 0 && (
            <div className="detail-row">
              <h3>Tags</h3>
              <div className="color-list">
                {product.search_tags.map((t) => (
                  <Link key={t} to={`/products?q=${encodeURIComponent(t)}`} className="tag tag-link">{t}</Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
