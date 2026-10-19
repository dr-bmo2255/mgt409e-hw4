import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="container section">
      <h1>Page not found</h1>
      <p>That page wandered off campus.</p>
      <Link to="/" className="btn btn-primary">Back home</Link>
    </div>
  )
}
