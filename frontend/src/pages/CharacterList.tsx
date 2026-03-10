import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { getImageSrc } from '../utils/image'
import type { Character, Stats } from '../types/character'

const ELEMENTS = ['火', '水', '风', '雷', '草', '岩', '冰', '无']
const WEAPONS = ['单手剑', '双手剑', '长柄武器', '法器', '弓', '无']
const BODY_TYPES = ['少女', '成女', '少年', '成男', '少年/少女']
const REGIONS = ['蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬', '坎瑞亚', '其他']

export default function CharacterList() {
  const [chars, setChars] = useState<Character[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [filters, setFilters] = useState<{
    element?: string
    weapon?: string
    rarity?: number
    body_type?: string
    region?: string
    race?: string
    gender?: string
    month?: number
    q?: string
  }>({})
  const [loading, setLoading] = useState(true)

  const [filterOptions, setFilterOptions] = useState<{ race: string[]; gender: string[] }>({ race: [], gender: [] })

  useEffect(() => {
    api.stats().then(setStats)
    api.filterOptions().then(setFilterOptions)
  }, [])

  useEffect(() => {
    setLoading(true)
    api.characters(filters).then((data) => {
      setChars(data)
      setLoading(false)
    })
  }, [filters])

  const updateFilter = (k: keyof typeof filters, v: string | number | undefined) => {
    setFilters((prev) => ({ ...prev, [k]: v === '' || v === undefined ? undefined : v }))
  }

  const img = (c: Character) =>
    getImageSrc((c.portraits && (c.portraits['立绘2'] || c.portraits['立绘'])) || c.official_intro?.portrait_url || c.image_url)


  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>角色列表</h1>

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 12,
          marginBottom: 24,
          padding: 16,
          background: 'var(--bg-card)',
          borderRadius: 8,
          border: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <input
          type="text"
          placeholder="搜索角色名、昵称、故事..."
          value={filters.q || ''}
          onChange={(e) => updateFilter('q', e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: 6,
            border: '1px solid #444',
            background: '#222',
            color: '#fff',
            minWidth: 200,
          }}
        />
        <select
          value={filters.element || ''}
          onChange={(e) => updateFilter('element', e.target.value || undefined)}
          style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #444', background: '#222', color: '#fff' }}
        >
          <option value="">全部元素</option>
          {ELEMENTS.map((e) => (
            <option key={e} value={e}>
              {e}
            </option>
          ))}
        </select>
        <select
          value={filters.weapon || ''}
          onChange={(e) => updateFilter('weapon', e.target.value || undefined)}
          style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #444', background: '#222', color: '#fff' }}
        >
          <option value="">全部武器</option>
          {WEAPONS.map((w) => (
            <option key={w} value={w}>
              {w}
            </option>
          ))}
        </select>
        <select
          value={filters.rarity ?? ''}
          onChange={(e) => updateFilter('rarity', e.target.value ? Number(e.target.value) : undefined)}
          style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #444', background: '#222', color: '#fff' }}
        >
          <option value="">全部稀有度</option>
          <option value="5">5星</option>
          <option value="4">4星</option>
        </select>
        <select
          value={filters.body_type || ''}
          onChange={(e) => updateFilter('body_type', e.target.value || undefined)}
          style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #444', background: '#222', color: '#fff' }}
        >
          <option value="">全部体型</option>
          {BODY_TYPES.map((b) => (
            <option key={b} value={b}>
              {b}
            </option>
          ))}
        </select>
        <select
          value={filters.region || ''}
          onChange={(e) => updateFilter('region', e.target.value || undefined)}
          style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #444', background: '#222', color: '#fff' }}
        >
          <option value="">全部地区</option>
          {REGIONS.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <select
          value={filters.race || ''}
          onChange={(e) => updateFilter('race', e.target.value || undefined)}
          style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #444', background: '#222', color: '#fff' }}
        >
          <option value="">全部种族</option>
          {filterOptions.race.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
        <select
          value={filters.gender || ''}
          onChange={(e) => updateFilter('gender', e.target.value || undefined)}
          style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #444', background: '#222', color: '#fff' }}
        >
          <option value="">全部性别</option>
          {filterOptions.gender.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
        <select
          value={filters.month ?? ''}
          onChange={(e) => updateFilter('month', e.target.value ? Number(e.target.value) : undefined)}
          style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #444', background: '#222', color: '#fff' }}
        >
          <option value="">全部月份</option>
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((m) => (
            <option key={m} value={m}>
              {m}月生日
            </option>
          ))}
        </select>
      </div>

      {stats && (
        <p style={{ color: '#aaa', marginBottom: 16 }}>
          共 {chars.length} 个角色
          {Object.keys(filters).some((k) => filters[k as keyof typeof filters] != null) && '（已筛选）'}
        </p>
      )}

      {loading ? (
        <p>加载中...</p>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
            gap: 16,
          }}
        >
          {chars.map((c) => (
            <Link
              key={c.character_id}
              to={`/characters/${c.character_id}`}
              style={{
                background: 'var(--bg-card)',
                borderRadius: 12,
                overflow: 'hidden',
                border: '1px solid rgba(255,255,255,0.08)',
                color: 'inherit',
                transition: 'transform 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'scale(1.02)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'scale(1)'
              }}
            >
              <img
                src={img(c)}
                alt={c.name}
                referrerPolicy="no-referrer"
                loading="lazy"
                decoding="async"
                style={{
                  width: '100%',
                  aspectRatio: '1',
                  objectFit: 'cover',
                }}
              />
              <div style={{ padding: 12 }}>
                <div style={{ fontWeight: 600 }}>{c.name}</div>
                <div style={{ fontSize: 12, color: '#aaa' }}>
                  {c.element} · {c.weapon}
                  {c.birthday && ` · ${c.birthday}`}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {!loading && chars.length === 0 && (
        <p style={{ color: '#888', textAlign: 'center', padding: 48 }}>
          暂无匹配角色。请先运行 <code>python scripts/export_characters.py</code> 导出数据。
        </p>
      )}
    </div>
  )
}
