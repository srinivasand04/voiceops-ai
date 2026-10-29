export type User = { id: number; email: string; role: string }

export type CallRow = {
  id: number
  filename: string
  status: string
  error: string | null
  file_size: number
  created_at: string
  intent: string | null
  sentiment: string | null
  customer_sentiment: string | null
  order_ids: string[]
}

export type Stats = {
  total_calls: number
  processed_calls: number
  intents: Record<string, number>
  sentiments: Record<string, number>
  top_keywords: { keyword: string; count: number }[]
}

export type Turn = {
  start: number
  end: number
  speaker: string
  text: string
}

export type Transcript = {
  call_id: number
  language: string
  duration: number
  turns: Turn[]
}

export type TurnSentiment = {
  start: number
  end: number
  speaker: string
  role: string
  score: number
  label: string
}

export type Analysis = {
  call_id: number
  roles: Record<string, string>
  sentiment: {
    overall: { score: number; label: string }
    speakers: Record<
      string,
      { role: string; average: number; label: string; turns: number }
    >
    customer_trend: string
    turns: TurnSentiment[]
  }
  intents: { primary: string; all: string[] }
  entities: Record<string, string[]>
  keywords: { keyword: string; count: number }[]
  summary: string
  action_items: string[]
  summary_source: string
}

const TOKEN_KEY = 'voiceops_token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (token: string | null) =>
  token ? localStorage.setItem(TOKEN_KEY, token) : localStorage.removeItem(TOKEN_KEY)

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = getToken()

  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (typeof init.body === 'string') headers.set('Content-Type', 'application/json')

  const response = await fetch(path, { ...init, headers })

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = typeof body.detail === 'string' ? body.detail : 'Request failed'
    } catch {
      /* keep status text */
    }
    throw new ApiError(response.status, detail)
  }

  return response.json() as Promise<T>
}

export const label = (value: string | null) =>
  value ? value.replace(/_/g, ' ') : '-'
