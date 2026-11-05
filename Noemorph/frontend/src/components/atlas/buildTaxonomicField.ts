import Graph from 'graphology'
import type { TheoryRecord } from '../../types'
import { ATLAS_GRAPHITE, LOCUS_ORDER, macroGroup } from '../atlasModel'

/**
 * The eight record classes currently represented by the catalog. The order is
 * deliberate: empirical descriptions begin at the top of the field and the
 * progressively more interpretive / historical classes follow below them.
 */
export const ROW_KINDS = [
  'Scientific theory',
  'Model or framework',
  'Clinical / state model',
  'Theory of mind / social cognition',
  'Phenomenological construct',
  'Philosophical position',
  'Argument / challenge',
  'Historical tradition',
] as const

export type TaxonomicRowKind = (typeof ROW_KINDS)[number]

export interface TaxonomicFieldNodeAttributes {
  x: number
  y: number
  size: number
  color: string
  label: string
  fullLabel: string
  forceLabel: false
  group: string
  domain: string
  kind: string
  recordId: string
  citationCount: number
  type: 'square'
  [key: string]: unknown
}

export interface TaxonomicFieldEdgeAttributes {
  [key: string]: unknown
}

export interface TaxonomicFieldColumn {
  group: string
  index: number
  color: string
  x: number
  minX: number
  maxX: number
  recordCount: number
  domainCount: number
}

export interface TaxonomicFieldRow {
  kind: string
  index: number
  y: number
  minY: number
  maxY: number
  recordCount: number
}

export interface TaxonomicFieldCell {
  id: string
  group: string
  kind: string
  columnIndex: number
  rowIndex: number
  x: number
  y: number
  minX: number
  maxX: number
  minY: number
  maxY: number
  recordCount: number
  domainCount: number
}

export interface TaxonomicFieldDomain {
  id: string
  group: string
  kind: string
  domain: string
  columnIndex: number
  rowIndex: number
  x: number
  y: number
  minX: number
  maxX: number
  minY: number
  maxY: number
  recordCount: number
  recordIds: string[]
}

export interface TaxonomicFieldBounds {
  minX: number
  maxX: number
  minY: number
  maxY: number
  width: number
  height: number
  centerX: number
  centerY: number
}

export interface TaxonomicFieldBuild {
  graph: Graph<TaxonomicFieldNodeAttributes, TaxonomicFieldEdgeAttributes>
  columns: TaxonomicFieldColumn[]
  rows: TaxonomicFieldRow[]
  cells: TaxonomicFieldCell[]
  domains: TaxonomicFieldDomain[]
  recordById: ReadonlyMap<string, TheoryRecord>
  nodeIdByRecordId: ReadonlyMap<string, string>
  bounds: TaxonomicFieldBounds
}

const CELL_WIDTH = 14
const CELL_HEIGHT = 8.5
const COLUMN_GAP = 3.25
const ROW_GAP = 2.25
const CELL_INSET_X = 1.15
const CELL_INSET_Y = 0.9
const FIELD_MARGIN = 2.5

function sortToken(value: string): string {
  return value.normalize('NFKD').toLocaleLowerCase('en-US')
}

function compareText(left: string, right: string): number {
  const normalizedLeft = sortToken(left)
  const normalizedRight = sortToken(right)
  if (normalizedLeft < normalizedRight) return -1
  if (normalizedLeft > normalizedRight) return 1
  return left < right ? -1 : left > right ? 1 : 0
}

function compareRecords(left: TheoryRecord, right: TheoryRecord): number {
  return compareText(left.name, right.name) || compareText(left.id, right.id)
}

function nodeId(recordId: string): string {
  return `record:${recordId}`
}

function coordinateKey(group: string, kind: string, domain: string): string {
  return `${group}\u0000${kind}\u0000${domain}`
}

function cellId(group: string, kind: string): string {
  return `cell:${group}\u0000${kind}`
}

function domainId(group: string, kind: string, domain: string): string {
  return `domain:${coordinateKey(group, kind, domain)}`
}

function calculateBounds(columns: TaxonomicFieldColumn[], rows: TaxonomicFieldRow[]): TaxonomicFieldBounds {
  if (!columns.length || !rows.length) {
    return { minX: -1, maxX: 1, minY: -1, maxY: 1, width: 2, height: 2, centerX: 0, centerY: 0 }
  }

  const minX = Math.min(...columns.map((column) => column.minX)) - FIELD_MARGIN
  const maxX = Math.max(...columns.map((column) => column.maxX)) + FIELD_MARGIN
  const minY = Math.min(...rows.map((row) => row.minY)) - FIELD_MARGIN
  const maxY = Math.max(...rows.map((row) => row.maxY)) + FIELD_MARGIN
  return {
    minX,
    maxX,
    minY,
    maxY,
    width: maxX - minX,
    height: maxY - minY,
    centerX: (minX + maxX) / 2,
    centerY: (minY + maxY) / 2,
  }
}

/**
 * Builds the zoomed-out Atlas as a fixed taxonomic field rather than a
 * relationship graph. There are intentionally no edges: horizontal position
 * is the canonical research locus and vertical position is the catalog's
 * explicit record class. Domain proximity only packs records inside that
 * computed perspective × explicit record-class cell; it does not assert
 * conceptual similarity or a theory-to-theory relationship.
 */
export function buildTaxonomicField(records: TheoryRecord[]): TaxonomicFieldBuild {
  const graph = new Graph<TaxonomicFieldNodeAttributes, TaxonomicFieldEdgeAttributes>({
    type: 'undirected',
    multi: false,
    allowSelfLoops: false,
  })

  const canonicalKinds = new Set<string>(ROW_KINDS)
  const additionalKinds = [...new Set(records.map((record) => record.kind))]
    .filter((kind) => !canonicalKinds.has(kind))
    .sort(compareText)
  // Appending a future explicit class preserves records without silently
  // reclassifying them.
  const rowKinds: string[] = [...ROW_KINDS, ...additionalKinds]

  const recordById = new Map<string, TheoryRecord>()
  const nodeIdByRecordId = new Map<string, string>()
  records.forEach((record) => {
    if (recordById.has(record.id)) throw new Error(`Duplicate theory record id: ${record.id}`)
    recordById.set(record.id, record)
    nodeIdByRecordId.set(record.id, nodeId(record.id))
  })

  const columns: TaxonomicFieldColumn[] = LOCUS_ORDER.map((group, index) => {
    const groupRecords = records.filter((record) => macroGroup(record) === group)
    const x = index * (CELL_WIDTH + COLUMN_GAP)
    return {
      group,
      index,
      color: ATLAS_GRAPHITE,
      x,
      minX: x - CELL_WIDTH / 2,
      maxX: x + CELL_WIDTH / 2,
      recordCount: groupRecords.length,
      domainCount: new Set(groupRecords.map((record) => record.domain)).size,
    }
  })

  const rows: TaxonomicFieldRow[] = rowKinds.map((kind, index) => {
    // Sigma's positive Y axis reads upward, so row zero is the visual top.
    const y = (rowKinds.length - 1 - index) * (CELL_HEIGHT + ROW_GAP)
    return {
      kind,
      index,
      y,
      minY: y - CELL_HEIGHT / 2,
      maxY: y + CELL_HEIGHT / 2,
      recordCount: records.filter((record) => record.kind === kind).length,
    }
  })

  const cells: TaxonomicFieldCell[] = []
  const domains: TaxonomicFieldDomain[] = []

  columns.forEach((column) => {
    rows.forEach((row) => {
      const members = records
        .filter((record) => macroGroup(record) === column.group && record.kind === row.kind)
        .sort(compareRecords)
      const domainBuckets = new Map<string, TheoryRecord[]>()
      members.forEach((record) => {
        domainBuckets.set(record.domain, [...(domainBuckets.get(record.domain) ?? []), record])
      })
      const orderedDomains = [...domainBuckets.entries()]
        .map(([domain, domainRecords]) => ({ domain, records: domainRecords.sort(compareRecords) }))
        .sort((left, right) => compareText(left.domain, right.domain))

      cells.push({
        id: cellId(column.group, row.kind),
        group: column.group,
        kind: row.kind,
        columnIndex: column.index,
        rowIndex: row.index,
        x: column.x,
        y: row.y,
        minX: column.minX,
        maxX: column.maxX,
        minY: row.minY,
        maxY: row.maxY,
        recordCount: members.length,
        domainCount: orderedDomains.length,
      })

      if (!orderedDomains.length) return

      const innerWidth = CELL_WIDTH - CELL_INSET_X * 2
      const innerHeight = CELL_HEIGHT - CELL_INSET_Y * 2
      const domainColumns = Math.max(1, Math.ceil(Math.sqrt(orderedDomains.length * (innerWidth / innerHeight))))
      const domainRows = Math.ceil(orderedDomains.length / domainColumns)
      const slotWidth = innerWidth / domainColumns
      const slotHeight = innerHeight / domainRows

      orderedDomains.forEach(({ domain, records: domainRecords }, domainIndex) => {
        const domainColumn = domainIndex % domainColumns
        const domainRow = Math.floor(domainIndex / domainColumns)
        const centerX = column.x - innerWidth / 2 + slotWidth * (domainColumn + 0.5)
        const centerY = row.y + innerHeight / 2 - slotHeight * (domainRow + 0.5)
        const minX = centerX - slotWidth / 2
        const maxX = centerX + slotWidth / 2
        const minY = centerY - slotHeight / 2
        const maxY = centerY + slotHeight / 2

        domains.push({
          id: domainId(column.group, row.kind, domain),
          group: column.group,
          kind: row.kind,
          domain,
          columnIndex: column.index,
          rowIndex: row.index,
          x: centerX,
          y: centerY,
          minX,
          maxX,
          minY,
          maxY,
          recordCount: domainRecords.length,
          recordIds: domainRecords.map((record) => record.id),
        })

        const packingAspect = Math.max(0.5, Math.min(2, slotWidth / slotHeight))
        const recordColumns = Math.max(1, Math.ceil(Math.sqrt(domainRecords.length * packingAspect)))
        const recordRows = Math.max(1, Math.ceil(domainRecords.length / recordColumns))
        const stepX = Math.min(1.08, slotWidth * 0.68 / Math.max(1, recordColumns - 1))
        const stepY = Math.min(1.08, slotHeight * 0.68 / Math.max(1, recordRows - 1))

        domainRecords.forEach((record, recordIndex) => {
          const recordColumn = recordIndex % recordColumns
          const recordRow = Math.floor(recordIndex / recordColumns)
          const occupiedColumns = Math.min(recordColumns, domainRecords.length - recordRow * recordColumns)
          const x = centerX + (recordColumn - (occupiedColumns - 1) / 2) * stepX
          const y = centerY + ((recordRows - 1) / 2 - recordRow) * stepY
          const citationCount = record.citations.length
          graph.addNode(nodeId(record.id), {
            x,
            y,
            size: 2.5 + Math.min(2.75, Math.log2(citationCount + 1) * 0.68),
            color: column.color,
            label: record.name,
            fullLabel: record.name,
            forceLabel: false,
            group: column.group,
            domain: record.domain,
            kind: record.kind,
            recordId: record.id,
            citationCount,
            type: 'square',
          })
        })
      })
    })
  })

  return {
    graph,
    columns,
    rows,
    cells,
    domains,
    recordById,
    nodeIdByRecordId,
    bounds: calculateBounds(columns, rows),
  }
}
