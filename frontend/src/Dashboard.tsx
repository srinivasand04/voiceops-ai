import { useCallback, useEffect, useRef, useState } from 'react'
import { api, label, type CallRow, type Stats } from './api'

type Props = { onOpen: (id: number) => void }

function Bars({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1])
  const max = Math.max(1, ...entries.map(([, n]) => n))

  if (entries.length === 0) return <div className="notice">No data yet.</div>

  return (
    <>
      {entries.map(([name, count]) => (
        <div className="bar-row" key={name}>
          <span>{label(name)}</span>
          <div className="bar">
            <div style={{ width: `${(count / max) * 100}%` }} />
          </div>
          <span>{count}</span>
        </div>
      ))}
    </>
  )
}

export function SentimentPill({ value }: { value: string | null }) {
  return value ? <span className={`pill ${value}`}>{value}</span> : <>-</>
}

export default function Dashboard({ onOpen }: Props) {
  const [stats, setStats] = useState<Stats | null>(null)
  const [calls, setCalls] = useState<CallRow[]>([])
  const [error, setError] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState('')
  const input = useRef<HTMLInputElement>(null)

  const load = useCallback(async () => {
    try {
      const [s, c] = await Promise.all([
        api<Stats>('/api/stats'),
        api<CallRow[]>('/api/calls'),
      ])
      setStats(s)
      setCalls(c)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load data')
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load()
  }, [load])

  // Keep the table fresh while any call is still being processed.
  const anyProcessing = calls.some((c) => c.status === 'processing')

  useEffect(() => {
    if (!anyProcessing) return
    const timer = setInterval(load, 5000)
    return () => clearInterval(timer)
  }, [anyProcessing, load])

  const uploadAndProcess = async () => {
    if (!file) return
    setError('')

    try {
      setBusy('Uploading...')
      const body = new FormData()
      body.append('file', file)
      const call = await api<{ id: number }>('/api/calls/upload', {
        method: 'POST',
        body,
      })

      await api(`/api/calls/${call.id}/process`, { method: 'POST' })
      setFile(null)
      if (input.current) input.current.value = ''
      await load()

      // Processing runs on the server in the background: poll until it ends.
      const started = Date.now()
      for (;;) {
        const seconds = Math.round((Date.now() - started) / 1000)
        setBusy(`Transcribing and analyzing... ${seconds}s (usually 1-2 minutes)`)
        await new Promise((resolve) => setTimeout(resolve, 3000))

        const current = await api<CallRow>(`/api/calls/${call.id}`)
        if (current.status === 'failed') {
          throw new Error(current.error ?? 'Processing failed')
        }
        if (current.status === 'processed') break
      }

      await load()
      onOpen(call.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Processing failed')
      await load()
    } finally {
      setBusy('')
    }
  }

  const customerMood = stats?.sentiments ?? {}

  return (
    <>
      <div className="grid stats">
        <div className="card stat">
          <div className="value">{stats?.total_calls ?? '-'}</div>
          <div className="label">Total calls</div>
        </div>
        <div className="card stat">
          <div className="value">{stats?.processed_calls ?? '-'}</div>
          <div className="label">Analyzed</div>
        </div>
        <div className="card stat">
          <div className="value">{customerMood.positive ?? 0}</div>
          <div className="label">Positive calls</div>
        </div>
        <div className="card stat">
          <div className="value">{customerMood.negative ?? 0}</div>
          <div className="label">Negative calls</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 14 }}>
        <h3>Analyze a new call</h3>
        <div className="upload-row">
          <input
            ref={input}
            type="file"
            accept=".wav,.mp3,.mpeg,audio/*"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            disabled={!!busy}
          />
          <button
            className="btn primary"
            onClick={uploadAndProcess}
            disabled={!file || !!busy}
          >
            Upload and analyze
          </button>
          {busy && <span className="notice">{busy}</span>}
        </div>
        {error && <div className="error" style={{ marginTop: 8 }}>{error}</div>}
      </div>

      <div className="grid two">
        <div className="card">
          <h3>Call reasons</h3>
          <Bars data={stats?.intents ?? {}} />
        </div>
        <div className="card">
          <h3>Overall sentiment</h3>
          <Bars data={stats?.sentiments ?? {}} />
          <h3 style={{ marginTop: 16 }}>Top keywords</h3>
          <div className="tags">
            {(stats?.top_keywords ?? []).map((k) => (
              <span className="pill" key={k.keyword}>
                {k.keyword} · {k.count}
              </span>
            ))}
            {stats?.top_keywords.length === 0 && (
              <span className="notice">No data yet.</span>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Calls</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>File</th>
                <th>Status</th>
                <th>Reason</th>
                <th>Customer mood</th>
                <th>Order</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {calls.map((call) => (
                <tr className="click" key={call.id} onClick={() => onOpen(call.id)}>
                  <td>{call.id}</td>
                  <td>{call.filename}</td>
                  <td title={call.error ?? undefined}>
                    {call.status}
                    {call.status === 'failed' && call.error ? ' ⚠' : ''}
                  </td>
                  <td>{label(call.intent)}</td>
                  <td>
                    <SentimentPill value={call.customer_sentiment} />
                  </td>
                  <td>{call.order_ids.join(', ') || '-'}</td>
                  <td>{new Date(call.created_at).toLocaleString()}</td>
                </tr>
              ))}
              {calls.length === 0 && (
                <tr>
                  <td colSpan={7} className="notice">
                    No calls yet. Upload one above.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
