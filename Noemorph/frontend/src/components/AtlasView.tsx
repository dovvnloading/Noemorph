import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import Sigma from 'sigma'
import type { CameraState } from 'sigma/types'
import { layerFill, sdfSquare } from 'sigma/rendering'
import type { TheoryRecord } from '../types'
import {
  ATLAS_COBALT,
  ATLAS_GRAPHITE,
  locusShortLabel,
  macroGroup,
  recordMatches,
  recordSearchRank,
} from './atlasModel'
import {
  buildTaxonomicField,
  type TaxonomicFieldBuild,
  type TaxonomicFieldEdgeAttributes,
  type TaxonomicFieldNodeAttributes,
} from './atlas/buildTaxonomicField'

interface AtlasViewProps {
  records: TheoryRecord[]
  selectedId?: string
  onSelect: (record: TheoryRecord) => void
  onClearSelection?: () => void
  onOpenTrace?: () => void
  query: string
  onClearQuery?: () => void
  onQueryChange?: (query: string) => void
}

type Projection = 'field' | 'trace'

interface ScreenColumn {
  group: string
  shortLabel: string
  color: string
  x: number
  y: number
  recordCount: number
  domainCount: number
}

interface ScreenRow {
  kind: string
  y: number
  recordCount: number
}

interface ScreenDomain {
  id: string
  label: string
  x: number
  y: number
  width: number
  height: number
  showLabel: boolean
}

interface GuideLayout {
  width: number
  height: number
  columns: ScreenColumn[]
  rows: ScreenRow[]
  verticals: number[]
  horizontals: number[]
  domains: ScreenDomain[]
}

function boundaryValues(values: Array<{ min: number; max: number }>, descending = false) {
  if (!values.length) return []
  const ordered = [...values].sort((left, right) => descending ? right.max - left.max : left.min - right.min)
  const boundaries = [descending ? ordered[0].max : ordered[0].min]
  for (let index = 1; index < ordered.length; index += 1) {
    boundaries.push(descending
      ? (ordered[index - 1].min + ordered[index].max) / 2
      : (ordered[index - 1].max + ordered[index].min) / 2)
  }
  boundaries.push(descending ? ordered.at(-1)!.min : ordered.at(-1)!.max)
  return boundaries
}

function truncate(value: string, length: number) {
  return value.length <= length ? value : `${value.slice(0, Math.max(0, length - 1)).trimEnd()}…`
}

function EvidenceTrace({ record }: { record: TheoryRecord }) {
  const classification = [
    ['Computed perspective', macroGroup(record)],
    ['Domain', record.domain],
    ['Record class', record.kind],
    ['Tradition', record.tradition],
  ]
  const citations = record.citations.slice(0, 8)

  return (
    <div className="atlas-trace" aria-label={`Evidence trace for ${record.name}`}>
      <div className="atlas-trace-grid">
        <section className="atlas-trace-lane atlas-trace-classification">
          <header><strong>Classification coordinates</strong></header>
          <div className="atlas-trace-stack">
            {classification.map(([label, value]) => (
              <article key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </article>
            ))}
          </div>
        </section>

        <section className="atlas-trace-lane atlas-trace-record">
          <header><strong>Selected record</strong></header>
          <article className="atlas-trace-primary">
            <i style={{ '--trace-color': ATLAS_COBALT } as CSSProperties} />
            <span>{record.kind}</span>
            <strong>{record.name}</strong>
            <small>{record.status}</small>
            <p>{record.summary}</p>
          </article>
        </section>

        <section className="atlas-trace-lane atlas-trace-attribution">
          <header><strong>Attributed people</strong></header>
          <div className="atlas-trace-stack">
            {record.proponents.length ? record.proponents.map((proponent) => (
              <article key={proponent}>
                <strong>{proponent}</strong>
              </article>
            )) : <p className="atlas-trace-empty">No person attribution is recorded.</p>}
          </div>
        </section>

        <section className="atlas-trace-lane atlas-trace-sources">
          <header><strong>{record.citations.length} cited works</strong></header>
          <div className="atlas-trace-stack">
            {citations.map((citation, index) => (
              <a key={`${citation.url}:${index}`} href={citation.url} target="_blank" rel="noreferrer">
                <span>{citation.authority.replaceAll('-', ' ')} · {citation.year}</span>
                <strong>{citation.title}</strong>
                <small>{citation.authors}</small>
                <b aria-hidden="true">↗</b>
              </a>
            ))}
            {record.citations.length > citations.length && (
              <p className="atlas-trace-more">+{record.citations.length - citations.length} additional works remain in the record inspector.</p>
            )}
          </div>
        </section>
      </div>
      <footer>
        <p>The perspective is a computed working taxonomy; other fields are direct catalog metadata. No theory-to-theory relationship is inferred.</p>
      </footer>
    </div>
  )
}

function buildGuideLayout(
  renderer: Sigma<TaxonomicFieldNodeAttributes, TaxonomicFieldEdgeAttributes>,
  field: TaxonomicFieldBuild,
  activeGroup: string | null,
): GuideLayout {
  const dimensions = renderer.getDimensions()
  const point = (x: number, y: number) => renderer.graphToViewport({ x, y })
  const verticalValues = boundaryValues(field.columns.map((column) => ({ min: column.minX, max: column.maxX })))
  const horizontalValues = boundaryValues(field.rows.map((row) => ({ min: row.minY, max: row.maxY })), true)
  const columns = field.columns.map((column) => {
    const screen = point(column.x, field.bounds.maxY)
    return {
      group: column.group,
      shortLabel: locusShortLabel(column.group),
      color: column.color,
      x: screen.x,
      y: point(column.x, field.rows[0]?.maxY ?? field.bounds.maxY).y,
      recordCount: column.recordCount,
      domainCount: column.domainCount,
    }
  })
  const rows = field.rows.map((row) => ({
    kind: row.kind,
    y: point(field.bounds.minX, row.y).y,
    recordCount: row.recordCount,
  }))
  const rankedDomains = activeGroup
    ? field.domains
        .filter((domain) => domain.group === activeGroup)
        .sort((left, right) => right.recordCount - left.recordCount || left.domain.localeCompare(right.domain))
    : []
  const labeled = new Set(rankedDomains.slice(0, 5).map((domain) => domain.id))
  const domains = rankedDomains.map((domain) => {
    const topLeft = point(domain.minX, domain.maxY)
    const bottomRight = point(domain.maxX, domain.minY)
    const width = Math.max(0, bottomRight.x - topLeft.x)
    const height = Math.max(0, bottomRight.y - topLeft.y)
    return {
      id: domain.id,
      label: `${truncate(domain.domain, 26)} · ${domain.recordCount}`,
      x: topLeft.x,
      y: topLeft.y,
      width,
      height,
      showLabel: labeled.has(domain.id) && width >= 72 && height >= 25,
    }
  })
  return {
    width: dimensions.width,
    height: dimensions.height,
    columns,
    rows,
    verticals: verticalValues.map((x) => point(x, field.bounds.centerY).x),
    horizontals: horizontalValues.map((y) => point(field.bounds.centerX, y).y),
    domains,
  }
}

export function AtlasView({
  records,
  selectedId,
  onSelect,
  onClearSelection,
  onOpenTrace,
  query,
  onClearQuery,
}: AtlasViewProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const rendererRef = useRef<Sigma<TaxonomicFieldNodeAttributes, TaxonomicFieldEdgeAttributes> | null>(null)
  const onSelectRef = useRef(onSelect)
  const onClearSelectionRef = useRef(onClearSelection)
  const hoveredRef = useRef<string | null>(null)
  const selectedRef = useRef<string | undefined>(selectedId)
  const activeGroupRef = useRef<string | null>(null)
  const queryRef = useRef(query.trim())
  const matchesRef = useRef(new Set<string>())
  const guideFrameRef = useRef<number | null>(null)
  const fieldCameraRef = useRef<CameraState | null>(null)
  const [projection, setProjection] = useState<Projection>('field')
  const [hoveredId, setHoveredId] = useState<string | null>(null)
  const [activeGroup, setActiveGroup] = useState<string | null>(null)
  const [indexOpen, setIndexOpen] = useState(false)
  const [railDismissed, setRailDismissed] = useState(false)
  const [activeResult, setActiveResult] = useState(0)
  const [cameraRatio, setCameraRatio] = useState(1)
  const [guideLayout, setGuideLayout] = useState<GuideLayout | null>(null)

  const field = useMemo(() => buildTaxonomicField(records), [records])
  const normalizedQuery = query.trim()
  const searchEngaged = normalizedQuery.length >= 2
  const searchMatches = useMemo(() => searchEngaged
    ? records
        .filter((record) => recordMatches(record, normalizedQuery))
        .sort((left, right) => recordSearchRank(left, normalizedQuery) - recordSearchRank(right, normalizedQuery) || left.name.localeCompare(right.name))
    : [...records].sort((left, right) => left.name.localeCompare(right.name)), [normalizedQuery, records, searchEngaged])
  const matchIds = useMemo(() => new Set(searchMatches.map((record) => record.id)), [searchMatches])
  const selectedRecord = selectedId ? field.recordById.get(selectedId) : undefined
  const hoveredRecord = hoveredId ? field.recordById.get(hoveredId) : undefined
  const domainCount = useMemo(() => new Set(records.map((record) => record.domain)).size, [records])

  onSelectRef.current = onSelect
  onClearSelectionRef.current = onClearSelection
  selectedRef.current = selectedId
  activeGroupRef.current = activeGroup
  queryRef.current = searchEngaged ? normalizedQuery : ''
  matchesRef.current = matchIds

  const scheduleGuideUpdate = useCallback(() => {
    if (guideFrameRef.current !== null) return
    guideFrameRef.current = window.requestAnimationFrame(() => {
      guideFrameRef.current = null
      const renderer = rendererRef.current
      if (!renderer) return
      setGuideLayout(buildGuideLayout(renderer, field, activeGroupRef.current))
      setCameraRatio(renderer.getCamera().getState().ratio)
    })
  }, [field])

  useEffect(() => {
    const container = containerRef.current
    if (!container || projection !== 'field') return
    const renderer = new Sigma<TaxonomicFieldNodeAttributes, TaxonomicFieldEdgeAttributes>(field.graph, container, {
      primitives: {
        nodes: {
          shapes: [sdfSquare()],
          layers: [layerFill()],
        },
      },
      styles: {
        nodes: [{
          color: { attribute: 'color' },
          size: { attribute: 'size' },
          shape: 'square',
        }],
      },
      settings: {
        allowInvalidContainer: true,
        enableCameraRotation: false,
        hideEdgesOnMove: true,
        hideLabelsOnMove: true,
        labelRenderedSizeThreshold: 999,
        minCameraRatio: 0.32,
        maxCameraRatio: 1.8,
        renderLabels: false,
        stagePadding: 54,
        itemSizesReference: 'screen',
      },
      nodeReducer: (node, data) => {
        // Sigma 4's display data excludes custom graph attributes.
        const attributes = field.graph.getNodeAttributes(node)
        const recordId = attributes.recordId
        const queryActive = Boolean(queryRef.current)
        const matches = !queryActive || matchesRef.current.has(recordId)
        const inScope = !activeGroupRef.current || attributes.group === activeGroupRef.current
        const selected = selectedRef.current === recordId
        const hovered = hoveredRef.current === recordId
        let color = ATLAS_GRAPHITE
        let size = data.size
        let zIndex = 1
        if (!inScope) {
          color = '#d2cec5'
          size *= 0.72
          zIndex = 0
        }
        if (!matches) {
          color = '#dedad2'
          size *= 0.58
          zIndex = 0
        }
        if (queryActive && matches) {
          color = ATLAS_COBALT
          size = Math.max(4.6, size * 1.12)
          zIndex = 3
        }
        if (activeGroupRef.current && inScope) {
          color = ATLAS_COBALT
          zIndex = Math.max(zIndex, 2)
        }
        if (hovered) {
          color = ATLAS_COBALT
          size = Math.max(7, size * 1.35)
          zIndex = 6
        }
        if (selected) {
          color = ATLAS_COBALT
          size = 6.2
          zIndex = 7
        }
        return {
          ...data,
          color,
          forceLabel: false,
          highlighted: hovered,
          label: null,
          size,
          zIndex,
        }
      },
    })
    renderer.setCustomBBox({
      x: [field.bounds.minX, field.bounds.maxX],
      y: [field.bounds.minY, field.bounds.maxY],
    })
    rendererRef.current = renderer

    renderer.on('enterNode', ({ node }) => {
      const recordId = renderer.getGraph().getNodeAttribute(node, 'recordId')
      hoveredRef.current = recordId
      setHoveredId(recordId)
      renderer.refresh()
    })
    renderer.on('leaveNode', () => {
      hoveredRef.current = null
      setHoveredId(null)
      renderer.refresh()
    })
    renderer.on('clickNode', ({ node, event }) => {
      event.preventSigmaDefault()
      const recordId = renderer.getGraph().getNodeAttribute(node, 'recordId')
      const record = field.recordById.get(recordId)
      if (record) {
        setRailDismissed(true)
        onSelectRef.current(record)
      }
    })
    renderer.on('clickStage', () => {
      hoveredRef.current = null
      setHoveredId(null)
      onClearSelectionRef.current?.()
    })
    renderer.getCamera().on('updated', () => {
      if (hoveredRef.current) {
        hoveredRef.current = null
        setHoveredId(null)
      }
      scheduleGuideUpdate()
    })
    renderer.on('afterRender', scheduleGuideUpdate)

    const resizeObserver = new ResizeObserver(() => {
      renderer.resize()
      renderer.refresh()
      scheduleGuideUpdate()
    })
    resizeObserver.observe(container)
    const frame = window.requestAnimationFrame(() => {
      renderer.getCamera().setState(fieldCameraRef.current ?? { x: 0.5, y: 0.5, ratio: 1, angle: 0 })
      scheduleGuideUpdate()
    })

    return () => {
      window.cancelAnimationFrame(frame)
      if (guideFrameRef.current !== null) window.cancelAnimationFrame(guideFrameRef.current)
      guideFrameRef.current = null
      resizeObserver.disconnect()
      fieldCameraRef.current = renderer.getCamera().getState()
      rendererRef.current = null
      renderer.kill()
    }
  }, [field, projection, scheduleGuideUpdate])

  useEffect(() => {
    rendererRef.current?.refresh()
    scheduleGuideUpdate()
  }, [activeGroup, hoveredId, matchIds, scheduleGuideUpdate, selectedId])

  useEffect(() => {
    setActiveResult(0)
    if (searchEngaged) {
      setRailDismissed(false)
      setIndexOpen(false)
      setActiveGroup(null)
      setProjection('field')
      rendererRef.current?.getCamera().animate({ x: 0.5, y: 0.5, ratio: 1, angle: 0 }, { duration: 260 })
    }
  }, [normalizedQuery, searchEngaged])

  useEffect(() => {
    if (!selectedRecord && projection === 'trace') setProjection('field')
  }, [projection, selectedRecord])

  const graphPointToCamera = useCallback((x: number, y: number) => {
    const renderer = rendererRef.current
    if (!renderer) return undefined
    const viewport = renderer.graphToViewport({ x, y })
    return renderer.viewportToFramedGraph(viewport)
  }, [])

  const focusGroup = useCallback((group: string | null) => {
    const renderer = rendererRef.current
    if (!renderer) return
    const camera = renderer.getCamera()
    if (!group) {
      camera.animate({ x: 0.5, y: 0.5, ratio: 1, angle: 0 }, { duration: 300 })
      return
    }
    const column = field.columns.find((candidate) => candidate.group === group)
    if (!column) return
    const target = graphPointToCamera(column.x, field.bounds.centerY)
    if (target) camera.animate({ x: target.x, y: target.y, ratio: 0.82, angle: 0 }, { duration: 320 })
  }, [field, graphPointToCamera])

  const changeGroup = useCallback((group: string | null) => {
    setProjection('field')
    setActiveGroup(group)
    onClearSelectionRef.current?.()
    window.requestAnimationFrame(() => focusGroup(group))
  }, [focusGroup])

  const fitField = useCallback(() => {
    focusGroup(activeGroup)
  }, [activeGroup, focusGroup])

  const zoomBy = useCallback((factor: number) => {
    const camera = rendererRef.current?.getCamera()
    if (!camera) return
    const state = camera.getState()
    camera.animate({ ratio: Math.max(0.32, Math.min(1.8, state.ratio * factor)) }, { duration: 180 })
  }, [])

  const focusRecord = useCallback((record: TheoryRecord) => {
    setProjection('field')
    setRailDismissed(true)
    setIndexOpen(false)
    onSelectRef.current(record)
    const nodeId = field.nodeIdByRecordId.get(record.id)
    const renderer = rendererRef.current
    if (!nodeId || !renderer?.getGraph().hasNode(nodeId)) return
    const attributes = renderer.getGraph().getNodeAttributes(nodeId)
    const target = graphPointToCamera(attributes.x, attributes.y)
    if (!target) return
    renderer.getCamera().animate({
      x: target.x,
      y: target.y,
      ratio: Math.min(renderer.getCamera().getState().ratio, 0.72),
    }, { duration: 280 })
  }, [field, graphPointToCamera])

  const previewRecord = useCallback((recordId: string | null) => {
    hoveredRef.current = recordId
    setHoveredId(recordId)
    rendererRef.current?.refresh()
  }, [])

  const closeIndex = () => {
    setIndexOpen(false)
    if (searchEngaged) setRailDismissed(true)
  }

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      const editing = Boolean(target && (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.isContentEditable))
      const inSearchSurface = Boolean(target && (target.id === 'corpus-search' || target.closest('.atlas-result-rail')))
      if (searchEngaged && inSearchSurface && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) {
        event.preventDefault()
        const delta = event.key === 'ArrowDown' ? 1 : -1
        setActiveResult((current) => Math.max(0, Math.min(searchMatches.length - 1, current + delta)))
        return
      }
      if (searchEngaged && inSearchSurface && event.key === 'Enter' && searchMatches[activeResult]) {
        event.preventDefault()
        focusRecord(searchMatches[activeResult])
        return
      }
      if (editing) return
      if (event.key.toLocaleLowerCase() === 'f' && projection === 'field') {
        event.preventDefault()
        fitField()
      }
      if (event.key === 'Escape' && !searchEngaged) {
        if (hoveredRef.current) {
          previewRecord(null)
          return
        }
        if (selectedRef.current) {
          onClearSelectionRef.current?.()
          return
        }
        if (activeGroupRef.current) changeGroup(null)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeResult, changeGroup, fitField, focusRecord, previewRecord, projection, searchEngaged, searchMatches])

  const railOpen = (searchEngaged && !railDismissed) || indexOpen
  const fieldZoom = Math.round(100 / Math.max(0.01, cameraRatio))

  return (
    <section className="view-frame atlas-instrument">
      <header className="atlas-instrument-bar">
        <div className="atlas-instrument-title">
          <span>{projection === 'field' ? 'ATLAS / FIELD 00' : 'ATLAS / TRACE 01'}</span>
          <strong>{projection === 'field' ? 'Taxonomic field' : 'Evidence trace'}</strong>
        </div>

        <div className="atlas-projection-switch" aria-label="Atlas projection">
          <button type="button" className={projection === 'field' ? 'active' : ''} onClick={() => setProjection('field')}>Field</button>
          <button
            type="button"
            className={projection === 'trace' ? 'active' : ''}
            onClick={() => {
              if (!selectedRecord) return
              setProjection('trace')
              onOpenTrace?.()
            }}
            disabled={!selectedRecord}
          >Trace</button>
        </div>

        {projection === 'field' && (
          <label className="atlas-scope-control">
            <span>Perspective</span>
            <select value={activeGroup ?? ''} onChange={(event) => changeGroup(event.target.value || null)}>
              <option value="">All eight perspectives</option>
              {field.columns.map((column) => <option key={column.group} value={column.group}>{column.group}</option>)}
            </select>
          </label>
        )}

        <div className="atlas-instrument-meta">
          <span><strong>{records.length}</strong> records</span>
          <i />
          <span><strong>{domainCount}</strong> domains</span>
        </div>

        <div className="atlas-instrument-actions">
          {projection === 'field' && <>
            <button type="button" className={railOpen ? 'active' : ''} onClick={() => searchEngaged ? setRailDismissed((dismissed) => !dismissed) : setIndexOpen((open) => !open)} aria-label={railOpen ? 'Close record index' : 'Open record index'}>Index</button>
            <button type="button" onClick={() => zoomBy(0.78)} aria-label="Zoom in">Zoom +</button>
            <button type="button" onClick={() => zoomBy(1.28)} aria-label="Zoom out">Zoom −</button>
            <button type="button" onClick={fitField} aria-label="Fit current field">Fit</button>
          </>}
        </div>
      </header>

      {projection === 'trace' && selectedRecord ? <EvidenceTrace record={selectedRecord} /> : (
        <div className="atlas-field-shell">
          <aside className="atlas-row-axis" aria-label="Record class axis">
            <span className="atlas-axis-name">RECORD CLASS</span>
            {guideLayout?.rows.map((row) => (
              <div key={row.kind} className="atlas-row-label" style={{ top: row.y }}>
                <strong>{row.kind}</strong><span>{row.recordCount}</span>
              </div>
            ))}
          </aside>

          <div className="atlas-field-canvas">
            <div ref={containerRef} className="atlas-field-sigma" tabIndex={0} aria-label="Taxonomic field. Records are positioned by perspective and explicit record class. Use the record index for keyboard navigation." />
            <div className="atlas-mobile-key" role="note" aria-label="Taxonomic field axes">
              <span><b>X</b> research perspective</span>
              <span><b>Y</b> record class</span>
            </div>

            {guideLayout && (
              <svg className="atlas-field-guides" width={guideLayout.width} height={guideLayout.height} aria-hidden="true">
                {guideLayout.verticals.map((x, index) => <line key={`v:${index}`} x1={x} x2={x} y1={0} y2={guideLayout.height} />)}
                {guideLayout.horizontals.map((y, index) => <line key={`h:${index}`} x1={0} x2={guideLayout.width} y1={y} y2={y} />)}
                {guideLayout.domains.map((domain) => (
                  <g key={domain.id} className="atlas-domain-guide">
                    <rect x={domain.x} y={domain.y} width={domain.width} height={domain.height} />
                    {domain.showLabel && <text x={domain.x + 5} y={domain.y + 12}>{domain.label}</text>}
                  </g>
                ))}
              </svg>
            )}

            <div className="atlas-column-axis" aria-label="Research perspective axis">
              <span className="atlas-axis-name">RESEARCH PERSPECTIVE</span>
              {guideLayout?.columns.map((column) => (
                <button
                  key={column.group}
                  type="button"
                  className={activeGroup === column.group ? 'active' : activeGroup ? 'muted' : ''}
                  style={{ left: column.x, top: Math.max(7, column.y - 42), '--column-color': activeGroup === column.group ? ATLAS_COBALT : column.color } as CSSProperties}
                  onClick={() => changeGroup(activeGroup === column.group ? null : column.group)}
                  aria-label={`${column.group}: ${column.recordCount} records across ${column.domainCount} domains`}
                  title={`${column.group}: ${column.recordCount} records across ${column.domainCount} domains`}
                >
                  <i /><strong>{column.shortLabel}</strong><span>{column.recordCount}</span>
                </button>
              ))}
            </div>

            {railOpen && (
              <aside className="atlas-result-rail">
                <header>
                  <div><span>{searchEngaged ? 'SEARCH IN PLACE' : 'CORPUS INDEX'}</span><strong>{searchEngaged ? `${searchMatches.length} matches` : `${records.length} records`}</strong></div>
                  <button type="button" onClick={closeIndex} aria-label="Close record index">Close</button>
                </header>
                {searchEngaged && (
                  <div className="atlas-result-query"><span>QUERY</span><strong>{normalizedQuery}</strong></div>
                )}
                <div className="atlas-result-list">
                  {searchMatches.map((record, index) => (
                    <button
                      key={record.id}
                      type="button"
                      className={index === activeResult ? 'active' : ''}
                      onClick={() => focusRecord(record)}
                      onMouseEnter={() => { setActiveResult(index); previewRecord(record.id) }}
                      onMouseLeave={() => previewRecord(null)}
                      onFocus={() => { setActiveResult(index); previewRecord(record.id) }}
                      onBlur={() => previewRecord(null)}
                    >
                      <i style={{ '--result-color': searchEngaged ? ATLAS_COBALT : ATLAS_GRAPHITE } as CSSProperties} />
                      <span><strong>{record.name}</strong><small>{record.kind} · {record.domain}</small></span>
                      <b>{record.citations.length}</b>
                    </button>
                  ))}
                  {searchMatches.length === 0 && <p>No catalog record matches this query.</p>}
                </div>
              </aside>
            )}

            {hoveredRecord && (
              <div className="atlas-field-probe">
                <i style={{ '--probe-color': ATLAS_COBALT } as CSSProperties} />
                <span><strong>{hoveredRecord.name}</strong><small>{hoveredRecord.kind} · {hoveredRecord.domain}</small></span>
                <b>{hoveredRecord.citations.length} sources</b>
              </div>
            )}

            <div className="atlas-field-method">
              <p>Working taxonomy only; proximity is non-relational. Mark area = retained cited works.</p>
            </div>
            <div className="atlas-field-scale"><span>{activeGroup ? 'SCOPED FIELD' : 'FULL FIELD'}</span><strong>{fieldZoom}%</strong></div>
          </div>
        </div>
      )}
    </section>
  )
}
