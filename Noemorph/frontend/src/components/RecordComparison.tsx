import type { Citation, ResearchProfileValue as ProfileValue, TheoryRecord } from '../types'
import { ResearchProfileValue } from './ResearchProfileValue'
import { publicComparisonUrl } from './recordComparison'

function FieldValue({ value }: { value?: ProfileValue }) {
  return value ? <ResearchProfileValue value={value} /> : <span className="comparison-unavailable">Not profiled</span>
}

function Citations({ citations }: { citations: Citation[] }) {
  return (
    <ul className="comparison-citations">
      {citations.map((citation) => (
        <li key={citation.source_uid ?? citation.url}>
          <a href={citation.url} target="_blank" rel="noopener noreferrer">{citation.title}</a>
          <small>{citation.authors} · {citation.authority.replaceAll('-', ' ')} · Citation status: {(citation.verification ?? 'pending-metadata-review').replaceAll('-', ' ')}</small>
        </li>
      ))}
    </ul>
  )
}

export function RecordComparison({ left, right, onClear }: {
  left: TheoryRecord
  right: TheoryRecord
  onClear: () => void
}) {
  const publicUrl = publicComparisonUrl([left.id, right.id])
  return (
    <section className="record-comparison" aria-labelledby="compare-title">
      <div className="comparison-heading">
        <div>
          <h2 id="compare-title" tabIndex={-1}>Read-only record comparison</h2>
          <p>Two catalog entries shown side by side. Similar wording, shared sources, and different labels are <strong>not</strong> evidence of convergence, disagreement, causal links, or theory equivalence. All claims retain their independent review status.</p>
        </div>
        <div className="comparison-actions">
          {publicUrl && <a href={publicUrl} target="_blank" rel="noopener noreferrer">Open shareable public comparison</a>}
          <button type="button" onClick={onClear}>Clear comparison</button>
        </div>
      </div>
      <div className="comparison-table-scroll" role="region" aria-label="Side-by-side record details" tabIndex={0}>
        <table className="comparison-table">
          <caption className="sr-only">Read-only comparison of two catalog entries, without inferred relationships</caption>
          <thead>
            <tr>
              <th scope="col">Research dimension</th>
              <th scope="col">{left.name}</th>
              <th scope="col">{right.name}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">Classification</th>
              <td>{left.kind}<small>{left.domain} · {left.tradition}</small></td>
              <td>{right.kind}<small>{right.domain} · {right.tradition}</small></td>
            </tr>
            <tr>
              <th scope="row">Current catalog status</th>
              <td>{left.status}<small>Record review: {left.review_state ?? 'unspecified'}</small></td>
              <td>{right.status}<small>Record review: {right.review_state ?? 'unspecified'}</small></td>
            </tr>
            <tr>
              <th scope="row">Overview</th>
              <td>{left.summary}</td>
              <td>{right.summary}</td>
            </tr>
            <tr>
              <th scope="row">Claim scope</th>
              <td><FieldValue value={left.claim_scope ?? left.scope} /></td>
              <td><FieldValue value={right.claim_scope ?? right.scope} /></td>
            </tr>
            <tr>
              <th scope="row">Boundaries</th>
              <td>{left.boundary_note ?? left.status_note ?? <span className="comparison-unavailable">Not profiled</span>}</td>
              <td>{right.boundary_note ?? right.status_note ?? <span className="comparison-unavailable">Not profiled</span>}</td>
            </tr>
            <tr>
              <th scope="row">Evidence profile</th>
              <td><FieldValue value={left.evidence_profile} /></td>
              <td><FieldValue value={right.evidence_profile} /></td>
            </tr>
            <tr>
              <th scope="row">Open questions</th>
              <td><FieldValue value={left.open_questions} /></td>
              <td><FieldValue value={right.open_questions} /></td>
            </tr>
            <tr>
              <th scope="row">Retained citations</th>
              <td><Citations citations={left.citations} /></td>
              <td><Citations citations={right.citations} /></td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="comparison-footer-note">A citation URL, DOI resolution, or bibliographic verification does not independently verify a claim. Unreviewed claim-level source leads and private local reviewer notes are not promoted by comparison.</p>
    </section>
  )
}
