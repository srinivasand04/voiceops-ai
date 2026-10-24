import { useState } from 'react'
import { api, setToken, type User } from './api'

type Props = { onLogin: (user: User) => void }

export default function Login({ onLogin }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')

    try {
      const data = await api<{ token: string; user: User }>(
        `/api/auth/${mode}`,
        { method: 'POST', body: JSON.stringify({ email, password }) },
      )
      setToken(data.token)
      onLogin(data.user)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="shell">
      <div className="card auth">
        <div className="brand">
          VoiceOps <span>AI</span>
        </div>
        <p className="notice">
          {mode === 'login'
            ? 'Sign in to see your call intelligence.'
            : 'Create an account. The first account becomes the admin.'}
        </p>

        <form onSubmit={submit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password (8+ characters)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />
          {error && <div className="error">{error}</div>}
          <button className="btn primary" disabled={busy}>
            {busy ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <p className="notice">
          {mode === 'login' ? 'No account yet? ' : 'Already registered? '}
          <button
            className="btn small"
            type="button"
            onClick={() => {
              setMode(mode === 'login' ? 'register' : 'login')
              setError('')
            }}
          >
            {mode === 'login' ? 'Register' : 'Sign in'}
          </button>
        </p>
      </div>
    </div>
  )
}
