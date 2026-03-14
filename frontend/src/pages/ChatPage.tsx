import { useEffect, useRef, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { getImageSrc } from '../utils/image'
import { useAuth } from '../contexts/AuthContext'
import type { Character } from '../types/character'

type Message = { role: 'user' | 'assistant'; content: string }

export default function ChatPage() {
  const { id } = useParams<{ id: string }>()
  const { token, isReady } = useAuth()
  const navigate = useNavigate()
  const [char, setChar] = useState<Character | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isReady && !token) {
      navigate('/login', { state: { from: `/characters/${id}/chat` } })
      return
    }
    if (id) {
      api.character(id).then(setChar)
      if (token) api.messages(id).then(msgs => setMessages(msgs as Message[])).catch(() => navigate('/login'))
    }
  }, [id, token, isReady, navigate])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || !char || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: text }, { role: 'assistant', content: '' }])
    setLoading(true)
    try {
      await api.chatStream(char.character_id, text, (chunk) => {
        setMessages((m) => {
          const newMessages = [...m]
          const lastIndex = newMessages.length - 1
          if (newMessages[lastIndex].role === 'assistant') {
            newMessages[lastIndex] = {
              ...newMessages[lastIndex],
              content: newMessages[lastIndex].content + chunk,
            }
          }
          return newMessages
        })
      })
    } catch (e) {
      setMessages((m) => {
        const newMessages = [...m]
        const lastIndex = newMessages.length - 1
        if (newMessages[lastIndex].role === 'assistant') {
          newMessages[lastIndex] = {
            ...newMessages[lastIndex],
            content: newMessages[lastIndex].content || `发送失败: ${(e as Error).message}`
          }
        }
        return newMessages
      })
    } finally {
      setLoading(false)
    }
  }

  if (!char) return <p>加载中...</p>

  const portrait = getImageSrc(
    (char.portraits && (char.portraits['立绘2'] || char.portraits['立绘'])) ||
      char.official_intro?.portrait_url ||
      char.image_url
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <Link to={`/characters/${id}`}>← 返回</Link>
        <img
          src={portrait}
          alt={char.name}
          style={{ width: 48, height: 48, borderRadius: 8, objectFit: 'cover' }}
        />
        <span style={{ fontWeight: 600, fontSize: 18 }}>{char.name}</span>
      </div>

      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: 16,
          background: 'rgba(0,0,0,0.2)',
          borderRadius: 12,
          marginBottom: 16,
        }}
      >
        {messages.length === 0 && (
          <p style={{ color: '#888', textAlign: 'center', marginTop: 40 }}>和 {char.name} 打个招呼吧～</p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              marginBottom: 12,
              display: 'flex',
              justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              style={{
                maxWidth: '75%',
                padding: '10px 14px',
                borderRadius: 12,
                background: m.role === 'user' ? 'rgba(100,150,255,0.25)' : 'rgba(255,255,255,0.08)',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ color: '#888', fontSize: 14 }}>正在输入...</div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder="输入消息..."
          disabled={loading}
          style={{
            flex: 1,
            padding: '12px 16px',
            borderRadius: 8,
            border: '1px solid rgba(255,255,255,0.2)',
            background: 'rgba(0,0,0,0.3)',
            color: '#fff',
            fontSize: 14,
          }}
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          style={{
            padding: '12px 24px',
            borderRadius: 8,
            border: 'none',
            background: 'rgba(100,150,255,0.6)',
            color: '#fff',
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
          }}
        >
          发送
        </button>
      </div>
    </div>
  )
}
