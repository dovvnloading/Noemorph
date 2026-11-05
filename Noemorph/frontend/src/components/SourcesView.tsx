import { useMemo, useState } from 'react'
import { openResearchSource } from '../desktop'
import type { SourceRecord, TheoryRecord } from '../types'

interface SourcesViewProps {
  sources: SourceRecord[]
  records: TheoryRecord[]
  query: string
  onInspectRecord: (record: TheoryRecord) => void
}

const authorityLabels: Record<string, string> = {
  'primary-original': 'Primary · original',
  'primary-self-exposition': 'Primary · self-exposition',
  'authoritative-secondary': 'Authoritative secondary',
  'scholarly-secondary': 'Scholarly secondary',
  'discovery-lead': 'Discovery lead',
}

export function SourcesView({ sources, records, query, onInspectRecord }: SourcesViewProps) {
  const [authority, setAuthority] = useState('All authority roles')
  const recordById = useMemo(
    () => Object.fromEntries(records.map((record) => [record.id, record])),
    [records],
  )
  const authorityRoles = useMemo(
    () => [...new Set(sources.map((source) => source.authority))].sort(),
    [sources],
  )
  const filtered = sources.filter((source) => {
    if (authority !== 'All authority roles' && source.authority !== authority) return false
    if (!query.trim()) return true
    const usedByNames = source.used_by.map((id) => recordById[id]?.name ?? id).join(' ')
    const haystack = `${source.title} ${source.authors} ${source.venue ?? ''} ${source.doi ?? ''} ${usedByNames}`.toLocaleLowerCase()
    return query.toLocaleLowerCase().split(/\s+/).every((term) => haystack.includes(term))
  })

  return (
    <section className="sources-view view-frame" aria-labelledby="sources-title">
      <h1 id="sources-title" className="sr-only">Source register</h1>
      <header className="context-bar" aria-label="Source controls">
        <div className="context-title">
          <span><strong>{filtered.length}</strong> of {sources.length} works</span>
        </div>
        <div className="context-controls">
          <label htmlFor="authority-filter">Authority role</label>
          <select id="authority-filter" value={authority} onChange={(event) => setAuthority(event.target.value)}>
            <option>All authority roles</option>
            {authorityRoles.map((role) => <option value={role} key={role}>{authorityLabels[role] ?? role}</option>)}
          </select>
        </div>
      </header>

      {filtered.length === 0 ? (
        <div className="empty-state"><h2>No matching sources</h2><p>Search by title, author, venue, DOI, or supported record.</p></div>
      ) : (
        <div className="source-table-wrap">
          <table className="source-table">
            <thead>
              <tr>
                <th>Work</th>
                <th>Year</th>
                <th>Authority role</th>
                <th>Supports</th>
                <th>Identifier</th>
                <th><span className="sr-only">Open</span></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((source) => (
                <tr key={source.id}>
                  <td>
                    <strong>{source.title}</strong>
                    <small>{source.authors}{source.venue ? ` · ${source.venue}` : ''}</small>
                  </td>
                  <td className="source-year">{source.year}</td>
                  <td><span className={`authority-tag authority-${source.authority}`}>{authorityLabels[source.authority] ?? source.authority}</span></td>
                  <td>
                    <div className="source-record-links">
                      {source.used_by.slice(0, 2).map((id) => {
                        const record = recordById[id]
                        return record
                          ? <button type="button" key={id} onClick={() => onInspectRecord(record)}>{record.name}</button>
                          : <span key={id}>{id}</span>
                      })}
                      {source.used_by.length > 2 && <span>+{source.used_by.length - 2}</span>}
                    </div>
                  </td>
                  <td className="source-identifier">{source.doi ? `DOI ${source.doi}` : 'Canonical link'}</td>
                  <td><button className="source-open" type="button" onClick={() => void openResearchSource(source.url, source.title)} aria-label={`Open source: ${source.title}`}>Open</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
