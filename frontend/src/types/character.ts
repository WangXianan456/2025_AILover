export interface Character {
  character_id: string
  name: string
  title?: string
  rarity?: number
  element?: string
  weapon?: string
  image_url?: string
  detail_url?: string
  birthday?: string
  birthday_parsed?: { month: number; day: number }
  zodiac?: string
  region?: string
  body_type?: string
  nicknames?: string[]
  voice_actors?: { cn?: string; jp?: string; kr?: string; en?: string }
  affiliation?: string
  occupation?: string
  story?: string
  stories?: Record<string, string>
  portraits?: Record<string, string>
  official_intro?: {
    portrait_url?: string
    title?: string
    description?: string
    story_er?: string
  }
  birthday_greetings?: Array<{ year: string; text: string; image_url: string }>
  festival_greetings?: Array<{ label: string; text: string; image_url: string }>
  constellations?: Array<{ name: string; effect: string }>
  skills?: Array<{ name: string; description: string }>
  stats?: Record<string, string>
}

export interface Stats {
  total: number
  by_element: Record<string, number>
  by_weapon: Record<string, number>
  by_rarity: Record<string, number>
  by_region: Record<string, number>
  by_zodiac: Record<string, number>
  by_body_type: Record<string, number>
  by_birthday_month: Record<string, number>
}
