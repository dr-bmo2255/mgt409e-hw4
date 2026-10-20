import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useBag } from '../context/BagContext'
import { useChatResults } from '../context/ChatResultsContext'

const LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/custom', label: 'Design with Dan' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const [open, setOpen] = useState(false)
  const { user, loading, logout } = useAuth()
  const { count } = useBag() // store items + custom gear, guests included
  const navigate = useNavigate()
  const chatResults = useChatResults()
  // Any top-menu click (or the logo) closes the menu and clears Dan's product suggestions from the top of the page,
  // so the chosen page shows from its top instead of sitting under the suggestions.
  const close = () => {
    setOpen(false)
    chatResults.clear()
  }

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

        {/* Phones: the menu is collapsed, so the bag and its badge also sit next to the menu button. */}
        <Link to="/bag" onClick={close} className="nav-bag-mobile" aria-label={`Bag, ${count} item${count === 1 ? '' : 's'}`}>
          <span aria-hidden>🛍</span>
          {count > 0 && <b className="bag-count" key={count}>{count}</b>}
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
            <NavLink to="/bag" onClick={close} className="nav-bag" aria-label={`Bag, ${count} item${count === 1 ? '' : 's'}`}>
              <span aria-hidden>🛍</span> Bag{count > 0 && <b className="bag-count" key={count}>{count}</b>}
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
