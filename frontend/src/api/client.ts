const API_BASE = '/api'

function getAuthHeaders(): Record<string, string> {
  const t = localStorage.getItem('ailover_token')
  return t ? { Authorization: `Bearer ${t}` } : {}
}

async function fetchApi<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v != null && v !== '') url.searchParams.set(k, String(v))
    })
  }
  const res = await fetch(url.toString(), { headers: getAuthHeaders() })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export const api = {
  characters: (params?: {
    element?: string
    weapon?: string
    rarity?: number
    body_type?: string
    region?: string
    race?: string
    gender?: string
    zodiac?: string
    month?: number
    q?: string
  }) => fetchApi<import('../types/character').Character[]>(`${API_BASE}/characters`, params),
  character: (id: string) => fetchApi<import('../types/character').Character | null>(`${API_BASE}/characters/${id}`),
  stats: () => fetchApi<import('../types/character').Stats>(`${API_BASE}/characters/stats`),
  filterOptions: () =>
    fetchApi<{ race: string[]; gender: string[] }>(`${API_BASE}/characters/filter-options`),
  random: () => fetchApi<import('../types/character').Character | null>(`${API_BASE}/characters/random`),
  today: () => fetchApi<import('../types/character').Character | null>(`${API_BASE}/characters/today`),
  birthdayCalendar: () =>
    fetchApi<Record<string, Array<{ character_id: string; name: string; birthday: string; day: number; image_url?: string }>>>(
      `${API_BASE}/characters/birthday-calendar`
    ),
  chatStream: async (characterId: string, content: string, onChunk: (chunk: string) => void) => {
    const r = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({ character_id: characterId, content }),
    })
    
    if (!r.ok) {
      const data = await r.json().catch(() => ({}))
      throw new Error(r.status === 429 ? (data.detail || '请求过于频繁，请稍后再试') : `API error: ${r.status}`)
    }
    
    const reader = r.body?.getReader()
    if (!reader) throw new Error('无响应流')
    const decoder = new TextDecoder()
    let reply = ''
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6).trim()
          if (dataStr === '[DONE]') break
          if (dataStr) {
            try {
              const parsed = JSON.parse(dataStr)
              if (parsed.chunk) {
                reply += parsed.chunk
                onChunk(parsed.chunk)
              }
            } catch (e) {}
          }
        }
      }
    }
    return { reply }
  },
  chat: (characterId: string, content: string) =>
    fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({ character_id: characterId, content }),
    }).then(async (r) => {
      const data = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(r.status === 429 ? (data.detail || '请求过于频繁，请稍后再试') : `API error: ${r.status}`)
      return data as { reply: string }
    }),
  messages: (characterId: string) =>
    fetchApi<{ role: string; content: string }[]>(`${API_BASE}/conversations/${characterId}/messages`),
}
