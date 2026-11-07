import { useMemo, useState } from 'react'
import type { DiscoveryEntry, TheoryRecord } from '../types'
import { recordMatches } from './atlasModel'
import { RecordComparison } from './RecordComparison'

const DISCOVERY_MATCH_LABELS: Record<DiscoveryEntry['catalog_match']['status'], string> = {
  'likely-present': 'Strong title candidate',
  'possible-match': 'Review candidate',
  'not-matched': 'No title candidate',
  'not-applicable': 'Not applicable',
}

interface CatalogViewProps {
  records: TheoryRecord[]
  discovery: DiscoveryEntry[]
  discoveryState: 'idle' | 'loading' | 'ready' | 'error'
  discoveryError: string | null
  onRetryDiscovery: () => void
  selectedDiscoverySlug?: string
  onSelectDiscovery: (entry: DiscoveryEntry) => void
  selectedId?: string
  onSelect: (record: TheoryRecord) => void
  comparisonIds: string[]
  onToggleComparison: (recordId: string) => void
  onClearComparison: () => void
  query: string
  selectedKind: string
  onKindChange: (kind: string) => void
  scope: 'catalog' | 'discovery'
  onScopeChange: (scope: 'catalog' | 'discovery') => void
}

export function CatalogView({
  records,
  discovery,
  discoveryState,
  discoveryError,
  onRetryDiscovery,
  selectedDiscoverySlug,
  onSelectDiscovery,
  selectedId,
  onSelect,
  comparisonIds,
  onToggleComparison,
  onClearComparison,
  query,
  selectedKind,
  onKindChange,
  scope,
  onScopeChange,
}: CatalogViewProps) {
  const [sortKey, setSortKey] = useState<'name' | 'kind' | 'domain' | 'proponents' | 'sources'>('name')
  const [sortDirection, setSortDirection] = useState<1 | -1>(1)
  const [selectedDiscoveryCategory, setSelectedDiscoveryCategory] = useState('All categories')
  const comparisonRecords = comparisonIds.map((id) => records.find((record) => record.id === id))
  const canCompare = comparisonRecords.length === 2 && comparisonRecords.every((item): item is TheoryRecord => Boolean(item))
  const kinds = [...new Set(records.map((record) => record.kind))].sort()
  const discoveryCategories = [...new Set(discovery.map((entry) => entry.category))].sort()
  // Catalog and atlas now apply the same identity, taxonomy and research-field search.
  const filtered = records.filter((record) => (
    (selectedKind === 'All records' || record.kind === selectedKind)
    && recordMatches(record, query)
  ))
  const sorted = useMemo(() => [...filtered].sort((left, right) => {
    const values: Record<typeof sortKey, [string | number, string | number]> = {
      name: [left.name, right.name],
      kind: [left.kind, right.kind],
      domain: [left.domain, right.domain],
      proponents: [left.proponents.join(', '), right.proponents.join(', ')],
      sources: [left.citations.length, right.citations.length],
    }
    const [leftValue, rightValue] = values[sortKey]
    return sortDirection * (typeof leftValue === 'number' && typeof rightValue === 'number'
      ? leftValue - rightValue
      : String(leftValue).localeCompare(String(rightValue)))
  }), [filtered, sortDirection, sortKey])

  const discoveryHaystack = (entry: DiscoveryEntry) => [
    entry.name,
    entry.description,
    entry.category,
    ...entry.proponents.flatMap((proponent) => [proponent.name, proponent.role]),
  ].join(' ').toLocaleLowerCase()
  const normalizedDiscoveryQuery = query.trim().toLocaleLowerCase()
  const discoveryPhraseMatchExists = normalizedDiscoveryQuery.includes(' ') && discovery.some((entry) => (
    (selectedDiscoveryCategory === 'All categories' || entry.category === selectedDiscoveryCategory)
    && discoveryHaystack(entry).includes(normalizedDiscoveryQuery)
  ))
  const filteredDiscovery = discovery.filter((entry) => {
    if (selectedDiscoveryCategory !== 'All categories' && entry.category !== selectedDiscoveryCategory) return false
    if (!normalizedDiscoveryQuery) return true
    const haystack = discoveryHaystack(entry)
    if (discoveryPhraseMatchExists) return haystack.includes(normalizedDiscoveryQuery)
    return normalizedDiscoveryQuery.split(/\s+/).every((term) => haystack.includes(term))
  })
  const sortedDiscovery = useMemo(() => [...filteredDiscovery].sort((left, right) => {
    const values: Record<typeof sortKey, [string | number, string | number]> = {
      name: [left.name, right.name],
      kind: [left.category, right.category],
      domain: [left.catalog_match.status, right.catalog_match.status],
      proponents: [left.proponents.map((item) => item.name).join(', '), right.proponents.map((item) => item.name).join(', ')],
      sources: [left.references.length, right.references.length],
    }
    const [leftValue, rightValue] = values[sortKey]
    return sortDirection * (typeof leftValue === 'number' && typeof rightValue === 'number'
      ? leftValue - rightValue
      : String(leftValue).localeCompare(String(rightValue)))
  }), [filteredDiscovery, sortDirection, sortKey])

  const sortBy = (nextKey: typeof sortKey) => {
    if (nextKey === sortKey) setSortDirection((current) => current === 1 ? -1 : 1)
    else {
      setSortKey(nextKey)
      setSortDirection(1)
    }
  }

  return (
    <section className="catalog-view view-frame" aria-labelledby="catalog-title">
      <h1 id="catalog-title" className="sr-only">Record catalog</h1>
      <header className="context-bar" aria-label="Catalog controls">
        <div className="context-title">
          <span>{scope === 'catalog'
            ? <><strong>{filtered.length}</strong> of {records.length} reviewed records</>
            : <><strong>{filteredDiscovery.length}</strong> of {discovery.length} source-page entries</>
          }</span>
        </div>
        <div className="catalog-control-group">
          <div className="context-controls select-wrap">
            <label htmlFor="catalog-scope">Collection</label>
            <select id="catalog-scope" aria-label="Collection" value={scope} onChange={(event) => onScopeChange(event.target.value as 'catalog' | 'discovery')}>
              <option value="catalog">Reviewed catalog</option>
              <option value="discovery">Discovery screening</option>
            </select>
          </div>
          {scope === 'catalog' ? (
            <div className="context-controls select-wrap">
              <label htmlFor="kind-filter">Record type</label>
              <select id="kind-filter" aria-label="Record type" value={selectedKind} onChange={(event) => onKindChange(event.target.value)}>
                <option>All records</option>
                {kinds.map((kind) => <option key={kind}>{kind}</option>)}
              </select>
            </div>
          ) : (
            <div className="context-controls select-wrap">
              <label htmlFor="discovery-category">Source category</label>
              <select id="discovery-category" aria-label="Source category" value={selectedDiscoveryCategory} onChange={(event) => setSelectedDiscoveryCategory(event.target.value)}>
                <option>All categories</option>
                {discoveryCategories.map((category) => <option key={category}>{category}</option>)}
              </select>
            </div>
          )}
        </div>
      </header>

      {scope === 'catalog' && (
        <div className="comparison-selection" aria-label="Choose two records for read-only comparison">
          <p aria-live="polite"><strong>{comparisonIds.length} of 2 selected</strong> · Choose two records to view their research fields side by side. Selecting them does not assert a relationship.</p>
          {comparisonIds.length > 0 && (
            <div className="comparison-selection-actions">
              <span>{comparisonIds.map((id) => records.find((record) => record.id === id)?.name ?? 'Unknown record').join(' / ')}</span>
              <button type="button" onClick={onClearComparison}>Clear selections</button>
            </div>
          )}
        </div>
      )}
      {scope === 'catalog' && canCompare && (
        <RecordComparison left={comparisonRecords[0]!} right={comparisonRecords[1]!} onClear={onClearComparison} />
      )}

      {scope === 'discovery' && (discoveryState === 'idle' || discoveryState === 'loading') ? (
        <div className="empty-state"><h2>Loading source registry</h2><p>Retrieving the discovery screen only; reviewed records remain available.</p></div>
      ) : scope === 'discovery' && discoveryState === 'error' ? (
        <div className="empty-state">
          <h2>Source registry unavailable</h2>
          <p>{discoveryError || 'The discovery registry could not be reached.'}</p>
          <button type="button" className="soft-button" onClick={onRetryDiscovery}>Retry</button>
        </div>
      ) : (scope === 'catalog' ? filtered.length : filteredDiscovery.length) === 0 ? (
        <div className="empty-state">
          <h2>No matching {scope === 'catalog' ? 'records' : 'source entries'}</h2>
          <p>Try a broader search or {scope === 'catalog' ? 'record type' : 'source category'}.</p>
        </div>
      ) : scope === 'catalog' ? (
        <div className="catalog-table-wrap">
          <table className="catalog-table">
            <thead>
              <tr>
                <th><button onClick={() => sortBy('name')}>Name {sortKey === 'name' ? (sortDirection === 1 ? '↑' : '↓') : ''}</button></th>
                <th><button onClick={() => sortBy('kind')}>Type {sortKey === 'kind' ? (sortDirection === 1 ? '↑' : '↓') : ''}</button></th>
                <th><button onClick={() => sortBy('domain')}>Domain {sortKey === 'domain' ? (sortDirection === 1 ? '↑' : '↓') : ''}</button></th>
                <th><button onClick={() => sortBy('proponents')}>Attributed proponents {sortKey === 'proponents' ? (sortDirection === 1 ? '↑' : '↓') : ''}</button></th>
                <th><button onClick={() => sortBy('sources')}>Sources {sortKey === 'sources' ? (sortDirection === 1 ? '↑' : '↓') : ''}</button></th><th />
              </tr>
            </thead>
            <tbody>
              {sorted.map((record) => (
                <tr
                  key={record.id}
                  className={record.id === selectedId ? 'selected' : ''}
                >
                  <td><strong>{record.name}</strong><small>{record.summary}</small></td>
                  <td><span className="kind-pill">{record.kind}</span></td>
                  <td>{record.domain}</td>
                  <td>{record.proponents.slice(0, 2).join(', ')}{record.proponents.length > 2 ? ' et al.' : ''}</td>
                  <td><span className="source-count">{record.citations.length}<small> works</small></span></td>
                  <td>
                    <div className="catalog-record-actions">
                      <button type="button" onClick={() => onSelect(record)} aria-label={`Inspect ${record.name}`}>Open</button>
                      <button
                        type="button"
                        aria-pressed={comparisonIds.includes(record.id)}
                        aria-label={`${comparisonIds.includes(record.id) ? 'Remove' : 'Add'} ${record.name} ${comparisonIds.includes(record.id) ? 'from' : 'to'} comparison`}
                        disabled={comparisonIds.length === 2 && !comparisonIds.includes(record.id)}
                        onClick={() => onToggleComparison(record.id)}
                      >
                        {comparisonIds.includes(record.id) ? 'Selected' : 'Compare'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="catalog-table-wrap">
          <table className="catalog-table discovery-table">
            <caption className="sr-only">Unreviewed Closer to Truth source-page entries. Title screening is automated and does not establish record identity.</caption>
            <thead>
              <tr>
                <th><button onClick={() => sortBy('name')}>Name {sortKey === 'name' ? (sortDirection === 1 ? '↑' : '↓') : ''}</button></th>
                <th><button onClick={() => sortBy('kind')}>Category {sortKey === 'kind' ? (sortDirection === 1 ? '↑' : '↓') : ''}</button></th>
                <th><button onClick={() => sortBy('domain')}>Title screen {sortKey === 'domain' ? (sortDirection === 1 ? '↑' : '↓') : ''}</button></th>
                <th><button onClick={() => sortBy('proponents')}>People named on page {sortKey === 'proponents' ? (sortDirection === 1 ? '↑' : '↓') : ''}</button></th>
                <th><button onClick={() => sortBy('sources')}>Page refs {sortKey === 'sources' ? (sortDirection === 1 ? '↑' : '↓') : ''}</button></th><th />
              </tr>
            </thead>
            <tbody>
              {sortedDiscovery.map((entry) => (
                <tr key={entry.slug} className={entry.slug === selectedDiscoverySlug ? 'selected' : ''}>
                  <td>
                    <strong>{entry.name}</strong>
                    <small><span className="discovery-entry-type">{entry.entry_type}</span>{entry.description || 'Description pending source-page review.'}</small>
                  </td>
                  <td><span className="kind-pill">{entry.category}</span></td>
                  <td>
                    <span
                      className={`discovery-match ${entry.catalog_match.status}`}
                      title="Automated lexical title screen; not a record-identity decision."
                    >{DISCOVERY_MATCH_LABELS[entry.catalog_match.status]}</span>
                  </td>
                  <td>{entry.proponents.slice(0, 2).map((item) => item.name).join(', ') || 'No people listed'}{entry.proponents.length > 2 ? ' et al.' : ''}</td>
                  <td><span className="source-count">{entry.references.length}<small> listed</small></span></td>
                  <td><button className="source-frame-link" type="button" onClick={() => onSelectDiscovery(entry)} aria-label={`Inspect source profile for ${entry.name}`}>Open</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
