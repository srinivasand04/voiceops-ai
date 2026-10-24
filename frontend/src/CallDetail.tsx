import { useEffect, useState } from 'react'
import { api, label, type Analysis, type Transcript } from './api'
import { SentimentPill } from './Dashboard'

type Props = { id: number; onBack: () => void }

const clock = (seconds: number) =>
  `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`

const scoreColor = (score: number) =>
  score >= 0.25 ? 'var(--positive)' : score <= -0.25 ? 'var(--negative)' : 'var(--neutral)'

export default function CallDetail({ id, onBack }: Props) {
  const [transcript, setTranscript] = useState<Transcript | null>(null)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api<Transcript>(`/api/calls/${id}/transcript`),
      api<Analysis>(`/api/calls/${id}/analysis`),
    ])
      .then(([t, a]) => {
        setTranscript(t)
        setAnalysis(a)
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Could not load call'),
      )
  }, [id])

  const roleOf = (speaker: string) => analysis?.roles[speaker] ?? 'customer'
  const entityRows = Object.entries(analysis?.entities ?? {}).filter(
    ([, values]) => values.length > 0,
  )

  return (
    <>
      <div className="detail-head">
        <button className="btn" onClick={onBack}>
          ← Back
        </button>
        <h2>Call #{id}</h2>
        {analysis && (
          <>
            <span className="pill">{label(analysis.intents.primary)}</span>
            <SentimentPill value={analysis.sentiment.overall.label} />
            <span className="muted">
              customer sentiment {analysis.sentiment.customer_trend}
            </span>
          </>
        )}
      </div>

      {error && <div className="error">{error}</div>}

      {analysis && (
        <div className="card" style={{ marginBottom: 14 }}>
          <h3>Summary {analysis.summary_source === 'claude' && '(Claude)'}</h3>
          <p style={{ margin: '0 0 12px' }}>{analysis.summary}</p>
          <h3>Action items</h3>
          <ul className="clean">
            {analysis.action_items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {analysis && (
        <div className="grid two">
          <div className="card">
            <h3>Customer and agent sentiment</h3>
            {Object.entries(analysis.sentiment.speakers).map(([speaker, s]) => (
              <div key={speaker} style={{ marginBottom: 6 }}>
                <strong style={{ textTransform: 'capitalize' }}>{s.role}</strong>{' '}
                <SentimentPill value={s.label} />{' '}
                <span className="muted">
                  avg {s.average} over {s.turns} turns
                </span>
              </div>
            ))}
            <div className="timeline" style={{ marginTop: 14 }}>
              <div className="mid" />
              {analysis.sentiment.turns.map((turn, i) => (
                <div
                  className="col"
                  key={i}
                  title={`${turn.role} ${clock(turn.start)}: ${turn.score}`}
                >
                  <div
                    style={{
                      background: scoreColor(turn.score),
                      height: `${Math.abs(turn.score) * 50}%`,
                      ...(turn.score >= 0 ? { bottom: '50%' } : { top: '50%' }),
                      opacity: turn.role === 'agent' ? 0.55 : 1,
                    }}
                  />
                </div>
              ))}
            </div>
            <div className="legend">
              <span>Bars up = positive, down = negative, one per turn</span>
              <span>Faded = agent</span>
            </div>
          </div>

          <div className="card">
            <h3>Details found</h3>
            <dl className="entities">
              {entityRows.map(([name, values]) => (
                <div key={name} style={{ display: 'contents' }}>
                  <dt>{label(name)}</dt>
                  <dd>{values.join(', ')}</dd>
                </div>
              ))}
              {entityRows.length === 0 && <dd>Nothing detected.</dd>}
            </dl>
            <h3 style={{ marginTop: 16 }}>Keywords</h3>
            <div className="tags">
              {analysis.keywords.map((k) => (
                <span className="pill" key={k.keyword}>
                  {k.keyword}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {transcript && (
        <div className="card">
          <h3>
            Transcript · {transcript.language.toUpperCase()} ·{' '}
            {clock(transcript.duration)}
          </h3>
          <div className="chat">
            {transcript.turns.map((turn, i) => (
              <div className={`bubble ${roleOf(turn.speaker)}`} key={i}>
                <div className="meta">
                  <span
                    className="dot"
                    style={{
                      background:
                        roleOf(turn.speaker) === 'agent'
                          ? 'var(--agent)'
                          : 'var(--customer)',
                    }}
                  />
                  <strong style={{ textTransform: 'capitalize' }}>
                    {roleOf(turn.speaker)}
                  </strong>
                  {clock(turn.start)}
                </div>
                {turn.text}
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
