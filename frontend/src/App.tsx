import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import CharacterList from './pages/CharacterList'
import CharacterDetail from './pages/CharacterDetail'
import BirthdayCalendar from './pages/BirthdayCalendar'
import ChatPage from './pages/ChatPage'
import LoginPage from './pages/LoginPage'
import { useAuth } from './contexts/AuthContext'

function App() {
  const { username, logout } = useAuth()
  return (
    <div style={{ minHeight: '100vh' }}>
      <nav
        style={{
          padding: '12px 24px',
          background: 'rgba(0,0,0,0.3)',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          display: 'flex',
          gap: '24px',
          alignItems: 'center',
        }}
      >
        <Link to="/" style={{ fontWeight: 600, color: '#fff' }}>
          原神角色图鉴
        </Link>
        <Link to="/characters">角色列表</Link>
        <Link to="/birthday">生日日历</Link>
        {username ? (
          <span style={{ marginLeft: 'auto', display: 'flex', gap: 12, alignItems: 'center' }}>
            {username}
            <button onClick={logout} style={{ background: 'none', border: 'none', color: '#7dd3fc', cursor: 'pointer', fontSize: 14 }}>退出</button>
          </span>
        ) : (
          <Link to="/login" style={{ marginLeft: 'auto' }}>登录</Link>
        )}
      </nav>
      <main style={{ padding: '24px', maxWidth: 1200, margin: '0 auto' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/characters" element={<CharacterList />} />
          <Route path="/characters/:id" element={<CharacterDetail />} />
          <Route path="/characters/:id/chat" element={<ChatPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/birthday" element={<BirthdayCalendar />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
