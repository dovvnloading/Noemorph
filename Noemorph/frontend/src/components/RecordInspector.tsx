import { openResearchSource } from '../desktop'
import type { TheoryRecord } from '../types'
import { ResearchProfileValue } from './ResearchProfileValue'
import { ClaimEvidenceHistory } from './ClaimEvidenceHistory'

const authorityLabels: Record<string, string> = {
  'primary-original': 'Primary original',
  'primary-self-exposition': 'Primary self-exposition',
  'authoritative-secondary': 'Authoritative secondary',
  'scholarly-secondary': 'Scholarly secondary',
  'discovery-lead': 'Discovery lead',
}

interface RecordInspectorProps {
  record?: TheoryRecord
  onClose?: () => void
  mobileOpen?: boolean
  currentView: 'atlas' | 'catalog'
  onLocateInAtlas: (record: TheoryRecord) => void
  onViewInCatalog: (record: TheoryRecord) => void
}

export function RecordInspector({ record, onClose, mobileOpen, currentView, onLocateInAtlas, onViewInCatalog }: RecordInspectorProps) {
  if (!record) {
    return <aside className="inspector glass-panel"><div className="inspector-empty"><span>NO RECORD</span><p>Select a catalog record to inspect its source trail.</p></div></aside>
  }

  const hasResearchDepth = Boolean(
    record.claim_scope
    || record.boundary_note
    || record.evidence_profile?.length
    || record.open_questions?.length,
  )

  return (
    <aside className={`inspector glass-panel ${mobileOpen ? 'mobile-open' : ''}`} aria-label={`Details for ${record.name}`}>
      {onClose && <header className="inspector-top"><button onClick={onClose} aria-label="Close details">Close</button></header>}
      <div className="record-type">{record.kind}</div>
      <h2>{record.name}</h2>
      {record.aliases && record.aliases.length > 0 && <p className="aliases">Also: {record.aliases.join(' · ')}</p>}
      <p className="summary">{record.summary}</p>

      <div className="inspector-actions">
        {currentView === 'catalog'
          ? <button type="button" onClick={() => onLocateInAtlas(record)}>Locate in Atlas</button>
          : <button type="button" onClick={() => onViewInCatalog(record)}>View in Catalog</button>}
      </div>

      <dl>
        <div><dt>Attributed proponents</dt><dd>{record.proponents.join(', ')}</dd></div>
        <div><dt>Domain</dt><dd>{record.domain}</dd></div>
        <div><dt>Tradition / locus</dt><dd>{record.tradition}</dd></div>
        <div><dt>Earliest date / era</dt><dd>{record.year ?? record.era ?? 'See sources'}</dd></div>
        <div><dt>Catalog status</dt><dd><span className="status-pill">{record.status}</span></dd></div>
      </dl>

      {record.status_note && <div className="status-note"><span>{record.status_note}</span></div>}
      {record.commitments && record.commitments.length > 0 && <section className="commitments"><p className="eyebrow">SOURCE-FAITHFUL COMMITMENTS</p><ul>{record.commitments.map((commitment) => <li key={commitment}>{commitment}</li>)}</ul></section>}
      {hasResearchDepth && (
        <details className="record-depth">
          <summary>Research scope and limits</summary>
          <div>
            {record.claim_scope && <section><strong>Claim scope</strong><ResearchProfileValue value={record.claim_scope} /></section>}
            {record.boundary_note && <section><strong>Boundary note</strong><p>{record.boundary_note}</p></section>}
            {record.evidence_profile && (
              <section>
                <strong>Evidence profile</strong>
                <ResearchProfileValue value={record.evidence_profile} />
              </section>
            )}
            {record.open_questions && record.open_questions.length > 0 && <section><strong>Open questions</strong><ul>{record.open_questions.map((item) => <li key={item}>{item}</li>)}</ul></section>}
          </div>
        </details>
      )}

      {record.claim_reviews && record.claim_reviews.length > 0 && (
        <section className="commitments" aria-label="Claim-level source review leads">
          <p className="eyebrow">CLAIM REVIEW LEADS · UNVERIFIED</p>
          <p>These are retained source URLs nominated for passage-level review. No claim-to-source support or refutation has been verified by these links.</p>
          <ol>
            {record.claim_reviews.map((claim) => (
              <li key={claim.id}>
                <strong>{claim.kind === 'scope' ? 'Theory statement' : 'Boundary or limitation'}</strong>
                <p>{claim.text}</p>
                <ul>
                  {claim.citations.map((lead) => {
                    const cited = record.citations.find((citation) => citation.url === lead.citation_url)
                    return (
                      <li key={lead.source_uid}>
                        <button type="button" onClick={() => void openResearchSource(lead.citation_url, cited?.title ?? 'Review lead')}>
                          Open candidate source: {cited?.title ?? lead.citation_url}
                        </button>
                        <small> · Source URL only · Claim match unreviewed · Citation metadata: {cited?.verification ?? 'pending'}</small>
                      </li>
                    )
                  })}
                </ul>
                <ClaimEvidenceHistory recordId={record.id} claimId={claim.id} />
              </li>
            ))}
          </ol>
        </section>
      )}

      <section className="inspector-citations">
        <div className="section-heading"><p className="eyebrow">CITATION TRAIL</p><span>{record.citations.length} work{record.citations.length === 1 ? '' : 's'}</span></div>
        {record.citations.map((citation, index) => (
          <article className="citation-card" key={`${citation.url}-${index}`}>
            <div><span>{authorityLabels[citation.authority] ?? citation.authority}</span></div>
            <p>{citation.authors} ({citation.year}). <i>{citation.title}</i>{citation.venue ? `. ${citation.venue}` : ''}</p>
            <footer><span>{citation.doi ? `DOI ${citation.doi}` : citation.verification?.replace('-', ' ')}</span><button type="button" onClick={() => void openResearchSource(citation.url, citation.title)} aria-label={`Open source: ${citation.title}`}>Open</button></footer>
          </article>
        ))}
      </section>
    </aside>
  )
}
