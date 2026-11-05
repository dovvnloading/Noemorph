import { useEffect, useState } from 'react'
import type { SemanticCandidateDetail, SemanticRelationTag, SemanticReviewUpdate } from '../../types'

const RELATION_TAGS: Array<{ value: SemanticRelationTag; label: string }> = [
  { value: 'possible-convergence', label: 'Possible convergence' },
  { value: 'possible-contrast', label: 'Possible contrast' },
  { value: 'shared-mechanism', label: 'Shared mechanism' },
  { value: 'shared-phenomenology', label: 'Shared phenomenology' },
  { value: 'shared-method', label: 'Shared method' },
  { value: 'possible-lineage', label: 'Possible lineage' },
  { value: 'terminological-overlap', label: 'Terminological overlap' },
  { value: 'artifact-risk', label: 'Artifact risk' },
]

interface SemanticReviewFormProps {
  candidate: SemanticCandidateDetail
  pending: boolean
  error?: string
  onSubmit: (review: SemanticReviewUpdate) => Promise<void>
}

function dispositionLabel(disposition: SemanticCandidateDetail['disposition']): string {
  if (!disposition || disposition === 'unreviewed') return 'Unreviewed'
  if (disposition === 'shortlisted') return 'Shortlisted research lead'
  if (disposition === 'needs-review') return 'Needs further review'
  return 'Dismissed'
}

export function SemanticReviewForm({ candidate, pending, error, onSubmit }: SemanticReviewFormProps) {
  const [shortlistOpen, setShortlistOpen] = useState(false)
  const [reviseOpen, setReviseOpen] = useState(false)
  const [tag, setTag] = useState<SemanticRelationTag>(candidate.relation_tag ?? 'possible-convergence')
  const [note, setNote] = useState(candidate.reviewer_note ?? '')
  const evidenceStatus = candidate.prior_art
    ? 'Focused prior-art screen attached; independent scholarly review is still required.'
    : 'Embedding signal only; prior art has not been screened.'

  useEffect(() => {
    setShortlistOpen(false)
    setReviseOpen(false)
    setTag(candidate.relation_tag ?? 'possible-convergence')
    setNote(candidate.reviewer_note ?? '')
  }, [candidate.id, candidate.relation_tag, candidate.reviewer_note])

  if (candidate.disposition && candidate.disposition !== 'unreviewed' && !reviseOpen) {
    return (
      <footer className="semantic-review-recorded">
        <div>
          <span>REVIEW DISPOSITION</span>
          <strong>{dispositionLabel(candidate.disposition)}</strong>
          {candidate.relation_tag && <small>{candidate.relation_tag.replaceAll('-', ' ')}</small>}
        </div>
        {candidate.reviewer_note && <p>{candidate.reviewer_note}</p>}
        <button type="button" onClick={() => setReviseOpen(true)}>Change disposition</button>
      </footer>
    )
  }

  if (shortlistOpen) {
    return (
      <footer className="semantic-review-form">
        <div className="semantic-review-form-heading">
          <strong>Shortlist as a research lead</strong>
          <button type="button" onClick={() => setShortlistOpen(false)} disabled={pending}>Cancel</button>
        </div>
        <label>
          <span>Working relationship</span>
          <select value={tag} onChange={(event) => setTag(event.target.value as SemanticRelationTag)} disabled={pending}>
            {RELATION_TAGS.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}
          </select>
        </label>
        <label>
          <span>Reviewer note</span>
          <textarea
            value={note}
            onChange={(event) => setNote(event.target.value)}
            rows={3}
            placeholder="State what merits examination; do not assert a relationship the evidence has not established."
            disabled={pending}
          />
        </label>
        {error && <p className="semantic-review-error" role="alert">{error}</p>}
        <button
          type="button"
          className="semantic-review-primary"
          disabled={pending || !note.trim()}
          onClick={() => void onSubmit({ disposition: 'shortlisted', relation_tag: tag, reviewer_note: note.trim() })}
        >{pending ? 'Saving…' : 'Save research lead'}</button>
      </footer>
    )
  }

  return (
    <footer className="semantic-review-actions">
      <div>
        <span>REVIEW DISPOSITION</span>
        <strong>{reviseOpen ? 'Revise the recorded review.' : evidenceStatus}</strong>
      </div>
      <div className="semantic-review-buttons">
        <button type="button" className="semantic-review-primary" onClick={() => setShortlistOpen(true)} disabled={pending}>Shortlist lead</button>
        <button type="button" onClick={() => void onSubmit({ disposition: 'needs-review' })} disabled={pending}>Needs review</button>
        <button type="button" onClick={() => void onSubmit({ disposition: 'dismissed' })} disabled={pending}>Dismiss</button>
        {reviseOpen && <button type="button" onClick={() => setReviseOpen(false)} disabled={pending}>Cancel</button>}
      </div>
      {error && <p className="semantic-review-error" role="alert">{error}</p>}
    </footer>
  )
}
