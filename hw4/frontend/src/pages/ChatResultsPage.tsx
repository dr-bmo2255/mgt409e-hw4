import { Link } from 'react-router-dom'
import { useChatResults } from '../context/ChatResultsContext'

// The "From your chat" grid itself is rendered by <ChatResults /> above the routes;
// this page just gives it a home to come back to from a product page.
export default function ChatResultsPage() {
  const { results } = useChatResults()
  if (results) return null
  return (
    <div className="container section">
      <h1>No chat results yet</h1>
      <p>Ask the chat assistant something like “what hoodies do you have?” and matching items will appear here.</p>
      <Link to="/products" className="btn btn-primary">Browse all products</Link>
    </div>
  )
}
