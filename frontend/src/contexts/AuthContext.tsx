import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

const TOKEN_KEY = 'ailover_token'

type AuthContextType = {
  token: string | null
  username: string | null
  login: (t: string, u: string) => void
  logout: () => void
  isReady: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [username, setUsername] = useState<string | null>(null)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    const t = localStorage.getItem(TOKEN_KEY)
    if (t) {
      setToken(t)
      fetch('/api/auth/me', { headers: { Authorization: `Bearer ${t}` } })
        .then((r) => (r.ok ? r.json() : null))
        .then((d) => d && setUsername(d.username))
        .catch(() => localStorage.removeItem(TOKEN_KEY))
    }
    setIsReady(true)
  }, [])

  const login = (t: string, u: string) => {
    localStorage.setItem(TOKEN_KEY, t)
    setToken(t)
    setUsername(u)
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUsername(null)
  }

  return (
    <AuthContext.Provider value={{ token, username, login, logout, isReady }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth outside AuthProvider')
  return ctx
}
