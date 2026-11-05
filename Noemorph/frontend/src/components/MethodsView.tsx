import type { CatalogMetadata, ViewKey } from '../types'

const stages: Array<{ title: string; text: string; destination: ViewKey }> = [
  { title: 'Discover', text: 'Search independent disciplinary frames.', destination: 'sources' },
  { title: 'Resolve identity', text: 'Separate aliases, versions, and entities.', destination: 'catalog' },
  { title: 'Verify claims', text: 'Keep every attribution traceable.', destination: 'sources' },
  { title: 'Measure coverage', text: 'Audit screening and discovery yield.', destination: 'coverage' },
  { title: 'Synthesize', text: 'Unlock reviewed relationships after the gate.', destination: 'coverage' },
]

const principles = [
  { title: 'Entity kinds are not interchangeable', text: 'Positions, scientific theories, arguments, traditions, and frameworks retain their own kind and scope.' },
  { title: 'Authority is claim-specific', text: 'A work may be primary for its author’s definition and secondary when it reports another thinker’s position.' },
  { title: '“Complete” is not a defensible count', text: 'No fixed denominator exists; Noemorph reports protocol coverage, gaps, and discovery yield.' },
  { title: 'Resolution is not verification', text: 'A resolving DOI proves existence, not that the work supports a catalog claim.' },
  { title: 'Corrections remain reproducible', text: 'The artifact is generated from a human-readable inventory and checked for misdirected destinations.' },
  { title: 'Relationships require phase two', text: 'Conceptual graph edges remain inaccessible until breadth and review gates pass.' },
]

interface MethodsViewProps {
  metadata: CatalogMetadata
  onNavigate: (view: ViewKey) => void
}

export function MethodsView({ metadata, onNavigate }: MethodsViewProps) {
  return (
    <section className="methods-view view-frame" aria-labelledby="methods-title">
      <h1 id="methods-title" className="sr-only">Research method</h1>

      <div className="method-scroll">
        <section className="method-intro" aria-label="Methodology summary">
          <p>{metadata.methodology}</p>
        </section>

        <div className="method-flow" aria-label="Research workflow">
          {stages.map((stage) => (
            <button
              type="button"
              className="method-stage"
              key={stage.title}
              onClick={() => onNavigate(stage.destination)}
            >
              <span className="method-copy"><strong>{stage.title}</strong><small>{stage.text}</small></span>
            </button>
          ))}
        </div>

        <details className="method-principles">
          <summary><strong>Evidence rules</strong></summary>
          <div className="principle-list">
            {principles.map((principle) => (
              <article key={principle.title}>
                <div><h2>{principle.title}</h2><p>{principle.text}</p></div>
              </article>
            ))}
          </div>
        </details>
      </div>
    </section>
  )
}
