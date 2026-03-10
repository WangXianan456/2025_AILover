import { useState } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const submit = async () => {
    setErr('')
    if (!username.trim() || !password) {
      setErr('请填写用户名和密码')
      return
    }
    setLoading(true)
    try {
      const path = mode === 'login' ? '/auth/login' : '/auth/register'
      const res = await fetch(`/api${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.trim(), password }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const d = data.detail
        const msg = Array.isArray(d) ? d[0]?.msg : (typeof d === 'string' ? d : null)
        setErr(msg || data.message || '请求失败')
        return
      }
      login(data.token, data.username)
      navigate(location.state?.from || '/', { replace: true })
    } catch (e) {
      setErr((e as Error).message === 'Failed to fetch' ? '网络错误，请检查后端是否已启动' : (e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 360, margin: '40px auto' }}>
      <h1 style={{ marginBottom: 24 }}>{mode === 'login' ? '登录' : '注册'}</h1>
      <form
        onSubmit={(e) => { e.preventDefault(); submit() }}
        style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
      >
        <input
          id="username"
          name="username"
          type="text"
          placeholder="用户名"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{ padding: 12, borderRadius: 8, border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(0,0,0,0.3)', color: '#fff' }}
        />
        <input
          id="password"
          name="password"
          type="password"
          placeholder="密码"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ padding: 12, borderRadius: 8, border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(0,0,0,0.3)', color: '#fff' }}
        />
        {err && <p style={{ color: '#f87171', fontSize: 14 }}>{err}</p>}
        <button type="button" onClick={submit} disabled={loading} style={{ padding: 12, borderRadius: 8, border: 'none', background: 'rgba(100,150,255,0.6)', color: '#fff', cursor: loading ? 'not-allowed' : 'pointer' }}>
          {loading ? '...' : mode === 'login' ? '登录' : '注册'}
        </button>
        <button
          type="button"
          onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setErr('') }}
          style={{ background: 'none', border: 'none', color: '#7dd3fc', cursor: 'pointer', fontSize: 14 }}
        >
          {mode === 'login' ? '没有账号？去注册' : '已有账号？去登录'}
        </button>
      </form>
      <Link to="/" style={{ display: 'block', marginTop: 24, color: '#888' }}>← 返回首页</Link>
    </div>
  )
}
