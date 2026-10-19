import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useBag } from '../context/BagContext'

const LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/custom', label: 'Design with Dan' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const [open, setOpen] = useState(false)
  const { user, loading, logout } = useAuth()
  const { bag } = useBag()
  const navigate = useNavigate()
  const close = () => setOpen(false)

  return (
    <header className="header">
      <div className="announcement">Officially licensed Yale apparel · Visit us at 57 Broadway, New Haven</div>
      <nav className="nav container" aria-label="Main">
        <Link to="/" className="brand" onClick={close}>
          <span className="brand-mark">CC</span>
          <span className="brand-text">
            Campus Customs
            <small>Bulldog Blue · New Haven</small>
          </span>
        </Link>

        <button
          className="nav-toggle"
          aria-expanded={open}
          aria-controls="nav-links"
          onClick={() => setOpen((o) => !o)}
        >
          <span className="sr-only">Menu</span>☰
        </button>

        <ul id="nav-links" className={`nav-links ${open ? 'open' : ''}`}>
          {LINKS.map((l) => (
            <li key={l.to}>
              <NavLink to={l.to} end={l.end} onClick={close}>
                {l.label}
              </NavLink>
            </li>
          ))}
          <li>
            <NavLink to="/bag" onClick={close} className="nav-bag" aria-label={`Bag, ${bag.count} items`}>
              <span aria-hidden>🛍</span> Bag{bag.count > 0 && <b className="bag-count">{bag.count}</b>}
            </NavLink>
          </li>
          <li className="nav-divider" aria-hidden />
          {loading ? null : user ? (
            <>
              <li>
                <NavLink to="/account" onClick={close}>
                  Hi, {user.first_name}
                </NavLink>
              </li>
              <li>
                <button
                  className="nav-cta nav-button"
                  onClick={async () => {
                    close()
                    await logout()
                    navigate('/')
                  }}
                >
                  Log Out
                </button>
              </li>
            </>
          ) : (
            <>
              <li>
                <NavLink to="/login" onClick={close}>
                  Log In
                </NavLink>
              </li>
              <li>
                <NavLink to="/create-account" className="nav-cta" onClick={close}>
                  Create Account
                </NavLink>
              </li>
            </>
          )}
        </ul>
      </nav>
    </header>
  )
}
