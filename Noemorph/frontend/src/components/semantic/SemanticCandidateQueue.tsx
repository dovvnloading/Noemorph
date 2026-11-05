import type { SemanticCandidateSummary } from '../../types'

interface SemanticCandidateQueueProps {
  items: SemanticCandidateSummary[]
  total: number
  offset: number
  limit: number
  selectedId?: string
  loading: boolean
  onSelect: (candidate: SemanticCandidateSummary) => void
  onPageChange: (offset: number) => void
}

function percentage(value?: number): string {
  if (value === undefined || !Number.isFinite(value)) return '—'
  const normalized = value <= 1 ? value * 100 : value
  return `${Math.round(normalized)}%`
}

function readableFlag(flag: string): string {
  return flag.replaceAll('-', ' ').replaceAll('_', ' ')
}

export function SemanticCandidateQueue({
  items,
  total,
  offset,
  limit,
  selectedId,
  loading,
  onSelect,
  onPageChange,
}: SemanticCandidateQueueProps) {
  const first = total === 0 ? 0 : offset + 1
  const last = Math.min(offset + items.length, total)
  const canGoBack = offset > 0 && !loading
  const canGoForward = offset + limit < total && !loading

  return (
    <section className="semantic-queue" aria-label="Candidate relationship queue">
      <div className="semantic-queue-heading">
        <strong>Review queue</strong>
        <span>{first}–{last} of {total}</span>
      </div>

      <div className="semantic-queue-scroll" aria-busy={loading}>
        {loading && items.length === 0 && (
          <div className="semantic-queue-state">
            <strong>Loading candidates</strong>
            <p>Retrieving one review page from the local semantic index.</p>
          </div>
        )}
        {!loading && items.length === 0 && (
          <div className="semantic-queue-state">
            <strong>No candidates in this view</strong>
            <p>Broaden the focus or lower the minimum review priority.</p>
          </div>
        )}
        {items.map((candidate) => {
          const flags = (candidate.flags ?? []).slice(0, 2)
          const sourceNote = candidate.source_overlap_count === 0
            ? 'no shared citation locator'
            : candidate.source_overlap_count
              ? `${candidate.source_overlap_count} shared source${candidate.source_overlap_count === 1 ? '' : 's'}`
              : undefined
          return (
            <button
              type="button"
              key={candidate.id}
              className={`semantic-candidate-row ${candidate.id === selectedId ? 'selected' : ''}`}
              onClick={() => onSelect(candidate)}
              aria-pressed={candidate.id === selectedId}
            >
              <span className="semantic-candidate-pair">
                <strong>{candidate.record_a.name}</strong>
                <i>with</i>
                <strong>{candidate.record_b.name}</strong>
              </span>
              <span className="semantic-candidate-score">
                <b>{percentage(candidate.semantic_similarity)}</b>
                <small>similarity</small>
              </span>
              <span className="semantic-candidate-context">
                {[candidate.record_a.domain, candidate.record_b.domain].filter(Boolean).join(' / ') || 'Domain metadata unavailable'}
              </span>
              <span className="semantic-candidate-basis">
                {[...flags.map(readableFlag), sourceNote].filter(Boolean).join(' · ') || 'Semantic proximity candidate'}
              </span>
            </button>
          )
        })}
      </div>

      <footer className="semantic-queue-pagination">
        <button type="button" disabled={!canGoBack} onClick={() => onPageChange(Math.max(0, offset - limit))}>Previous</button>
        <span>Page {total === 0 ? 0 : Math.floor(offset / limit) + 1}</span>
        <button type="button" disabled={!canGoForward} onClick={() => onPageChange(offset + limit)}>Next</button>
      </footer>
    </section>
  )
}
