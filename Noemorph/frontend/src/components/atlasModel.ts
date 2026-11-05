import type { GraphLink, GraphNode, TheoryRecord } from '../types'
import { researchProfileText } from './ResearchProfileValue'

export const ATLAS_ROOT_ID = 'phenomenon-consciousness'

/**
 * This order is intentionally semantic rather than alphabetical. Keeping it fixed
 * gives each research locus a persistent compass position as the catalog grows.
 */
export const LOCUS_ORDER = [
  'Metaphysics & philosophy of mind',
  'Historical & living traditions',
  'Mindreading & social cognition',
  'Embodied & phenomenological',
  'Neural & biological models',
  'Physical & field proposals',
  'Computational & informational',
  'Cognitive architectures',
] as const

export type LocusName = (typeof LOCUS_ORDER)[number]

/**
 * The field is a classification instrument, not a categorical heat map. A
 * single graphite mark keeps the eight perspectives from competing for
 * attention; cobalt is reserved for an explicit interaction state.
 */
export const ATLAS_GRAPHITE = '#555a5d'
export const ATLAS_COBALT = '#263fc0'

export const GROUP_COLORS = LOCUS_ORDER.map(() => ATLAS_GRAPHITE)

export const LOCUS_SHORT_LABELS: Record<LocusName, string> = {
  'Metaphysics & philosophy of mind': 'Metaphysics',
  'Historical & living traditions': 'Traditions',
  'Mindreading & social cognition': 'Social mind',
  'Embodied & phenomenological': 'Embodied',
  'Neural & biological models': 'Neural',
  'Physical & field proposals': 'Physical',
  'Computational & informational': 'Computational',
  'Cognitive architectures': 'Cognitive systems',
}

export function locusShortLabel(group: string): string {
  return LOCUS_SHORT_LABELS[group as LocusName] ?? group
}

const FULL_CIRCLE = Math.PI * 2
const LOCUS_RADIUS = 1650
const TRUNK_RADII = [260, 650, 1080]
const SINGLETON_BRANCH_CAPACITY = 3
const SHARED_DOMAIN_BRANCH_CAPACITY = 1
const BRANCH_LABEL_CLEARANCE = 62
const DOMAIN_LABEL_CORRIDOR = 0.48
const ATLAS_WORLD_PADDING = 330

export interface AtlasBounds {
  minX: number
  maxX: number
  minY: number
  maxY: number
  width: number
  height: number
  centerX: number
  centerY: number
}

export interface AtlasDomainDescriptor {
  id: string
  name: string
  group: string
  count: number
  recordIds: string[]
  branchIndex: number
  home_x: number
  home_y: number
}

export interface AtlasGraphModel {
  nodes: GraphNode[]
  links: GraphLink[]
  groups: string[]
  groupCounts: Record<string, number>
  domainCounts: Record<string, number>
  locusIdByGroup: Record<string, string>
  domainIdByRecordId: Record<string, string>
  domainIdByKey: Record<string, string>
  recordIdsByDomainId: Record<string, string[]>
  groupDomainIds: Record<string, string[]>
  pathByRecordId: Record<string, string[]>
  semanticPathByRecordId: Record<string, string[]>
  domains: AtlasDomainDescriptor[]
  bounds: AtlasBounds
}

export function macroGroup(record: TheoryRecord): string {
  const text = `${record.domain} ${record.tradition} ${record.kind}`.toLocaleLowerCase()
  if (record.kind.includes('social cognition')) return 'Mindreading & social cognition'
  if (record.kind === 'Historical tradition') return 'Historical & living traditions'
  if (record.kind === 'Philosophical position') return 'Metaphysics & philosophy of mind'
  if (/quantum|electromagnetic|field|physics|resonance/.test(text)) return 'Physical & field proposals'
  if (/phenomenolog|embodied|enactiv|sensorimotor/.test(text)) return 'Embodied & phenomenological'
  if (/computation|information|predict|mathemat|algorithm|network/.test(text)) return 'Computational & informational'
  if (/brain|neuro|cort|thalam|dendrit|cellular|biolog|affective/.test(text)) return 'Neural & biological models'
  return 'Cognitive architectures'
}

export function recordMatches(record: TheoryRecord, query: string): boolean {
  const normalized = query.trim().toLocaleLowerCase()
  if (!normalized) return true
  const haystack = [
    record.name,
    record.summary,
    record.domain,
    record.kind,
    ...record.proponents,
    ...(record.aliases ?? []),
    researchProfileText(record.claim_scope),
    record.boundary_note ?? '',
    researchProfileText(record.evidence_profile),
    ...(record.open_questions ?? []),
  ].join(' ').toLocaleLowerCase()
  return normalized.split(/\s+/).every((term) => haystack.includes(term))
}

/**
 * Produces a stable research-search ordering. Title and alias identity outrank
 * incidental mentions in a summary, so an exact theory name cannot be buried
 * beneath a record that only discusses it.
 */
export function recordSearchRank(record: TheoryRecord, query: string): number {
  const normalized = query.trim().toLocaleLowerCase()
  if (!normalized) return 100
  const name = record.name.toLocaleLowerCase()
  const aliases = (record.aliases ?? []).map((alias) => alias.toLocaleLowerCase())
  const proponents = record.proponents.map((proponent) => proponent.toLocaleLowerCase())
  const terms = normalized.split(/\s+/).filter(Boolean)
  const titleHasTerms = terms.every((term) => name.includes(term))

  if (name === normalized) return 0
  if (aliases.some((alias) => alias === normalized)) return 1
  if (name.startsWith(normalized)) return 2
  if (titleHasTerms) return 3
  if (aliases.some((alias) => terms.every((term) => alias.includes(term)))) return 4
  if (proponents.some((proponent) => terms.every((term) => proponent.includes(term)))) return 5
  if (`${record.domain} ${record.kind}`.toLocaleLowerCase().includes(normalized)) return 6
  return 7
}

function slug(value: string): string {
  return value
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 42)
}

/** FNV-1a provides a compact, deterministic suffix; it is not used for security. */
function stableHash(value: string): number {
  let hash = 0x811c9dc5
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 0x01000193)
  }
  return hash >>> 0
}

function hashToken(value: string): string {
  return stableHash(value).toString(36).padStart(7, '0')
}

function taxonomyDomainKey(group: string, domain: string): string {
  return `${group}\u0000${domain}`
}

export function locusNodeId(group: string): string {
  return `locus-${slug(group)}-${hashToken(group)}`
}

export function domainNodeId(group: string, domain: string): string {
  const key = taxonomyDomainKey(group, domain)
  return `domain-${slug(domain)}-${hashToken(key)}`
}

function point(radius: number, angle: number) {
  return { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius }
}

function fixedNode(node: Omit<GraphNode, 'x' | 'y' | 'fx' | 'fy'> & { home_x: number; home_y: number }): GraphNode {
  return {
    ...node,
    x: node.home_x,
    y: node.home_y,
    fx: node.home_x,
    fy: node.home_y,
  }
}

function orderedGroups(records: TheoryRecord[]): string[] {
  const present = new Set(records.map(macroGroup))
  const canonical = LOCUS_ORDER.filter((group) => present.has(group))
  const additions = [...present]
    .filter((group) => !(LOCUS_ORDER as readonly string[]).includes(group))
    .sort((left, right) => left.localeCompare(right))
  return [...canonical, ...additions]
}

function calculateBounds(nodes: GraphNode[]): AtlasBounds {
  if (!nodes.length) {
    return { minX: -1, maxX: 1, minY: -1, maxY: 1, width: 2, height: 2, centerX: 0, centerY: 0 }
  }
  // At whole-atlas zoom, this becomes roughly 45-70 screen pixels. That keeps
  // the outermost nodes and their admitted labels clear of the header, locus
  // dock, minimap, and viewport controls instead of pinning them to chrome.
  const padding = ATLAS_WORLD_PADDING
  const minX = Math.min(...nodes.map((node) => node.home_x ?? 0)) - padding
  const maxX = Math.max(...nodes.map((node) => node.home_x ?? 0)) + padding
  const minY = Math.min(...nodes.map((node) => node.home_y ?? 0)) - padding
  const maxY = Math.max(...nodes.map((node) => node.home_y ?? 0)) + padding
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

interface DomainEntry {
  domain: string
  members: TheoryRecord[]
  id: string
  hash: number
}

interface LeafPlacement {
  angle: number
  radius: number
  ring: number
}

interface BranchBucket {
  mode: 'shared' | 'singleton'
  entries: DomainEntry[]
  radius: number
  hash: number
}

interface BranchPlacement extends BranchBucket {
  branchIndex: number
  row: number
  tangent: number
  angle: number
  home_x: number
  home_y: number
}

function angularDistance(left: number, right: number): number {
  const difference = Math.abs((left - right) % FULL_CIRCLE)
  return Math.min(difference, FULL_CIRCLE - difference)
}

function safeLobeAngles(count: number, corridors: number[], phase = 0): number[] {
  if (count <= 0) return []
  const sampleCount = 360
  const candidates = Array.from({ length: sampleCount }, (_, index) =>
    phase + (index / sampleCount) * FULL_CIRCLE,
  ).filter((angle) => corridors.every((corridor) => angularDistance(angle, corridor) >= DOMAIN_LABEL_CORRIDOR))
  const selected: number[] = []
  while (selected.length < count && candidates.length) {
    let bestIndex = 0
    let bestScore = -1
    candidates.forEach((angle, index) => {
      const score = selected.length
        ? Math.min(...selected.map((chosen) => angularDistance(angle, chosen)))
        : Math.min(...corridors.map((corridor) => angularDistance(angle, corridor)))
      if (score > bestScore) {
        bestScore = score
        bestIndex = index
      }
    })
    selected.push(candidates.splice(bestIndex, 1)[0])
  }
  return selected.sort((left, right) => left - right)
}

/**
 * A shared domain is a small skill-tree constellation rather than a decorative
 * wagon wheel. Small domains use one open ring; large domains use two staggered
 * lobes. The outward corridor is intentionally empty so the domain label and
 * its incoming route never have a spoke drawn through them.
 */
function recordLobeLayout(count: number, outwardAngle: number, incomingAngle?: number): LeafPlacement[] {
  if (count <= 0) return []
  const corridors = incomingAngle === undefined
    ? [outwardAngle]
    : [outwardAngle, incomingAngle]

  if (count <= 8) {
    const minimumChord = count <= 4 ? 76 : 82
    const angles = safeLobeAngles(count, corridors, outwardAngle + Math.PI)
    const minimumStep = count <= 1
      ? Math.PI
      : Math.min(...angles.map((angle, index) => angularDistance(angle, angles[(index + 1) % angles.length])))
    const radius = Math.max(count <= 2 ? 88 : 96, minimumChord / (2 * Math.sin(minimumStep / 2)))
    return angles.map((angle) => ({ angle, radius, ring: 0 }))
  }

  const innerCount = Math.min(6, Math.max(4, Math.floor(count * 0.46)))
  const outerCount = count - innerCount
  const innerRadius = 108
  const innerAngles = safeLobeAngles(innerCount, corridors, outwardAngle + Math.PI)
  const outerAngles = safeLobeAngles(outerCount, corridors, outwardAngle + Math.PI + 0.31)
  const outerMinimumStep = Math.min(...outerAngles.map((angle, index) =>
    angularDistance(angle, outerAngles[(index + 1) % outerAngles.length])))
  const outerRadius = Math.max(184, 88 / (2 * Math.sin(outerMinimumStep / 2)))
  return [
    ...innerAngles.map((angle) => ({ angle, radius: innerRadius, ring: 0 })),
    ...outerAngles.map((angle) => ({ angle, radius: outerRadius, ring: 1 })),
  ]
}

function domainNeighborhoodRadius(memberCount: number): number {
  const layout = recordLobeLayout(memberCount, 0)
  const outerRadius = Math.max(0, ...layout.map((placement) => placement.radius))
  return outerRadius + 34
}

function singletonFan(count: number, outwardAngle: number): LeafPlacement[] {
  if (count <= 0) return []
  if (count === 1) return [{ angle: outwardAngle, radius: 108, ring: 0 }]
  const span = count === 2 ? 0.9 : 1.28
  const radius = count === 2 ? 122 : 142
  return Array.from({ length: count }, (_, index) => ({
    angle: outwardAngle - span / 2 + (index / (count - 1)) * span,
    radius,
    ring: 0,
  }))
}

function branchEntryLayout(bucket: Pick<BranchBucket, 'mode' | 'entries'>, outwardAngle: number): LeafPlacement[] {
  if (bucket.mode === 'singleton') return singletonFan(bucket.entries.length, outwardAngle)
  if (bucket.entries.length === 1) {
    return [{ angle: outwardAngle, radius: 78, ring: 0 }]
  }

  const footprints = bucket.entries.map((entry) => domainNeighborhoodRadius(entry.members.length))
  const halfSpread = 0.69
  const requiredRadius = (footprints[0] + footprints[1] + 72) / (2 * Math.sin(halfSpread))
  const radius = Math.max(248, requiredRadius)
  return [
    { angle: outwardAngle - halfSpread, radius, ring: 0 },
    { angle: outwardAngle + halfSpread, radius, ring: 0 },
  ]
}

function branchRadius(mode: BranchBucket['mode'], entries: DomainEntry[]): number {
  const layout = branchEntryLayout({ mode, entries }, 0)
  return layout.reduce((extent, placement, index) => {
    const semanticRadius = mode === 'singleton'
      ? 32
      : domainNeighborhoodRadius(entries[index].members.length)
    return Math.max(extent, placement.radius + semanticRadius)
  }, 0) + BRANCH_LABEL_CLEARANCE
}

function makeBranchBuckets(entries: DomainEntry[]): BranchBucket[] {
  const singletonEntries = entries.filter((entry) => entry.members.length === 1)
  const sharedEntries = entries.filter((entry) => entry.members.length > 1)
  const buckets: BranchBucket[] = []

  for (let index = 0; index < singletonEntries.length; index += SINGLETON_BRANCH_CAPACITY) {
    const members = singletonEntries.slice(index, index + SINGLETON_BRANCH_CAPACITY)
    buckets.push({
      mode: 'singleton',
      entries: members,
      radius: branchRadius('singleton', members),
      hash: stableHash(members.map((entry) => entry.id).join('\u0000')),
    })
  }

  // Large shared domains retain a branch of their own. Pairing is reserved for
  // genuinely compact domains, so a 13-record clinical domain can never crush
  // an adjacent two-record domain into the same ornamental circle.
  let pendingCompact: DomainEntry[] = []
  const flushCompact = () => {
    if (!pendingCompact.length) return
    const members = pendingCompact
    buckets.push({
      mode: 'shared',
      entries: members,
      radius: branchRadius('shared', members),
      hash: stableHash(members.map((entry) => entry.id).join('\u0000')),
    })
    pendingCompact = []
  }
  sharedEntries.forEach((entry) => {
    if (entry.members.length >= 7) {
      flushCompact()
      buckets.push({
        mode: 'shared',
        entries: [entry],
        radius: branchRadius('shared', [entry]),
        hash: entry.hash,
      })
      return
    }
    pendingCompact.push(entry)
    if (pendingCompact.length === SHARED_DOMAIN_BRANCH_CAPACITY) flushCompact()
  })
  flushCompact()

  return buckets.sort((left, right) =>
    left.radius - right.radius
      || left.mode.localeCompare(right.mode)
      || left.hash - right.hash,
  )
}

/**
 * Packs branch neighborhoods into a compact three-lane research tree. Later
 * rows route through the nearest previous-row junction instead of drawing a
 * crosshair from the locus to every leaf cluster. Compact lanes also keep a
 * framed locus useful at the AtlasView's 42% regional camera floor.
 */
function placeBranches(
  buckets: BranchBucket[],
  locusPoint: { x: number; y: number },
  groupAngle: number,
): BranchPlacement[] {
  const columns = 3
  const forwardStart = 255
  const rowStep = 245
  const tangentStep = 410

  return buckets.map((bucket, branchIndex) => {
    const row = Math.floor(branchIndex / columns)
    const rowStart = row * columns
    const rowCount = Math.min(columns, buckets.length - rowStart)
    const column = branchIndex - rowStart
    const baseTangent = (column - (rowCount - 1) / 2) * tangentStep
    // A slight deterministic bend stops rows reading as a diagramming-tool
    // grid while retaining predictable, inspectable world coordinates.
    const tangent = baseTangent + Math.sin((branchIndex + 1) * 1.91) * 24
    const forward = forwardStart + row * rowStep + Math.abs(tangent) * 0.055
    const home_x = locusPoint.x
      + Math.cos(groupAngle) * forward
      + Math.cos(groupAngle + Math.PI / 2) * tangent
    const home_y = locusPoint.y
      + Math.sin(groupAngle) * forward
      + Math.sin(groupAngle + Math.PI / 2) * tangent
    return {
      ...bucket,
      branchIndex,
      row,
      tangent,
      angle: Math.atan2(home_y - locusPoint.y, home_x - locusPoint.x),
      home_x,
      home_y,
    }
  })
}

/**
 * Builds a Path-of-Exile-style taxonomy in persistent world coordinates.
 *
 * Semantic hierarchy:
 * phenomenon (depth 0) -> broad locus (1) -> shared record.domain (2) -> record (3)
 * Singleton raw-domain labels remain record metadata but do not create a
 * redundant one-record gateway in the interactive hierarchy.
 *
 * Junctions are non-semantic travel nodes. They create readable shared paths
 * without inventing conceptual relationships between theories.
 */
export function buildAtlasGraph(records: TheoryRecord[]): AtlasGraphModel {
  const groups = orderedGroups(records)
  const groupCounts = Object.fromEntries(
    groups.map((group) => [group, records.filter((record) => macroGroup(record) === group).length]),
  )
  const nodes: GraphNode[] = [fixedNode({
    id: ATLAS_ROOT_ID,
    name: 'Consciousness',
    node_type: 'phenomenon',
    group: 'Target phenomenon',
    size: 23,
    depth: 0,
    structural: false,
    home_x: 0,
    home_y: 0,
  })]
  const links: GraphLink[] = []
  const locusIdByGroup: Record<string, string> = {}
  const domainIdByRecordId: Record<string, string> = {}
  const domainIdByKey: Record<string, string> = {}
  const recordIdsByDomainId: Record<string, string[]> = {}
  const groupDomainIds: Record<string, string[]> = {}
  const pathByRecordId: Record<string, string[]> = {}
  const semanticPathByRecordId: Record<string, string[]> = {}
  const domainCounts: Record<string, number> = {}
  const domains: AtlasDomainDescriptor[] = []
  // Canonical loci retain their compass slot even if a partial dataset omits
  // another locus; absent groups therefore leave a deliberate empty sector.
  const sectorSize = FULL_CIRCLE / Math.max(LOCUS_ORDER.length, groups.length, 1)
  // The half-sector rotation puts the two largest current loci on opposing
  // diagonals, preserving a balanced world silhouette without encoding rank.
  const startAngle = -Math.PI / 4

  groups.forEach((group, groupIndex) => {
    const canonicalIndex = (LOCUS_ORDER as readonly string[]).indexOf(group)
    const compassIndex = canonicalIndex >= 0 ? canonicalIndex : groupIndex
    const groupAngle = startAngle + compassIndex * sectorSize
    const locusId = locusNodeId(group)
    const locusPoint = point(LOCUS_RADIUS, groupAngle)
    locusIdByGroup[group] = locusId

    // Alternating bends avoid the generic straight-spoke appearance while
    // keeping every trunk inside its own compass sector.
    const bendDirection = groupIndex % 2 === 0 ? 1 : -1
    const trunkIds = TRUNK_RADII.map((radius, routeIndex) => {
      const bend = bendDirection * (routeIndex === 0 ? 0.075 : -0.045)
      const junctionPoint = point(radius, groupAngle + bend)
      const id = `junction-trunk-${slug(group)}-${routeIndex + 1}`
      nodes.push(fixedNode({
        id,
        name: `${group} route`,
        node_type: 'junction',
        group,
        size: routeIndex === 0 ? 2.7 : 3.1,
        depth: 1,
        parent_id: routeIndex === 0 ? ATLAS_ROOT_ID : `junction-trunk-${slug(group)}-${routeIndex}`,
        semantic_parent_id: ATLAS_ROOT_ID,
        structural: true,
        angle: groupAngle,
        home_x: junctionPoint.x,
        home_y: junctionPoint.y,
      }))
      return id
    })

    const trunkPath = [ATLAS_ROOT_ID, ...trunkIds, locusId]
    trunkPath.slice(0, -1).forEach((source, index) => {
      links.push({
        id: `link-trunk-${source}-${trunkPath[index + 1]}`,
        source,
        target: trunkPath[index + 1],
        kind: 'trunk',
        group,
        depth: 1,
      })
    })

    const groupRecords = records
      .filter((record) => macroGroup(record) === group)
      .sort((left, right) => left.id.localeCompare(right.id) || left.name.localeCompare(right.name))
    const groupedDomains = new Map<string, TheoryRecord[]>()
    groupRecords.forEach((record) => {
      const members = groupedDomains.get(record.domain) ?? []
      members.push(record)
      groupedDomains.set(record.domain, members)
    })
    const domainEntries = [...groupedDomains.entries()]
      .map(([domain, members]) => ({
        domain,
        members: members.sort((left, right) => left.id.localeCompare(right.id) || left.name.localeCompare(right.name)),
        id: domainNodeId(group, domain),
        hash: stableHash(taxonomyDomainKey(group, domain)),
      }))
      .sort((left, right) => left.hash - right.hash || left.domain.localeCompare(right.domain))

    nodes.push(fixedNode({
      id: locusId,
      name: group,
      node_type: 'locus',
      group,
      size: 15 + Math.min(groupRecords.length, 36) * 0.075,
      count: groupRecords.length,
      depth: 1,
      parent_id: trunkIds.at(-1) ?? ATLAS_ROOT_ID,
      semantic_parent_id: ATLAS_ROOT_ID,
      structural: false,
      angle: groupAngle,
      home_x: locusPoint.x,
      home_y: locusPoint.y,
    }))

    groupDomainIds[group] = []
    const branchPlacements = placeBranches(makeBranchBuckets(domainEntries), locusPoint, groupAngle)
    const hubIdByBranch: string[] = []
    const hubPathByBranch: string[][] = []
    const lastBranchRow = Math.max(0, ...branchPlacements.map((branch) => branch.row))

    branchPlacements.forEach((branch) => {
      const branchIndex = branch.branchIndex
      const hubId = `junction-hub-${hashToken(group)}-${hashToken(branch.entries.map((entry) => entry.id).join('\u0000'))}`
      const previousRowParent = branchPlacements
        .filter((candidate) => candidate.row === branch.row - 1)
        .sort((left, right) => Math.abs(left.tangent - branch.tangent) - Math.abs(right.tangent - branch.tangent))[0]
      const parentId = previousRowParent ? hubIdByBranch[previousRowParent.branchIndex] : locusId
      const parentPath = previousRowParent ? hubPathByBranch[previousRowParent.branchIndex] : trunkPath
      const physicalRoute = [...parentPath, hubId]
      const routeDistance = Math.hypot(branch.home_x - locusPoint.x, branch.home_y - locusPoint.y)
      nodes.push(fixedNode({
        id: hubId,
        name: branch.mode === 'shared' ? `${group} shared-domain branch` : `${group} singleton branch`,
        node_type: 'junction',
        group,
        size: branch.mode === 'shared' ? 3.4 : 2.8,
        depth: 2,
        parent_id: parentId,
        semantic_parent_id: locusId,
        structural: true,
        branch_index: branchIndex,
        ring_index: Math.max(0, Math.round((routeDistance - branch.radius) / 185)),
        angle: branch.angle,
        home_x: branch.home_x,
        home_y: branch.home_y,
      }))
      links.push({
        id: `link-branch-${parentId}-${hubId}`,
        source: parentId,
        target: hubId,
        kind: 'branch',
        group,
        depth: 2,
      })
      hubIdByBranch[branchIndex] = hubId
      hubPathByBranch[branchIndex] = physicalRoute

      // Shared domains and one-record source domains use separate branches.
      // This prevents singleton labels from being threaded through a large
      // domain constellation and makes each short branch serve one clear task.
      const side = branch.tangent < -80
        ? -1
        : branch.tangent > 80
          ? 1
          : (branch.row + groupIndex) % 2 === 0 ? -1 : 1
      // Intermediate clusters grow sideways from their route lane, preserving
      // a clean continuation to the next row. Terminal neighborhoods can open
      // forward into the unused end of the sector.
      const clusterAngle = branch.row === lastBranchRow
        ? branch.angle
        : groupAngle + side * Math.PI / 2
      const entryPlacements = branchEntryLayout(branch, clusterAngle)
      if (branch.mode === 'shared' && branch.row < lastBranchRow) {
        entryPlacements.forEach((placement, index) => {
          // Move the complete record lobe beyond the continuation lane, not
          // merely its domain node. Child-row routes can then pass the parent
          // hub without slicing through a theory or its label corridor.
          placement.radius = Math.max(
            placement.radius,
            domainNeighborhoodRadius(branch.entries[index].members.length) + 64,
          )
        })
      }
      branch.entries.forEach((entry, domainIndex) => {
        const entryPlacement = entryPlacements[domainIndex]
        const domainPoint = {
          x: branch.home_x + Math.cos(entryPlacement.angle) * entryPlacement.radius,
          y: branch.home_y + Math.sin(entryPlacement.angle) * entryPlacement.radius,
        }
        const domainAngle = Math.atan2(domainPoint.y - locusPoint.y, domainPoint.x - locusPoint.x)
        const domainId = entry.id
        const recordIds = entry.members.map((record) => record.id)
        const domainKey = taxonomyDomainKey(group, entry.domain)

        // Most imported domain strings currently identify a single catalog
        // record. Preserve that source label on the record, but skip a visually
        // and interactively redundant domain -> record hop until a second member
        // gives the domain genuine grouping utility.
        if (entry.members.length === 1) {
          const record = entry.members[0]
          nodes.push(fixedNode({
            id: record.id,
            name: record.name,
            node_type: 'record',
            group,
            domain: record.domain,
            kind: record.kind,
            status: record.status,
            size: 6.2,
            citation_count: record.citations.length,
            depth: 2,
            parent_id: hubId,
            semantic_parent_id: locusId,
            structural: false,
            branch_index: branchIndex,
            ring_index: entryPlacement.ring,
            angle: domainAngle,
            home_x: domainPoint.x,
            home_y: domainPoint.y,
          }))
          links.push({
            id: `link-classification-${hubId}-${record.id}`,
            source: hubId,
            target: record.id,
            kind: 'classification',
            group,
            domain: record.domain,
            depth: 2,
          })
          pathByRecordId[record.id] = [...physicalRoute, record.id]
          semanticPathByRecordId[record.id] = [ATLAS_ROOT_ID, locusId, record.id]
          return
        }

        domainIdByKey[domainKey] = domainId
        recordIdsByDomainId[domainId] = recordIds
        groupDomainIds[group].push(domainId)
        domainCounts[domainId] = entry.members.length
        domains.push({
          id: domainId,
          name: entry.domain,
          group,
          count: entry.members.length,
          recordIds,
          branchIndex,
          home_x: domainPoint.x,
          home_y: domainPoint.y,
        })
        nodes.push(fixedNode({
          id: domainId,
          name: entry.domain,
          node_type: 'domain',
          group,
          domain: entry.domain,
          size: 9.5 + Math.min(entry.members.length, 8) * 0.55,
          count: entry.members.length,
          depth: 2,
          parent_id: hubId,
          semantic_parent_id: locusId,
          structural: false,
          branch_index: branchIndex,
          ring_index: entryPlacement.ring,
          angle: domainAngle,
          home_x: domainPoint.x,
          home_y: domainPoint.y,
        }))
        links.push({
          id: `link-branch-${hubId}-${domainId}`,
          source: hubId,
          target: domainId,
          kind: 'branch',
          group,
          domain: entry.domain,
          depth: 2,
        })

        const incomingDomainAngle = entryPlacement.angle + Math.PI
        const recordPlacements = recordLobeLayout(entry.members.length, domainAngle, incomingDomainAngle)
        entry.members.forEach((record, recordIndex) => {
          const recordPlacement = recordPlacements[recordIndex]
          const recordPoint = {
            x: domainPoint.x + Math.cos(recordPlacement.angle) * recordPlacement.radius,
            y: domainPoint.y + Math.sin(recordPlacement.angle) * recordPlacement.radius,
          }
          nodes.push(fixedNode({
            id: record.id,
            name: record.name,
            node_type: 'record',
            group,
            domain: record.domain,
            kind: record.kind,
            status: record.status,
            size: 6.2,
            citation_count: record.citations.length,
            depth: 3,
            parent_id: domainId,
            semantic_parent_id: domainId,
            structural: false,
            branch_index: branchIndex,
            ring_index: recordPlacement.ring,
            angle: recordPlacement.angle,
            home_x: recordPoint.x,
            home_y: recordPoint.y,
          }))
          links.push({
            id: `link-classification-${domainId}-${record.id}`,
            source: domainId,
            target: record.id,
            kind: 'classification',
            group,
            domain: record.domain,
            depth: 3,
          })
          domainIdByRecordId[record.id] = domainId
          pathByRecordId[record.id] = [...physicalRoute, domainId, record.id]
          semanticPathByRecordId[record.id] = [ATLAS_ROOT_ID, locusId, domainId, record.id]
        })
      })
    })
  })

  return {
    nodes,
    links,
    groups,
    groupCounts,
    domainCounts,
    locusIdByGroup,
    domainIdByRecordId,
    domainIdByKey,
    recordIdsByDomainId,
    groupDomainIds,
    pathByRecordId,
    semanticPathByRecordId,
    domains,
    bounds: calculateBounds(nodes),
  }
}

export function endpointId(endpoint: string | number | { id?: string | number } | undefined): string {
  if (endpoint && typeof endpoint === 'object') return String(endpoint.id)
  return String(endpoint ?? '')
}
