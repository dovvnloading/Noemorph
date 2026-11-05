import { openResearchSource } from '../../desktop'
import type {
  SemanticCandidateDetail,
  SemanticReviewUpdate,
  TheoryRecord,
} from '../../types'
import { ResearchProfileValue } from '../ResearchProfileValue'
import { SemanticReviewForm } from './SemanticReviewForm'

interface SemanticPairComparisonProps {
  candidate?: SemanticCandidateDetail
  records: TheoryRecord[]
  loading: boolean
  error?: string
  reviewPending: boolean
  reviewError?: string
  onRetry: () => void
  onOpenRecord: (record: TheoryRecord) => void
  onReview: (review: SemanticReviewUpdate) => Promise<void>
  onBack: () => void
}

function percentage(value?: number, decimals = 0): string {
  if (value === undefined || !Number.isFinite(value)) return 'Not available'
  const normalized = value <= 1 ? value * 100 : value
  return `${normalized.toFixed(decimals)}%`
}

function fieldLabel(value: string): string {
  return value.replaceAll('_', ' ').replaceAll('-', ' ')
}

function RecordColumn({ reference, record, onOpen }: {
  reference: SemanticCandidateDetail['record_a']
  record?: TheoryRecord
  onOpen: (record: TheoryRecord) => void
}) {
  return (
    <article className="semantic-record-column">
      <span>{record?.kind ?? reference.kind ?? 'Catalog record'}</span>
      <h2>{record?.name ?? reference.name}</h2>
      <p>{record?.domain ?? reference.domain ?? 'Domain not recorded'}</p>
      {record && <button type="button" onClick={() => onOpen(record)}>Open catalog record</button>}
    </article>
  )
}

function TextPair({ heading, left, right }: { heading: string; left?: string; right?: string }) {
  if (!left && !right) return null
  return (
    <section className="semantic-pair-section">
      <h3>{heading}</h3>
      <div className="semantic-pair-columns">
        <p>{left || 'Not recorded.'}</p>
        <p>{right || 'Not recorded.'}</p>
      </div>
    </section>
  )
}

function ProfilePair({ heading, left, right }: {
  heading: string
  left?: TheoryRecord['claim_scope']
  right?: TheoryRecord['claim_scope']
}) {
  if (!left && !right) return null
  return (
    <section className="semantic-pair-section">
      <h3>{heading}</h3>
      <div className="semantic-pair-columns semantic-profile-pair">
        <div>{left ? <ResearchProfileValue value={left} /> : <p>Not recorded.</p>}</div>
        <div>{right ? <ResearchProfileValue value={right} /> : <p>Not recorded.</p>}</div>
      </div>
    </section>
  )
}

function CitationColumn({ record }: { record?: TheoryRecord }) {
  if (!record) return <p>Catalog record unavailable.</p>
  return (
    <ol>
      {record.citations.slice(0, 3).map((citation, index) => (
        <li key={`${citation.url}-${index}`}>
          <button type="button" onClick={() => void openResearchSource(citation.url, citation.title)}>{citation.title}</button>
          <small>{citation.authors} · {citation.year}</small>
        </li>
      ))}
      {record.citations.length > 3 && <li className="semantic-citation-remainder">+{record.citations.length - 3} additional works in the catalog record</li>}
    </ol>
  )
}

export function SemanticPairComparison({
  candidate,
  records,
  loading,
  error,
  reviewPending,
  reviewError,
  onRetry,
  onOpenRecord,
  onReview,
  onBack,
}: SemanticPairComparisonProps) {
  if (loading) {
    return (
      <section className="semantic-comparison semantic-comparison-state" aria-live="polite">
        <strong>Loading evidence comparison</strong>
        <p>Retrieving the selected pair and its embedding provenance.</p>
      </section>
    )
  }

  if (error) {
    return (
      <section className="semantic-comparison semantic-comparison-state" role="alert">
        <strong>Candidate detail unavailable</strong>
        <p>{error}</p>
        <button type="button" onClick={onRetry}>Retry</button>
      </section>
    )
  }

  if (!candidate) {
    return (
      <section className="semantic-comparison semantic-comparison-state">
        <strong>Select a candidate relationship</strong>
        <p>Choose one pair from the review queue to compare its claims, evidence, and source trail.</p>
      </section>
    )
  }

  const recordA = records.find((record) => record.id === candidate.record_a.id)
  const recordB = records.find((record) => record.id === candidate.record_b.id)
  const sourceOverlap = candidate.source_overlap_count ?? 0
  const contributions = (candidate.field_contributions ?? []).slice(0, 6)
  const taxonomicSeparation = candidate.cross_domain && candidate.cross_tradition
    ? 'Cross-domain and tradition'
    : candidate.cross_domain
      ? 'Cross-domain'
      : candidate.cross_tradition
        ? 'Cross-tradition'
        : 'Within current classification'

  return (
    <section className="semantic-comparison" aria-label={`Evidence comparison for ${candidate.record_a.name} and ${candidate.record_b.name}`}>
      <header className="semantic-comparison-header">
        <button type="button" className="semantic-mobile-back" onClick={onBack}>Back to queue</button>
        <div>
          <span>EMBEDDING CANDIDATE · {(candidate.disposition ?? 'unreviewed').replaceAll('-', ' ')}</span>
          <strong>Relationship evidence</strong>
        </div>
        <p>{candidate.interpretation_policy ?? 'Semantic proximity is a review signal, not an established relationship.'}</p>
      </header>

      <div className="semantic-comparison-scroll">
        <div className="semantic-record-pair">
          <RecordColumn reference={candidate.record_a} record={recordA} onOpen={onOpenRecord} />
          <RecordColumn reference={candidate.record_b} record={recordB} onOpen={onOpenRecord} />
        </div>

        <section className="semantic-signal-summary" aria-labelledby="semantic-signal-heading">
          <h3 id="semantic-signal-heading">Why this pair surfaced</h3>
          <dl>
            <div><dt>Semantic similarity</dt><dd>{percentage(candidate.semantic_similarity, 1)}</dd></div>
            <div><dt>Corpus percentile</dt><dd>{percentage(candidate.similarity_percentile, 1)}</dd></div>
            <div><dt>Taxonomic separation</dt><dd>{taxonomicSeparation}</dd></div>
            <div><dt>Shared cited sources</dt><dd>{sourceOverlap}</dd></div>
          </dl>
          {candidate.proponent_overlap_count !== undefined && candidate.proponent_overlap_count > 0 && (
            <p>{candidate.proponent_overlap_count} attributed proponent{candidate.proponent_overlap_count === 1 ? '' : 's'} occur in both records; interpret the similarity with caution.</p>
          )}
        </section>

        <TextPair heading="Catalog summaries" left={recordA?.summary ?? candidate.record_a.summary} right={recordB?.summary ?? candidate.record_b.summary} />
        <ProfilePair heading="Claim scope" left={recordA?.claim_scope} right={recordB?.claim_scope} />
        <TextPair heading="Proposed mechanism" left={recordA?.mechanism} right={recordB?.mechanism} />

        {(recordA?.evidence_profile || recordB?.evidence_profile || recordA?.boundary_note || recordB?.boundary_note) && (
          <details className="semantic-supporting-detail">
            <summary>Evidence profiles and limits</summary>
            <ProfilePair heading="Evidence profile" left={recordA?.evidence_profile} right={recordB?.evidence_profile} />
            <TextPair heading="Boundary notes" left={recordA?.boundary_note} right={recordB?.boundary_note} />
          </details>
        )}

        <section className="semantic-textual-basis">
          <div className="semantic-section-heading">
            <h3>Representative view inputs</h3>
            <span>{contributions.length} retained signal{contributions.length === 1 ? '' : 's'}</span>
          </div>
          {contributions.length > 0 && (
            <p className="semantic-attribution-note">
              Scores apply to each complete semantic view. These excerpts are representative inputs, not token-level explanations or evidence for a relationship.
            </p>
          )}
          {contributions.length === 0 ? (
            <p className="semantic-detail-empty">No section-level contribution was retained for this candidate.</p>
          ) : contributions.map((contribution, index) => (
            <article key={`${contribution.field_a}-${contribution.field_b}-${index}`}>
              <header>
                <span>{contribution.signal ? `${fieldLabel(contribution.signal)} · ` : ''}{fieldLabel(contribution.field_a)} / {fieldLabel(contribution.field_b)}</span>
                <b>{percentage(contribution.score, 1)}</b>
              </header>
              <div className="semantic-pair-columns">
                <blockquote>{contribution.excerpt_a}</blockquote>
                <blockquote>{contribution.excerpt_b}</blockquote>
              </div>
            </article>
          ))}
        </section>

        {candidate.prior_art && (
          <section className="semantic-prior-art" aria-labelledby="semantic-prior-art-heading">
            <div className="semantic-section-heading">
              <h3 id="semantic-prior-art-heading">Focused prior-art screen</h3>
              <span>{fieldLabel(candidate.prior_art.status)}</span>
            </div>
            <div className="semantic-prior-art-findings">
              <p><strong>Direct comparison</strong>{candidate.prior_art.direct_comparison}</p>
              <p><strong>Assessment</strong>{candidate.prior_art.assessment}</p>
              <p><strong>Boundary</strong>{candidate.prior_art.caution}</p>
            </div>
            <ol>
              {candidate.prior_art.sources.map((source) => (
                <li key={source.url}>
                  <button type="button" onClick={() => void openResearchSource(source.url, source.title)}>{source.title}</button>
                  <small>{source.authors} · {source.year}</small>
                  <p>{source.role}</p>
                </li>
              ))}
            </ol>
            <p className="semantic-prior-art-limit">Focused search only. A missing direct hit is not evidence that a connection is novel.</p>
          </section>
        )}

        <details className="semantic-citations">
          <summary>Citation anchors</summary>
          <div className="semantic-pair-columns">
            <CitationColumn record={recordA} />
            <CitationColumn record={recordB} />
          </div>
        </details>

        <details className="semantic-provenance">
          <summary>Embedding provenance</summary>
          <dl>
            <div><dt>Model</dt><dd>{candidate.run ? `${candidate.run.model.provider} · ${candidate.run.model.name} · ${candidate.run.model.dimensions} dimensions` : 'Not recorded'}</dd></div>
            <div><dt>Model digest</dt><dd>{candidate.run?.model.digest ?? 'Not recorded'}</dd></div>
            <div><dt>Metric</dt><dd>{candidate.run?.recipe.metric ?? 'cosine similarity'}</dd></div>
            <div><dt>Catalog version</dt><dd>{candidate.run?.catalog_version ?? 'Not recorded'}</dd></div>
            <div><dt>Corpus hash</dt><dd>{candidate.run?.catalog_hash ?? 'Not recorded'}</dd></div>
            <div><dt>Run</dt><dd>{candidate.run?.id ?? 'Not recorded'}{candidate.run?.created_at ? ` · ${new Date(candidate.run.created_at).toLocaleString()}` : ''}</dd></div>
          </dl>
        </details>
      </div>

      <SemanticReviewForm candidate={candidate} pending={reviewPending} error={reviewError} onSubmit={onReview} />
    </section>
  )
}
