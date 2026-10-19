import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { customApi, formatDate, type Design } from '../api'
import { useAuth } from '../context/AuthContext'

export default function Account() {
  const { user, loading, logout } = useAuth()
  const navigate = useNavigate()
  const welcome = (useLocation().state as { welcome?: boolean } | null)?.welcome
  const [designs, setDesigns] = useState<Design[]>([])

  // Custom Dans saved in the account (kept 90 days, Part C2).
  useEffect(() => {
    if (user) customApi.designs().then((d) => setDesigns(d.mine.filter((x) => x.status === 'ready'))).catch(() => undefined)
  }, [user])

  if (loading) return <div className="container section"><p>Loading…</p></div>
  if (!user) return <Navigate to="/login" replace state={{ from: '/account' }} />

  return (
    <div className="container section auth">
      <div className="auth-card">
        <h1>{welcome ? `Welcome, ${user.first_name}!` : `Hi, ${user.first_name}`}</h1>
        <p className="auth-sub">
          {welcome ? 'Your Campus Customs account is ready.' : "You're signed in to Campus Customs."}
        </p>
        <dl className="account-info">
          <dt>Name</dt>
          <dd>{user.first_name} {user.last_name}</dd>
          <dt>Email</dt>
          <dd>{user.email}</dd>
        </dl>
        <section className="account-designs">
          <h2>My Dan designs</h2>
          <p className="muted small">
            Designs you create are saved here for <b>90 days</b>, so you can come back and put them on more gear. After that they're deleted.
          </p>
          {designs.length === 0 ? (
            <Link to="/custom" className="link-arrow">Design your first Dan →</Link>
          ) : (
            <ul>
              {designs.map((d) => (
                <li key={d.ref}>
                  <Link to={`/custom?design=${encodeURIComponent(d.ref)}`}>
                    {d.thumb_url && <img src={d.thumb_url} alt="" />}
                    <span>
                      <b>{d.title}</b>
                      <small>Saved until {d.expires_at ? formatDate(d.expires_at) : '—'} · {d.days_left} days left</small>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
        <Link to="/products" className="btn btn-primary btn-block">Start shopping</Link>
        <button
          className="btn btn-ghost-dark btn-block"
          onClick={async () => {
            await logout()
            navigate('/', { replace: true })
          }}
        >
          Log out
        </button>
      </div>
    </div>
  )
}
