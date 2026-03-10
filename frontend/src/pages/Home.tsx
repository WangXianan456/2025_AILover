import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { getImageSrc } from '../utils/image'
import type { Character } from '../types/character'

export default function Home() {
  const [today, setToday] = useState<Character | null>(null)
  const [random, setRandom] = useState<Character | null>(null)
  const [stats, setStats] = useState<{ total: number } | null>(null)

  useEffect(() => {
    Promise.all([api.today(), api.random(), api.stats()]).then(([t, r, s]) => {
      setToday(t)
      setRandom(r)
      setStats(s)
    })
  }, [])

  const img = (c: Character) =>
    getImageSrc((c.portraits && c.portraits['立绘']) || c.official_intro?.portrait_url || c.image_url)

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>原神角色图鉴</h1>
      <p style={{ color: '#aaa', marginBottom: 32 }}>
        将角色当真人对待：生日、星座、地区、贺图、故事…… 多维度筛选与推荐。
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 24 }}>
        <section
          style={{
            background: 'var(--bg-card)',
            borderRadius: 12,
            padding: 24,
            border: '1px solid rgba(255,255,255,0.08)',
          }}
        >
          <h2 style={{ margin: '0 0 16px', fontSize: 18 }}>今日推荐</h2>
          {today ? (
            <Link to={`/characters/${today.character_id}`} style={{ display: 'block', color: 'inherit' }}>
              <img
                src={img(today)}
                alt={today.name}
                referrerPolicy="no-referrer"
                loading="lazy"
                decoding="async"
                style={{
                  width: '100%',
                  aspectRatio: '1',
                  objectFit: 'cover',
                  borderRadius: 8,
                  marginBottom: 12,
                }}
              />
              <div style={{ fontWeight: 600 }}>{today.name}</div>
              <div style={{ fontSize: 14, color: '#aaa' }}>
                {today.title && `${today.title} · `}
                {today.element} · {today.weapon}
              </div>
            </Link>
          ) : (
            <p style={{ color: '#888' }}>暂无数据，请先导出角色数据</p>
          )}
        </section>

        <section
          style={{
            background: 'var(--bg-card)',
            borderRadius: 12,
            padding: 24,
            border: '1px solid rgba(255,255,255,0.08)',
          }}
        >
          <h2 style={{ margin: '0 0 16px', fontSize: 18 }}>随机邂逅</h2>
          {random ? (
            <Link to={`/characters/${random.character_id}`} style={{ display: 'block', color: 'inherit' }}>
              <img
                src={img(random)}
                alt={random.name}
                referrerPolicy="no-referrer"
                loading="lazy"
                decoding="async"
                style={{
                  width: '100%',
                  aspectRatio: '1',
                  objectFit: 'cover',
                  borderRadius: 8,
                  marginBottom: 12,
                }}
              />
              <div style={{ fontWeight: 600 }}>{random.name}</div>
              <div style={{ fontSize: 14, color: '#aaa' }}>
                {random.birthday && `${random.birthday} · `}
                {random.zodiac}
              </div>
            </Link>
          ) : (
            <p style={{ color: '#888' }}>暂无数据</p>
          )}
        </section>

        <section
          style={{
            background: 'var(--bg-card)',
            borderRadius: 12,
            padding: 24,
            border: '1px solid rgba(255,255,255,0.08)',
          }}
        >
          <h2 style={{ margin: '0 0 16px', fontSize: 18 }}>数据概览</h2>
          {stats && (
            <div style={{ fontSize: 48, fontWeight: 700, color: '#6eb5ff' }}>{stats.total}</div>
          )}
          <p style={{ margin: 0, color: '#aaa' }}>已收录角色</p>
          <Link to="/characters" style={{ display: 'inline-block', marginTop: 12 }}>
            浏览全部 →
          </Link>
        </section>
      </div>

      <div style={{ marginTop: 48 }}>
        <Link to="/birthday" style={{ fontSize: 18 }}>
          📅 查看生日日历 →
        </Link>
      </div>
    </div>
  )
}
