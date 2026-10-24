import { useEffect, useState } from 'react'
import { api, ApiError, getToken, setToken, type User } from './api'
import CallDetail from './CallDetail'
import Dashboard from './Dashboard'
import Login from './Login'
import './App.css'

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [checking, setChecking] = useState(!!getToken())
  const [openCall, setOpenCall] = useState<number | null>(null)

  useEffect(() => {
    if (!getToken()) return

    api<User>('/api/auth/me')
      .then(setUser)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) setToken(null)
      })
      .finally(() => setChecking(false))
  }, [])

  const logout = () => {
    setToken(null)
    setUser(null)
    setOpenCall(null)
  }

  if (checking) return <div className="shell notice">Loading...</div>
  if (!user) return <Login onLogin={setUser} />

  return (
    <div className="shell">
      <div className="topbar">
        <div className="brand">
          VoiceOps <span>AI</span>
        </div>
        <div className="topbar-right">
          {user.email} ({user.role})
          <button className="btn small" onClick={logout}>
            Sign out
          </button>
        </div>
      </div>

      {openCall === null ? (
        <Dashboard onOpen={setOpenCall} />
      ) : (
        <CallDetail id={openCall} onBack={() => setOpenCall(null)} />
      )}
    </div>
  )
}

export default App
