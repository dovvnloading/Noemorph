import { openResearchSource } from '../desktop'
import type { DiscoveryEntry } from '../types'

interface DiscoveryInspectorProps {
  entry: DiscoveryEntry
  onClose: () => void
}

export function DiscoveryInspector({ entry, onClose }: DiscoveryInspectorProps) {
  const match = entry.catalog_match

  return (
    <aside className="inspector discovery-inspector" aria-label={`Source profile for ${entry.name}`}>
      <header className="inspector-top"><button type="button" onClick={onClose} aria-label="Close source profile">Close</button></header>
      <div className="record-type">{entry.entry_type} · {entry.category}</div>
      <h2>{entry.name}</h2>
      <p className="summary">{entry.description || 'No source-page description was retained.'}</p>

      <div className="inspector-actions">
        <button type="button" onClick={() => void openResearchSource(entry.url, entry.name)}>Open source profile</button>
      </div>

      <dl>
        <div><dt>Source verification</dt><dd>{entry.verified_by_source ? 'Marked verified on source page' : 'No source-page badge'}</dd></div>
        <div><dt>Title screen</dt><dd>{match.status.replaceAll('-', ' ')}</dd></div>
        {match.record_name && <div><dt>Candidate record</dt><dd>{match.record_name}</dd></div>}
        {match.record_name && <div><dt>Lexical evidence</dt><dd>{Math.round(match.score * 100)}% · {(match.basis ?? 'full-title').replaceAll('-', ' ')}</dd></div>}
        {entry.modified_at && <div><dt>Source modified</dt><dd>{new Date(entry.modified_at).toLocaleDateString()}</dd></div>}
      </dl>

      {entry.proponents.length > 0 && (
        <section className="discovery-inspector-section">
          <p className="eyebrow">PEOPLE NAMED ON PAGE</p>
          <ul>{entry.proponents.map((person, index) => <li key={`${person.name}-${index}`}><strong>{person.name}</strong>{person.role && <span>{person.role}</span>}</li>)}</ul>
        </section>
      )}

      {entry.key_takeaways.length > 0 && (
        <section className="discovery-inspector-section">
          <p className="eyebrow">SOURCE-PAGE CLAIMS</p>
          <dl className="discovery-takeaways">{entry.key_takeaways.map((item, index) => <div key={`${item.label}-${index}`}><dt>{item.label.trim()}</dt><dd>{item.text}</dd></div>)}</dl>
        </section>
      )}

      <section className="inspector-citations discovery-references">
        <div className="section-heading"><p className="eyebrow">RETAINED PAGE REFERENCES</p><span>{entry.references.length}</span></div>
        {entry.references.length === 0 && <p className="discovery-reference-empty">No reference was exposed on this source page.</p>}
        {entry.references.map((reference, index) => (
          <article className="citation-card" key={`${reference.title}-${index}`}>
            <p>{reference.authors ? `${reference.authors}. ` : ''}<i>{reference.title || reference.label}</i>{reference.container ? `. ${reference.container}` : ''}</p>
            {reference.locators.length > 0 && (
              <footer><span>{reference.locators.length} locator{reference.locators.length === 1 ? '' : 's'}</span><button type="button" onClick={() => void openResearchSource(reference.locators[0], reference.title || reference.label)}>Open</button></footer>
            )}
          </article>
        ))}
      </section>
    </aside>
  )
}
