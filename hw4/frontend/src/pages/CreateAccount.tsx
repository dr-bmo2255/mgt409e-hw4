import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// Same rules as password_problems() in backend/auth.py (the server is the authority).
const PASSWORD_RULES = [
  { label: 'At least 8 characters', test: (p: string) => p.length >= 8 },
  { label: 'At least 1 number', test: (p: string) => /\d/.test(p) },
  { label: 'At least 1 symbol (like ! @ # $ %)', test: (p: string) => /[^A-Za-z0-9\s]/.test(p) },
]

const EMPTY = { first_name: '', last_name: '', email: '', password: '', confirm_password: '' }

export default function CreateAccount() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const set = (key: keyof typeof form) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }))

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    // Quick checks here for fast feedback; the backend enforces the same rules.
    const missing = PASSWORD_RULES.filter((r) => !r.test(form.password))
    if (missing.length) return setError(`Password needs: ${missing.map((r) => r.label.toLowerCase()).join(', ')}.`)
    if (form.password !== form.confirm_password) return setError('Passwords do not match.')
    setBusy(true)
    setError(null)
    try {
      await signup(form)
      navigate('/account', { replace: true, state: { welcome: true } })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container section auth">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Create account</h1>
        <p className="auth-sub">Save your chats and get personal recommendations.</p>
        <div className="auth-row">
          <label>
            First name
            <input required autoComplete="given-name" value={form.first_name} onChange={set('first_name')} />
          </label>
          <label>
            Last name
            <input required autoComplete="family-name" value={form.last_name} onChange={set('last_name')} />
          </label>
        </div>
        <label>
          Email
          <input type="email" required autoComplete="email" value={form.email} onChange={set('email')} />
        </label>
        <label>
          Password
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={form.password}
            onChange={set('password')}
          />
          <ul className="pw-rules" aria-live="polite">
            {PASSWORD_RULES.map((r) => (
              <li key={r.label} className={r.test(form.password) ? 'met' : ''}>
                {r.label}
              </li>
            ))}
          </ul>
        </label>
        <label>
          Confirm password
          <input
            type="password"
            required
            autoComplete="new-password"
            value={form.confirm_password}
            onChange={set('confirm_password')}
          />
        </label>
        {error && <p className="notice" role="alert">{error}</p>}
        <button className="btn btn-primary btn-block" disabled={busy}>{busy ? 'Creating…' : 'Create account'}</button>
        <p className="auth-alt">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  )
}
