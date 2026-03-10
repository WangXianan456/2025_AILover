import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api/client'
import { getImageSrc } from '../utils/image'
import type { Character } from '../types/character'

export default function CharacterDetail() {
  const { id } = useParams<{ id: string }>()
  const [char, setChar] = useState<Character | null>(null)

  useEffect(() => {
    if (id) api.character(id).then(setChar)
  }, [id])

  if (!char) return <p>加载中...</p>

  const portrait = getImageSrc(
    (char.portraits && (char.portraits['立绘2'] || char.portraits['立绘'])) || char.official_intro?.portrait_url || char.image_url
  )

  const statsEntries = Object.entries(char.stats || {})

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', gap: 12, alignItems: 'center' }}>
        <Link to="/characters">← 返回列表</Link>
        <Link to={`/characters/${id}/chat`} style={{ color: '#7dd3fc', fontWeight: 500 }}>
          与 {char.name} 对话
        </Link>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(200px, 1fr) 2fr', gap: 32, alignItems: 'start' }}>
        <div>
          <img
            src={portrait}
            alt={char.name}
            referrerPolicy="no-referrer"
            decoding="async"
            style={{
              width: '100%',
              borderRadius: 12,
              border: '1px solid rgba(255,255,255,0.1)',
            }}
          />
          <div style={{ marginTop: 16, fontSize: 14, color: '#aaa' }}>
            {char.title && <div>称号：{char.title}</div>}
            {char.birthday && <div>生日：{char.birthday}</div>}
            {char.zodiac && <div>星座：{char.zodiac}</div>}
            {char.region && <div>地区：{char.region}</div>}
            {char.body_type && <div>体型：{char.body_type}</div>}
            {char.affiliation && <div>所属：{char.affiliation}</div>}
            {char.occupation && <div>职业：{char.occupation}</div>}
            {char.nicknames && char.nicknames.length > 0 && (
              <div>昵称：{char.nicknames.join('、')}</div>
            )}
            {char.voice_actors && (
              <div style={{ marginTop: 8 }}>
                CV：{char.voice_actors.cn || char.voice_actors.jp || '-'}
              </div>
            )}
          </div>
        </div>

        <div>
          <h1 style={{ margin: '0 0 8px' }}>{char.name}</h1>
          <div style={{ color: '#aaa', marginBottom: 24 }}>
            {char.element} · {char.weapon} · {char.rarity}星
          </div>

          {char.official_intro?.title && (
            <section style={{ marginBottom: 24 }}>
              <h2 style={{ fontSize: 18, marginBottom: 8 }}>{char.official_intro.title}</h2>
              <p style={{ lineHeight: 1.8, color: '#ddd' }}>{char.official_intro.description}</p>
            </section>
          )}

          {char.official_intro?.story_er && (
            <section style={{ marginBottom: 24 }}>
              <h2 style={{ fontSize: 18, marginBottom: 8 }}>贰·故事</h2>
              <p style={{ lineHeight: 1.8, color: '#ddd', whiteSpace: 'pre-wrap' }}>
                {char.official_intro.story_er}
              </p>
            </section>
          )}

          {char.birthday_greetings && char.birthday_greetings.length > 0 && (
            <section style={{ marginBottom: 24 }}>
              <h2 style={{ fontSize: 18, marginBottom: 12 }}>生日贺图</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {char.birthday_greetings.map((g) => (
                  <div
                    key={g.year}
                    style={{
                      background: 'var(--bg-card)',
                      padding: 16,
                      borderRadius: 8,
                      border: '1px solid rgba(255,255,255,0.08)',
                    }}
                  >
                    <div style={{ fontWeight: 600, marginBottom: 8 }}>{g.year}年</div>
                    {g.text && (
                      <p style={{ margin: '0 0 12px', lineHeight: 1.6, color: '#ccc', fontSize: 14 }}>
                        {g.text}
                      </p>
                    )}
                    {g.image_url && (
                      <img
                        src={getImageSrc(g.image_url)}
                        alt={`${char.name} ${g.year}`}
                        referrerPolicy="no-referrer"
                        loading="lazy"
                        decoding="async"
                        style={{ maxWidth: 300, borderRadius: 8 }}
                      />
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {char.festival_greetings && char.festival_greetings.length > 0 && (
            <section style={{ marginBottom: 24 }}>
              <h2 style={{ fontSize: 18, marginBottom: 12 }}>节日贺图</h2>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
                {char.festival_greetings.map((g) => (
                  <div
                    key={g.label}
                    style={{
                      background: 'var(--bg-card)',
                      padding: 16,
                      borderRadius: 8,
                      border: '1px solid rgba(255,255,255,0.08)',
                      maxWidth: 280,
                    }}
                  >
                    <div style={{ fontWeight: 600, marginBottom: 8 }}>{g.label}</div>
                    {g.text && (
                      <p style={{ margin: '0 0 12px', lineHeight: 1.5, color: '#ccc', fontSize: 13 }}>
                        {g.text.slice(0, 80)}...
                      </p>
                    )}
                    {g.image_url && (
                      <img
                        src={getImageSrc(g.image_url)}
                        alt={g.label}
                        referrerPolicy="no-referrer"
                        loading="lazy"
                        decoding="async"
                        style={{ maxWidth: '100%', borderRadius: 6 }}
                      />
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {char.constellations && char.constellations.length > 0 && (
            <section style={{ marginBottom: 24 }}>
              <h2 style={{ fontSize: 18, marginBottom: 12 }}>命之座</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {char.constellations.map((c, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 12,
                      background: 'rgba(255,255,255,0.03)',
                      borderRadius: 6,
                      fontSize: 14,
                    }}
                  >
                    <strong>{c.name}</strong>：{c.effect}
                  </div>
                ))}
              </div>
            </section>
          )}

          {statsEntries.length > 0 && (
            <section style={{ marginBottom: 24 }}>
              <h2 style={{ fontSize: 18, marginBottom: 12 }}>首表详细信息</h2>
              <table
                style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: 14,
                }}
              >
                <tbody>
                  {statsEntries.map(([k, v]) => (
                    <tr key={k}>
                      <td
                        style={{
                          padding: '6px 8px',
                          borderBottom: '1px solid rgba(255,255,255,0.06)',
                          width: 120,
                          color: '#aaa',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {k}
                      </td>
                      <td
                        style={{
                          padding: '6px 8px',
                          borderBottom: '1px solid rgba(255,255,255,0.06)',
                          color: '#ddd',
                          lineHeight: 1.5,
                        }}
                      >
                        {v}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}
