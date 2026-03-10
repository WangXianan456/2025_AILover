import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { getImageSrc } from '../utils/image'

interface BirthdayEntry {
  character_id: string
  name: string
  birthday: string
  day: number
  image_url?: string
}

const MONTH_NAMES = [
  '一月', '二月', '三月', '四月', '五月', '六月',
  '七月', '八月', '九月', '十月', '十一月', '十二月',
]

export default function BirthdayCalendar() {
  const [calendar, setCalendar] = useState<Record<string, BirthdayEntry[]>>({})
  const [activeMonth, setActiveMonth] = useState<string>('')

  useEffect(() => {
    api.birthdayCalendar().then((data) => {
      setCalendar(data)
      const months = Object.keys(data).sort((a, b) => Number(a) - Number(b))
      if (months.length > 0) {
        const now = new Date().getMonth() + 1
        setActiveMonth(months.includes(String(now)) ? String(now) : months[0])
      }
    })
  }, [])

  const months = Object.keys(calendar).sort((a, b) => Number(a) - Number(b))
  const entries = activeMonth ? (calendar[activeMonth] || []) : []

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>生日日历</h1>
      <p style={{ color: '#aaa', marginBottom: 24 }}>
        按月份查看角色生日，像真人一样记住他们的生日。
      </p>

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 8,
          marginBottom: 24,
        }}
      >
        {months.map((m) => (
          <button
            key={m}
            onClick={() => setActiveMonth(m)}
            style={{
              padding: '8px 16px',
              borderRadius: 8,
              border: activeMonth === m ? '2px solid #6eb5ff' : '1px solid #444',
              background: activeMonth === m ? 'rgba(110,181,255,0.2)' : 'var(--bg-card)',
              color: '#fff',
              cursor: 'pointer',
            }}
          >
            {MONTH_NAMES[Number(m) - 1]}
          </button>
        ))}
      </div>

      {activeMonth && (
        <section>
          <h2 style={{ marginBottom: 16 }}>{MONTH_NAMES[Number(activeMonth) - 1]} 生日</h2>
          {entries.length === 0 ? (
            <p style={{ color: '#888' }}>该月暂无角色生日</p>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
                gap: 16,
              }}
            >
              {entries.map((e) => (
                <Link
                  key={e.character_id}
                  to={`/characters/${e.character_id}`}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    padding: 16,
                    background: 'var(--bg-card)',
                    borderRadius: 12,
                    border: '1px solid rgba(255,255,255,0.08)',
                    color: 'inherit',
                  }}
                >
                  <img
                    src={getImageSrc(e.image_url)}
                    alt={e.name}
                    referrerPolicy="no-referrer"
                    loading="lazy"
                    decoding="async"
                    style={{
                      width: 80,
                      height: 80,
                      objectFit: 'cover',
                      borderRadius: 8,
                      marginBottom: 8,
                    }}
                  />
                  <div style={{ fontWeight: 600 }}>{e.name}</div>
                  <div style={{ fontSize: 13, color: '#6eb5ff' }}>{e.birthday}</div>
                </Link>
              ))}
            </div>
          )}
        </section>
      )}

      {months.length === 0 && (
        <p style={{ color: '#888', textAlign: 'center', padding: 48 }}>
          暂无生日数据。请先运行 <code>python scripts/export_characters.py</code> 导出数据。
        </p>
      )}
    </div>
  )
}
