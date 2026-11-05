import { useEffect, useState } from 'react'
import { loadClaimEvidenceHistory } from '../api'
import type { ClaimEvidenceHistory as History } from '../types'

export function ClaimEvidenceHistory({ recordId, claimId }: {
  recordId: string
  claimId: string
}) {
  const [history, setHistory] = useState<History | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setHistory(null)
    setError(null)
    loadClaimEvidenceHistory(recordId, claimId, controller.signal)
      .then(value => {
        if (!controller.signal.aborted) setHistory(value)
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : 'Local review ledger unavailable.')
        }
      })
    return () => controller.abort()
  }, [recordId, claimId])

  if (error) return <p className="claim-evidence-state" role="status">Local review history unavailable: {error}</p>
  if (!history) return <p className="claim-evidence-state" role="status">Loading local review history…</p>
  if (history.database_state === 'absent') {
    return <p className="claim-evidence-state">No local evidence ledger. The source link remains unreviewed.</p>
  }

  return (
    <div className="claim-evidence-history">
      <strong>Local review ledger · not published evidence</strong>
      <p className="claim-evidence-state">{history.identity_note}</p>
      {history.sources.map(source => {
        const events = history.events.filter(item => item.source_uid === source.source_uid)
        return (
          <div key={source.source_uid}>
            <p><strong>Assessment state:</strong> {source.status.replaceAll('-', ' ')}
              {' · '}{source.active_reviewer_count} self-declared reviewer
              {source.active_reviewer_count === 1 ? '' : 's'}
            </p>
            {source.status === 'independent-agreement-recorded' && (
              <p>Multiple matching reviewer labels are recorded. This is not independently authenticated or a verified claim.</p>
            )}
            {events.length > 0 && (
              <details>
                <summary>{events.length} append-only review event{events.length === 1 ? '' : 's'}</summary>
                <ol>
                  {events.map(event => (
                    <li key={event.event_id}>
                      <p><strong>{event.decision.replaceAll('-', ' ')}</strong>
                        {' · '}{event.reviewer_id} · {event.created_at}
                        {!event.current && ' · stale claim/source snapshot'}
                      </p>
                      <p>Locator: {event.locator_kind}, {event.locator}</p>
                      {event.excerpt && <blockquote>{event.excerpt}</blockquote>}
                      <p>{event.note}</p>
                    </li>
                  ))}
                </ol>
              </details>
            )}
          </div>
        )
      })}
    </div>
  )
}
