import { lazy, Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { loadDiscovery, loadWorkspace } from './api'
import { AtlasInspector } from './components/AtlasInspector'
import { CatalogView } from './components/CatalogView'
import { DiscoveryInspector } from './components/DiscoveryInspector'
import { recordMatches, recordSearchRank } from './components/atlasModel'
import { parseComparisonIds } from './components/recordComparison'
import { MethodsView } from './components/MethodsView'
import { RecordInspector } from './components/RecordInspector'
import { SourcesView } from './components/SourcesView'
import type {
  CatalogMetadata,
  CoverageResponse,
  DiscoveryEntry,
  SourceRecord,
  TaxonomyGraph,
  TheoryRecord,
  ViewKey,
} from './types'

const AtlasView = lazy(() => import('./components/AtlasView').then((module) => ({ default: module.AtlasView })))
const CoverageView = lazy(() => import('./components/CoverageView').then((module) => ({ default: module.CoverageView })))
const SemanticReviewView = lazy(() => import('./components/semantic/SemanticReviewView').then((module) => ({ default: module.SemanticReviewView })))

interface WorkspaceData {
  records: TheoryRecord[]
  sources: SourceRecord[]
  coverage: CoverageResponse
  metadata: CatalogMetadata
  graph: TaxonomyGraph
}

const NAV_ITEMS: Array<{ id: ViewKey; label: string; shortcut: string }> = [
  { id: 'atlas', label: 'Taxonomic atlas', shortcut: '1' },
  { id: 'catalog', label: 'Record catalog', shortcut: '2' },
  { id: 'sources', label: 'Source register', shortcut: '3' },
  { id: 'relations', label: 'Relationship review', shortcut: '4' },
  { id: 'coverage', label: 'Collection audit', shortcut: '5' },
  { id: 'methods', label: 'Research method', shortcut: '6' },
]

const VIEW_TITLES: Record<ViewKey, string> = {
  atlas: 'Taxonomic atlas',
  catalog: 'Record catalog',
  relations: 'Relationship review',
  sources: 'Source register',
  coverage: 'Collection audit',
  methods: 'Research method',
}

export default function App() {
  const [view, setView] = useState<ViewKey>(() => parseComparisonIds(window.location.search).length === 2 ? 'catalog' : 'atlas')
  const [comparisonIds, setComparisonIds] = useState<string[]>(() => parseComparisonIds(window.location.search))
  const [recordQuery, setRecordQuery] = useState('')
  const [sourceQuery, setSourceQuery] = useState('')
  const [semanticQuery, setSemanticQuery] = useState('')
  const [selectedKind, setSelectedKind] = useState('All records')
  const [catalogScope, setCatalogScope] = useState<'catalog' | 'discovery'>('catalog')
  const [selectedId, setSelectedId] = useState<string>()
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const [data, setData] = useState<WorkspaceData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [discovery, setDiscovery] = useState<DiscoveryEntry[]>([])
  const [discoveryState, setDiscoveryState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle')
  const [discoveryError, setDiscoveryError] = useState<string | null>(null)
  const [selectedDiscoverySlug, setSelectedDiscoverySlug] = useState<string>()
  const discoveryRequestActive = useRef(false)

  useEffect(() => {
    let cancelled = false
    loadWorkspace()
      .then((workspace) => {
        if (cancelled) return
        setData({
          records: workspace.catalog.items,
          sources: workspace.sources.items,
          coverage: workspace.coverage,
          metadata: workspace.metadata,
          graph: workspace.graph,
        })
      })
      .catch((reason: unknown) => {
        if (cancelled) return
        setError(reason instanceof Error ? reason.message : 'The research service could not be reached.')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const requestDiscovery = () => {
    if (discoveryRequestActive.current || discoveryState === 'loading') return
    discoveryRequestActive.current = true
    setDiscoveryState('loading')
    setDiscoveryError(null)
    loadDiscovery()
      .then((response) => {
        setDiscovery(response.items)
        setDiscoveryState('ready')
      })
      .catch((reason: unknown) => {
        setDiscoveryError(reason instanceof Error ? reason.message : 'The discovery registry could not be reached.')
        setDiscoveryState('error')
      })
      .finally(() => {
        discoveryRequestActive.current = false
      })
  }

  useEffect(() => {
    if (view === 'catalog' && catalogScope === 'discovery' && discoveryState === 'idle') {
      requestDiscovery()
    }
  }, [catalogScope, discoveryState, view])

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      const isEditing = Boolean(target && (
        ['INPUT', 'SELECT', 'TEXTAREA', 'BUTTON'].includes(target.tagName)
        || target.isContentEditable
      ))
      if ((event.ctrlKey || event.metaKey) && event.key.toLocaleLowerCase() === 'k') {
        event.preventDefault()
        if (view === 'coverage' || view === 'methods') {
          setView('catalog')
          setInspectorOpen(false)
          window.requestAnimationFrame(() => document.getElementById('corpus-search')?.focus())
        } else {
          document.getElementById('corpus-search')?.focus()
        }
      }
      if (!isEditing && !event.ctrlKey && !event.metaKey && !event.altKey) {
        const item = NAV_ITEMS.find((candidate) => candidate.shortcut === event.key)
        if (item) {
          setView(item.id)
          setInspectorOpen(false)
          setSelectedId(undefined)
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [view])

  useEffect(() => {
    if (!data || comparisonIds.length !== 2) return
    if (comparisonIds.some((id) => !data.records.some((record) => record.id === id))) {
      setComparisonIds([])
    }
  }, [comparisonIds, data])

  useEffect(() => {
    const url = new URL(window.location.href)
    if (comparisonIds.length === 2) {
      url.searchParams.set('compare', comparisonIds.join(','))
      url.searchParams.delete('record')
    } else {
      url.searchParams.delete('compare')
    }
    window.history.replaceState(null, '', url.href)
  }, [comparisonIds])

  useEffect(() => {
    if (comparisonIds.length === 2 && view === 'catalog' && catalogScope === 'catalog' && data) {
      window.requestAnimationFrame(() => document.getElementById('compare-title')?.focus({ preventScroll: true }))
    }
  }, [comparisonIds, view, catalogScope, data])

  const toggleComparison = (id: string) => {
    setComparisonIds((current) => {
      if (current.includes(id)) return current.filter((item) => item !== id)
      if (current.length === 2) return current
      return [...current, id]
    })
    setInspectorOpen(false)
  }

  const records = data?.records ?? []
  const selectedRecord = useMemo(
    () => records.find((record) => record.id === selectedId),
    [records, selectedId],
  )
  const selectedDiscoveryEntry = useMemo(
    () => discovery.find((entry) => entry.slug === selectedDiscoverySlug),
    [discovery, selectedDiscoverySlug],
  )
  const handleSelect = (record: TheoryRecord) => {
    setSelectedId(record.id)
    setInspectorOpen(true)
  }
  const handleSelectDiscovery = (entry: DiscoveryEntry) => {
    setSelectedDiscoverySlug(entry.slug)
    setInspectorOpen(true)
  }

  const activateTopSearchMatch = () => {
    if (!recordQuery.trim() || (view !== 'atlas' && view !== 'catalog')) return
    if (view === 'atlas' || catalogScope === 'discovery') {
      document.getElementById('corpus-search')?.blur()
      return
    }
    const match = records
      .filter((record) => recordMatches(record, recordQuery))
      .sort((left, right) => recordSearchRank(left, recordQuery) - recordSearchRank(right, recordQuery) || left.name.localeCompare(right.name))[0]
    if (match) {
      setRecordQuery('')
      handleSelect(match)
    }
  }

  const changeView = (nextView: ViewKey) => {
    setView(nextView)
    setInspectorOpen(false)
    setSelectedId(undefined)
    setSelectedDiscoverySlug(undefined)
  }

  const inspectRecordIn = (record: TheoryRecord, nextView: 'atlas' | 'catalog') => {
    setRecordQuery('')
    setSelectedId(record.id)
    setView(nextView)
    setInspectorOpen(true)
  }

  const inspectorVisible = inspectorOpen && (view === 'atlas' || view === 'catalog')

  const renderView = () => {
    if (error) {
      return (
        <div className="service-state service-error">
          <span className="service-state-code">SERVICE</span>
          <div><strong>Research service unavailable</strong><p>{error}</p></div>
        </div>
      )
    }
    if (!data) {
      return (
        <div className="service-state">
          <span className="loading-indicator" />
          <div><strong>Indexing research corpus</strong><p>Loading catalog, citations, and audit state…</p></div>
        </div>
      )
    }

    if (view === 'atlas') {
      return (
        <AtlasView
          records={records}
          selectedId={selectedId}
          onSelect={handleSelect}
          onClearSelection={() => {
            setSelectedId(undefined)
            setInspectorOpen(false)
          }}
          onOpenTrace={() => setInspectorOpen(false)}
          query={recordQuery}
          onClearQuery={() => setRecordQuery('')}
          onQueryChange={setRecordQuery}
        />
      )
    }
    if (view === 'catalog') {
      return (
        <CatalogView
          records={records}
          discovery={discovery}
          discoveryState={discoveryState}
          discoveryError={discoveryError}
          onRetryDiscovery={requestDiscovery}
          selectedDiscoverySlug={selectedDiscoverySlug}
          onSelectDiscovery={handleSelectDiscovery}
          selectedId={selectedId}
          onSelect={handleSelect}
          comparisonIds={comparisonIds}
          onToggleComparison={toggleComparison}
          onClearComparison={() => setComparisonIds([])}
          query={recordQuery}
          selectedKind={selectedKind}
          onKindChange={setSelectedKind}
          scope={catalogScope}
          onScopeChange={(scope) => {
            setCatalogScope(scope)
            setInspectorOpen(false)
            setSelectedId(undefined)
            setSelectedDiscoverySlug(undefined)
          }}
        />
      )
    }
    if (view === 'relations') {
      return (
        <SemanticReviewView
          records={records}
          query={semanticQuery}
          onOpenRecord={(record) => inspectRecordIn(record, 'catalog')}
        />
      )
    }
    if (view === 'sources') {
      return (
        <SourcesView
          sources={data.sources}
          records={records}
          query={sourceQuery}
          onInspectRecord={(record) => inspectRecordIn(record, 'catalog')}
        />
      )
    }
    if (view === 'coverage') return <CoverageView coverage={data.coverage} onInspectRecord={(recordId) => {
      const match = records.find((record) => record.id === recordId)
      if (match) inspectRecordIn(match, 'catalog')
    }} />
    return <MethodsView metadata={data.metadata} onNavigate={changeView} />
  }

  const viewTitle = VIEW_TITLES[view]
  const searchValue = view === 'sources' ? sourceQuery : view === 'relations' ? semanticQuery : recordQuery
  const searchAvailable = view === 'atlas' || view === 'catalog' || view === 'relations' || view === 'sources'
  const discoverySearch = view === 'catalog' && catalogScope === 'discovery'

  return (
    <main className={`application-frame editorial-shell view-${view} ${inspectorVisible ? 'inspector-open' : 'inspector-collapsed'}`}>
      <aside className="folio-index">
        <header className="folio-brand">
          <strong>NOEMORPH</strong>
        </header>
        <nav className="folio-navigation" aria-label="Research workspaces">
          {NAV_ITEMS.map((item) => (
            <button
              type="button"
              key={item.id}
              className={view === item.id ? 'active' : ''}
              onClick={() => changeView(item.id)}
              aria-current={view === item.id ? 'page' : undefined}
            >
              <strong>{item.label}</strong>
            </button>
          ))}
        </nav>
      </aside>

      <header className="folio-masthead">
        <label className="mobile-workspace-switcher">
          <span>WORKSPACE</span>
          <select value={view} onChange={(event) => changeView(event.target.value as ViewKey)} aria-label="Choose research workspace">
            {NAV_ITEMS.map((item) => <option value={item.id} key={item.id}>{item.label}</option>)}
          </select>
        </label>
        <div className="folio-page-title">
          <strong>{viewTitle}</strong>
        </div>
        {searchAvailable && (
          <form className="folio-search" role="search" onSubmit={(event) => { event.preventDefault(); activateTopSearchMatch() }}>
            <input
              id="corpus-search"
              value={searchValue}
              onChange={(event) => {
                if (view === 'sources') setSourceQuery(event.target.value)
                else if (view === 'relations') setSemanticQuery(event.target.value)
                else setRecordQuery(event.target.value)
              }}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && view !== 'sources') {
                  event.preventDefault()
                  if (view === 'relations') {
                    event.currentTarget.blur()
                    return
                  }
                  activateTopSearchMatch()
                  return
                }
                if (event.key !== 'Escape') return
                event.preventDefault()
                event.stopPropagation()
                if (view === 'sources') setSourceQuery('')
                else if (view === 'relations') setSemanticQuery('')
                else setRecordQuery('')
              }}
              aria-label={view === 'sources' ? 'Search sources' : view === 'relations' ? 'Search candidate relationships' : discoverySearch ? 'Search discovery source pages' : 'Search records'}
              placeholder={view === 'sources' ? 'Author, journal, title, or DOI' : view === 'relations' ? 'Record or concept' : discoverySearch ? 'Source title, person, category, or concept' : 'Theory, author, domain, or concept'}
            />
            {searchValue && (
              <button
                type="button"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => {
                  if (view === 'sources') setSourceQuery('')
                  else if (view === 'relations') setSemanticQuery('')
                  else setRecordQuery('')
                }}
                aria-label="Clear search"
              >Clear</button>
            )}
          </form>
        )}
        {view === 'atlas' && <div className="folio-corpus-count"><strong>{records.length}</strong><small>records</small></div>}
      </header>

      <section className="workspace-stage">
        <Suspense fallback={<div className="service-state"><span className="loading-indicator" /><div><strong>Preparing research view</strong><p>Loading the visualization module…</p></div></div>}>
          {renderView()}
        </Suspense>
      </section>

      {view === 'atlas' && inspectorVisible && selectedRecord && (
        <AtlasInspector
          record={selectedRecord}
          onClose={() => { setInspectorOpen(false); setSelectedId(undefined) }}
          onViewCatalog={(record) => inspectRecordIn(record, 'catalog')}
        />
      )}
      {view === 'catalog' && inspectorVisible && (
        catalogScope === 'discovery' && selectedDiscoveryEntry
          ? <DiscoveryInspector entry={selectedDiscoveryEntry} onClose={() => { setInspectorOpen(false); setSelectedDiscoverySlug(undefined) }} />
          : <RecordInspector
              record={selectedRecord}
              onClose={() => setInspectorOpen(false)}
              mobileOpen={inspectorOpen}
              currentView="catalog"
              onLocateInAtlas={(record) => inspectRecordIn(record, 'atlas')}
              onViewInCatalog={(record) => inspectRecordIn(record, 'catalog')}
            />
      )}
    </main>
  )
}
