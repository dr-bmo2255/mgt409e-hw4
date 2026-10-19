import { Link, useNavigate } from 'react-router-dom'
import { displayName, formatPrice, type Product } from '../api'

// The fields a card needs. Catalog products and chat results (ChatProduct) both fit.
export type CardProduct = Pick<
  Product,
  'product_id' | 'name' | 'category' | 'image_url' | 'description' | 'price' | 'colors' | 'total_stock' | 'dan'
>

// Hover / keyboard focus cross-fades the product photo to "Dan's take" on that category.
export default function ProductCard({ product }: { product: CardProduct }) {
  const lowStock = product.total_stock > 0 && product.total_stock < 40
  const name = displayName(product.name)
  const navigate = useNavigate()
  return (
    <Link to={`/products/${product.product_id}`} className={`card ${product.dan ? 'has-dan' : ''}`}>
      <div className="card-img">
        <img className="card-photo" src={product.image_url} alt={name} loading="lazy" />
        {product.dan && (
          <>
            <img className="card-dan" src={product.dan.thumb_url} alt="" loading="lazy" />
            <span className="card-dan-tag">🐶 Dan's take</span>
          </>
        )}
        {lowStock && <span className="badge badge-warn">Low stock</span>}
      </div>
      <div className="card-body">
        <span className="card-cat">{product.category}</span>
        <h3 className="card-title">{name}</h3>
        <p className="card-desc">{product.description}</p>
        <div className="card-foot">
          <span className="price">{formatPrice(product.price)}</span>
          {product.colors.length > 0 && (
            <span className="card-colors" title={product.colors.join(', ')}>
              {product.colors.slice(0, 3).map((c) => (
                <i
                  key={c}
                  className="swatch"
                  style={{ background: swatch(c) }}
                  title={`See it in ${c}`}
                  onClick={(e) => {
                    // Part D: open the product page already showing this colorway.
                    e.preventDefault()
                    navigate(`/products/${product.product_id}?color=${encodeURIComponent(c)}`)
                  }}
                />
              ))}
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}

// Color words → swatch colors (falls back to a neutral gray).
export function swatch(c: string): string {
  const s = c.toLowerCase()
  if (s.includes('navy')) return '#14254a'
  if (s.includes('charcoal')) return '#3d4148'
  if (s.includes('heather') || s.includes('gray') || s.includes('grey')) return '#a7aab0'
  if (s.includes('white') || s.includes('ivory') || s.includes('cream')) return '#f3efe6'
  if (s.includes('black')) return '#1b1b1b'
  if (s.includes('red') || s.includes('crimson')) return '#b3242c'
  if (s.includes('royal') || s.includes('blue')) return '#2b5bb5'
  if (s.includes('yellow') || s.includes('gold')) return '#e2b93b'
  if (s.includes('green')) return '#3f7d4e'
  if (s.includes('pink') || s.includes('salmon') || s.includes('coral')) return '#e88c7d'
  if (s.includes('purple')) return '#5a3b8c'
  return '#c9c4b8'
}
