import type {
  CatalogMetadata,
  CatalogResponse,
  CoverageResponse,
  ProfileQualityReport,
  ClaimEvidenceHistory,
  DiscoveryResponse,
  SemanticCandidateDetail,
  SemanticPriorArtScreen,
  SemanticCandidateSummary,
  SemanticCandidatesResponse,
  SemanticFieldContribution,
  SemanticReviewUpdate,
  SemanticRun,
  SemanticStatus,
  SourcesResponse,
} from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })
  if (!response.ok) {
    const body = await response.text()
    let detail = body
    try {
      const parsed = JSON.parse(body) as { detail?: string }
      detail = parsed.detail ?? body
    } catch {
      // Preserve non-JSON service responses as written.
    }
    throw new Error(detail || `Request failed with ${response.status}`)
  }
  return response.json() as Promise<T>
}

export async function loadCatalog(signal?: AbortSignal): Promise<CatalogResponse> {
  const pageSize = 1000
  const items: CatalogResponse['items'] = []
  let offset = 0
  let total = Number.POSITIVE_INFINITY

  while (items.length < total) {
    const page = await request<CatalogResponse>(`/api/catalog?offset=${offset}&limit=${pageSize}`, { signal })
    items.push(...page.items)
    total = page.total
    offset += page.items.length
    if (page.items.length === 0) break
  }

  return { items, total: Number.isFinite(total) ? total : items.length, offset: 0, limit: items.length }
}

export async function loadDiscovery(): Promise<DiscoveryResponse> {
  const pageSize = 1000
  const items: DiscoveryResponse['items'] = []
  let offset = 0
  let total = Number.POSITIVE_INFINITY
  let collection: DiscoveryResponse['collection'] | undefined

  while (items.length < total) {
    const page = await request<DiscoveryResponse>(`/api/discovery/closer-to-truth?offset=${offset}&limit=${pageSize}`)
    items.push(...page.items)
    total = page.total
    collection = page.collection
    offset += page.items.length
    if (page.items.length === 0) break
  }

  if (!collection) throw new Error('Discovery registry metadata is unavailable')
  return { items, collection, total: Number.isFinite(total) ? total : items.length, offset: 0, limit: items.length }
}

export interface SemanticCandidateQuery {
  disposition?: 'unreviewed' | 'shortlisted' | 'needs-review' | 'dismissed'
  focus?: 'cross-domain' | 'cross-tradition' | 'all'
  q?: string
  minPriority?: number
  offset?: number
  limit?: number
  signal?: AbortSignal
}

export function loadSemanticStatus(signal?: AbortSignal): Promise<SemanticStatus> {
  return request<SemanticStatus>('/api/semantic/status', { signal })
}

export function loadSemanticCandidates({
  disposition = 'unreviewed',
  focus = 'cross-domain',
  q,
  minPriority = 0.75,
  offset = 0,
  limit = 40,
  signal,
}: SemanticCandidateQuery = {}): Promise<SemanticCandidatesResponse> {
  const params = new URLSearchParams({
    disposition,
    min_priority: String(minPriority),
    offset: String(offset),
    limit: String(limit),
  })
  if (focus === 'cross-domain') params.set('cross_domain', 'true')
  if (focus === 'cross-tradition') params.set('cross_tradition', 'true')
  if (q?.trim()) params.set('q', q.trim())
  return request<SemanticCandidatesResponse>(`/api/semantic/candidates?${params.toString()}`, { signal })
}

interface SemanticDetailEnvelope {
  candidate: SemanticCandidateSummary & {
    contributions?: SemanticFieldContribution[] | {
      field_contributions?: SemanticFieldContribution[]
      prior_art?: SemanticPriorArtScreen
    }
  }
  run: SemanticRun
  interpretation_policy: string
  relationship_synthesis_locked: boolean
}

function normalizeSemanticDetail(payload: SemanticDetailEnvelope): SemanticCandidateDetail {
  const contributions = payload.candidate.contributions
  const fieldContributions = Array.isArray(contributions)
    ? contributions
    : contributions?.field_contributions ?? []
  return {
    ...payload.candidate,
    field_contributions: fieldContributions,
    prior_art: Array.isArray(contributions) ? undefined : contributions?.prior_art,
    run: payload.run,
    interpretation_policy: payload.interpretation_policy,
    relationship_synthesis_locked: payload.relationship_synthesis_locked,
  }
}

export async function loadSemanticCandidate(candidateId: string, signal?: AbortSignal): Promise<SemanticCandidateDetail> {
  const payload = await request<SemanticDetailEnvelope>(`/api/semantic/candidates/${encodeURIComponent(candidateId)}`, { signal })
  return normalizeSemanticDetail(payload)
}

export async function updateSemanticReview(candidateId: string, review: SemanticReviewUpdate): Promise<SemanticCandidateDetail> {
  const payload = await request<SemanticDetailEnvelope>(`/api/semantic/candidates/${encodeURIComponent(candidateId)}`, {
    method: 'PATCH',
    body: JSON.stringify(review),
  })
  return normalizeSemanticDetail(payload)
}

export function loadClaimEvidenceHistory(
  recordId: string,
  claimId: string,
  signal?: AbortSignal,
): Promise<ClaimEvidenceHistory> {
  return request<ClaimEvidenceHistory>(
    `/api/claim-evidence/records/${encodeURIComponent(recordId)}/claims/${encodeURIComponent(claimId)}`,
    { signal },
  )
}

export function loadProfileQuality(signal?: AbortSignal): Promise<ProfileQualityReport> {
  return request<ProfileQualityReport>('/api/profile-quality', { signal })
}

// The catalog is the only required workspace request. Supplemental panels
// load independently when opened, so their failure never blocks reading records.
export function loadSources(signal?: AbortSignal): Promise<SourcesResponse> {
  return request<SourcesResponse>('/api/sources', { signal })
}

export function loadCoverage(signal?: AbortSignal): Promise<CoverageResponse> {
  return request<CoverageResponse>('/api/coverage', { signal })
}

export function loadMetadata(signal?: AbortSignal): Promise<CatalogMetadata> {
  return request<CatalogMetadata>('/api/meta', { signal })
}
