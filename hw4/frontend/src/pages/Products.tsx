import { useEffect, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { fetchCategories, fetchProducts, type Category, type Product } from '../api'
import ProductCard from '../components/ProductCard'

type Sort = 'name' | 'price-asc' | 'price-desc'

export default function Products() {
  const [params, setParams] = useSearchParams()
  const category = params.get('category') ?? ''
  const q = params.get('q') ?? ''
  const danId = params.get('dan') ?? '' // Dan category filter (from Home rails / chat)
  const [products, setProducts] = useState<Product[] | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [error, setError] = useState(false)
  const [search, setSearch] = useState(q)
  const [sort, setSort] = useState<Sort>('name')

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => setError(true))
  }, [])

  useEffect(() => {
    setProducts(null)
    setSearch(q)
    fetchProducts({ q, category })
      .then(setProducts)
      .catch(() => setError(true))
  }, [q, category])

  function update(next: { q?: string; category?: string }) {
    const merged = { q, category, ...next }
    const p = new URLSearchParams()
    if (merged.q) p.set('q', merged.q)
    if (merged.category) p.set('category', merged.category)
    setParams(p)
  }

  function onSearch(e: FormEvent) {
    e.preventDefault()
    update({ q: search.trim() })
  }

  const visible = (products ?? []).filter((p) => !danId || p.dan?.asset_id === danId)
  const dan = danId ? visible[0]?.dan : null
  const sorted = [...visible].sort((a, b) =>
    sort === 'price-asc' ? a.price - b.price : sort === 'price-desc' ? b.price - a.price : a.name.localeCompare(b.name),
  )

  return (
    <div className="container section">
      <div className="page-head">
        <h1>{dan ? dan.category : category || 'All products'}</h1>
        <p>{products ? `${visible.length} item${visible.length === 1 ? '' : 's'}` : 'Loading…'}</p>
      </div>

      {dan && (
        <div className="dan-banner">
          <img src={dan.image_url} alt={`Handsome Dan: ${dan.category}`} />
          <div>
            <p className="kicker">Shop with Dan</p>
            <h2>{dan.caption}</h2>
            <p className="muted">Every item below shares this look. Pick your size and color.</p>
            <Link to="/products" className="link-arrow">← All products</Link>
          </div>
        </div>
      )}

      <div className="toolbar">
        <form onSubmit={onSearch} className="search">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search bulldog, navy, Berkeley…"
            aria-label="Search products"
          />
          <button type="submit" className="btn btn-primary">Search</button>
          {q && (
            <button type="button" className="btn btn-ghost-dark" onClick={() => update({ q: '' })}>
              Clear
            </button>
          )}
        </form>
        <label className="sort">
          Sort
          <select value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
            <option value="name">Name</option>
            <option value="price-asc">Price: low to high</option>
            <option value="price-desc">Price: high to low</option>
          </select>
        </label>
      </div>

      <div className="chips" role="group" aria-label="Filter by category">
        <button className={!category ? 'chip active' : 'chip'} onClick={() => update({ category: '' })}>
          All
        </button>
        {categories.map((c) => (
          <button
            key={c.name}
            className={category === c.name ? 'chip active' : 'chip'}
            onClick={() => update({ category: c.name })}
          >
            {c.name} <small>{c.count}</small>
          </button>
        ))}
      </div>

      {error && <p className="notice">We couldn't reach the product server. Make sure the backend is running on port 8000.</p>}
      {products && visible.length === 0 && <p className="empty">No products match that search. Try another word.</p>}

      <div className="grid">
        {products === null && !error
          ? Array.from({ length: 8 }, (_, i) => <div key={i} className="card skeleton" />)
          : sorted.map((p) => <ProductCard key={p.product_id} product={p} />)}
      </div>
    </div>
  )
}
