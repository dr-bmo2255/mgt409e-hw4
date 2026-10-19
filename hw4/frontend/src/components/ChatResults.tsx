import { useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useChatResults } from '../context/ChatResultsContext'
import ProductCard from './ProductCard'

// "From your chat" section: the agent's product matches rendered as normal product cards.
// Each card links to /products/:id, the same single-item page as the catalog.
export default function ChatResults() {
  const { results, clear } = useChatResults()
  const { pathname } = useLocation()
  const ref = useRef<HTMLElement>(null)
  const onDetail = pathname.startsWith('/products/')

  // New results arrived: bring them into view (not while reading a product page).
  useEffect(() => {
    if (results && !onDetail) ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [results?.id])

  if (!results) return null

  // On a product page, keep a slim link back instead of the full grid.
  if (onDetail) {
    return (
      <div className="chat-results-bar container">
        <span>
          {results.voice === 'dan' ? '🐶' : '💬'} From your chat: <strong>{results.title}</strong> ({results.products.length})
        </span>
        <Link to="/chat-results">View all</Link>
      </div>
    )
  }

  return (
    <section ref={ref} className="chat-results container" aria-label="Products from your chat" data-testid="chat-results">
      <div className="chat-results-head">
        <div>
          <p className="eyebrow">
            {results.voice === 'dan' ? '🐶 Fetched by Handsome Dan' : '💬 From your chat'} · “{results.query}”
          </p>
          <h2>
            {results.title} <small>{results.products.length} item{results.products.length === 1 ? '' : 's'}</small>
          </h2>
        </div>
        <div className="chat-results-actions">
          {results.seeAllCategory && (
            <Link to={`/products?category=${encodeURIComponent(results.seeAllCategory)}`} className="btn btn-ghost-dark">
              See all {results.seeAllCategory}
            </Link>
          )}
          <button className="btn btn-ghost-dark" onClick={clear}>
            Clear
          </button>
        </div>
      </div>
      {results.dan && (
        <figure className="results-dan" key={results.id}>
          <img src={results.dan.image_url} alt={`Handsome Dan: ${results.dan.category}`} />
          <figcaption>
            <span className="kicker light">Dan found it</span>
            <b>{results.dan.caption}</b>
          </figcaption>
        </figure>
      )}
      <div className="grid results-grid" key={`g${results.id}`}>
        {results.products.map((p, i) => (
          <div key={p.product_id} className="stagger" style={{ animationDelay: `${(results.dan ? 900 : 0) + i * 70}ms` }}>
            <ProductCard product={p} />
          </div>
        ))}
      </div>
    </section>
  )
}
