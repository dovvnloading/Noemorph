import type { Citation, TheoryRecord } from '../types'
import { ResearchProfileValue } from './ResearchProfileValue'

const authorityLabels: Record<string, string> = {
  'primary-original': 'Primary original',
  'primary-self-exposition': 'Primary self-exposition',
  'authoritative-secondary': 'Authoritative secondary',
  'scholarly-secondary': 'Scholarly secondary',
  'discovery-lead': 'Discovery lead',
}

const verificationLabels: Record<NonNullable<Citation['verification']>, string> = {
  'doi-resolved': 'DOI resolved',
  'locator-recorded': 'Locator recorded',
  'human-verified': 'Human verified',
  'pending-metadata-review': 'Pending metadata review',
}

interface AtlasInspectorProps {
  record: TheoryRecord
  onClose: () => void
  onViewCatalog: (record: TheoryRecord) => void
}

function CitationEntry({ citation }: { citation: Citation }) {
  const locator = citation.doi
    ? `DOI ${citation.doi}`
    : citation.verification
      ? verificationLabels[citation.verification]
      : undefined

  return (
    <li className="research-drawer-citation">
      <div className="research-drawer-citation-heading">
        <span>{authorityLabels[citation.authority] ?? citation.authority.replaceAll('-', ' ')}</span>
        {locator && <small>{locator}</small>}
      </div>
      <a
        className="research-drawer-citation-link"
        href={citation.url}
        target="_blank"
        rel="noreferrer"
      >
        {citation.title}
      </a>
      <p className="research-drawer-citation-byline">
        {citation.authors} · {citation.year}{citation.venue ? ` · ${citation.venue}` : ''}
      </p>
      {citation.note && <p className="research-drawer-citation-note">{citation.note}</p>}
    </li>
  )
}

export function AtlasInspector({ record, onClose, onViewCatalog }: AtlasInspectorProps) {
  const date = record.year ?? record.era ?? 'Not established'
  const hasResearchDepth = Boolean(
    record.claim_scope
    || record.boundary_note
    || record.evidence_profile?.length
    || record.open_questions?.length,
  )

  return (
    <aside className="research-drawer-shell" aria-labelledby="research-drawer-title">
      <header className="research-drawer-header">
        <div className="research-drawer-identity">
          <p className="research-drawer-kind">{record.kind}</p>
          <h2 id="research-drawer-title">{record.name}</h2>
          {record.aliases && record.aliases.length > 0 && (
            <p className="research-drawer-aliases">Also indexed as {record.aliases.join(' · ')}</p>
          )}
        </div>
        <button className="research-drawer-close" type="button" onClick={onClose} aria-label="Close record details">
          Close
        </button>
      </header>

      <div className="research-drawer-scroll-region">
        <p className="research-drawer-summary">{record.summary}</p>

        <section className="research-drawer-section" aria-labelledby="research-drawer-metadata-heading">
          <h3 id="research-drawer-metadata-heading">Catalog metadata</h3>
          <dl className="research-drawer-metadata">
            <div><dt>Record ID</dt><dd>{record.id}</dd></div>
            <div><dt>Domain</dt><dd>{record.domain}</dd></div>
            <div><dt>Tradition / locus</dt><dd>{record.tradition}</dd></div>
            <div><dt>Earliest date / era</dt><dd>{date}</dd></div>
            {record.scope && <div><dt>Scope</dt><dd>{record.scope}</dd></div>}
            {record.mechanism && <div><dt>Proposed mechanism</dt><dd>{record.mechanism}</dd></div>}
          </dl>
        </section>

        <section className="research-drawer-section" aria-labelledby="research-drawer-status-heading">
          <h3 id="research-drawer-status-heading">Research status</h3>
          <dl className="research-drawer-status">
            <div><dt>Catalog status</dt><dd>{record.status}</dd></div>
            {record.review_state && <div><dt>Review state</dt><dd>{record.review_state.replaceAll('-', ' ')}</dd></div>}
          </dl>
          {record.status_note && <p className="research-drawer-status-note">{record.status_note}</p>}
          {record.commitments && record.commitments.length > 0 && (
            <div className="research-drawer-commitments">
              <h4>Source-faithful commitments</h4>
              <ul>{record.commitments.map((commitment) => <li key={commitment}>{commitment}</li>)}</ul>
            </div>
          )}
        </section>

        {hasResearchDepth && (
          <details className="research-drawer-depth">
            <summary>Research scope and limits</summary>
            <div className="research-drawer-depth-body">
              {record.claim_scope && <div><h3>Claim scope</h3><ResearchProfileValue value={record.claim_scope} /></div>}
              {record.boundary_note && <div><h3>Boundary note</h3><p>{record.boundary_note}</p></div>}
              {record.evidence_profile && (
                <div>
                  <h3>Evidence profile</h3>
                  <ResearchProfileValue value={record.evidence_profile} />
                </div>
              )}
              {record.open_questions && record.open_questions.length > 0 && (
                <div><h3>Open questions</h3><ul>{record.open_questions.map((item) => <li key={item}>{item}</li>)}</ul></div>
              )}
            </div>
          </details>
        )}

        <section className="research-drawer-section" aria-labelledby="research-drawer-proponents-heading">
          <h3 id="research-drawer-proponents-heading">Attributed proponents</h3>
          {record.proponents.length > 0
            ? <ul className="research-drawer-proponents">{record.proponents.map((proponent) => <li key={proponent}>{proponent}</li>)}</ul>
            : <p className="research-drawer-empty">No proponent is currently attributed.</p>}
        </section>

        <section className="research-drawer-section" aria-labelledby="research-drawer-citations-heading">
          <div className="research-drawer-section-heading">
            <h3 id="research-drawer-citations-heading">Citations</h3>
            <span>{record.citations.length} {record.citations.length === 1 ? 'source' : 'sources'}</span>
          </div>
          {record.citations.length > 0
            ? <ol className="research-drawer-citations">{record.citations.map((citation, index) => <CitationEntry key={`${citation.url}-${index}`} citation={citation} />)}</ol>
            : <p className="research-drawer-empty">No citation has been retained for this record.</p>}
        </section>
      </div>

      <footer className="research-drawer-footer">
        <button type="button" onClick={() => onViewCatalog(record)}>View full catalog record</button>
      </footer>
    </aside>
  )
}
