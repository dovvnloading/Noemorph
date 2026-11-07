export type RecordKind =
  | 'Scientific theory'
  | 'Philosophical position'
  | 'Model or framework'
  | 'Historical tradition'
  | 'Phenomenological construct'
  | 'Clinical / state model'
  | 'Theory of mind / social cognition'
  | 'Argument / challenge'
  | 'Speculative hypothesis'

export interface Citation {
  source_id?: string
  source_uid?: string
  title: string
  authors: string
  year: number | string
  url: string
  doi?: string
  venue?: string
  authority: string
  verification?: 'doi-resolved' | 'locator-recorded' | 'human-verified' | 'pending-metadata-review'
  note?: string
  retrieved?: string
}

export interface ClaimReviewLead {
  citation_url: string
  source_uid: string
  locator_kind: 'source-url-only'
  review_state: 'unreviewed'
}

export interface ClaimReview {
  id: string
  kind: 'scope' | 'boundary'
  field: string
  text: string
  citations: ClaimReviewLead[]
  review_state: 'unreviewed'
}

export type ClaimEvidenceDecision =
  | 'supports' | 'challenges' | 'contextualizes' | 'inconclusive' | 'not-relevant'

export interface ClaimEvidenceEvent {
  event_id: string
  record_id: string
  claim_id: string
  claim_hash: string
  source_uid: string
  citation_url: string
  reviewer_id: string
  decision: ClaimEvidenceDecision
  locator_kind: string
  locator: string
  excerpt: string | null
  note: string
  created_at: string
  event_hash: string
  previous_hash: string
  current: boolean
}

export interface ClaimEvidenceHistory {
  record_id: string
  claim_id: string
  claim_text: string
  claim_hash: string
  database_state: 'absent' | 'ready'
  publication_state: 'review-only'
  relationships_locked: true
  identity_note: string
  sources: Array<{
    source_uid: string
    citation_url: string
    status: string
    active_reviewer_count: number
    distinct_decisions: ClaimEvidenceDecision[]
    recorded_agreement_is_not_verification: true
  }>
  events: ClaimEvidenceEvent[]
}

export type ResearchProfileValue =
  | string
  | string[]
  | Record<string, string | string[]>

export interface TheoryRecord {
  id: string
  name: string
  aliases?: string[]
  kind: RecordKind | string
  domain: string
  tradition: string
  status: string
  status_note?: string
  summary: string
  proponents: string[]
  year?: number | string
  era?: string
  scope?: string
  claim_scope?: ResearchProfileValue
  boundary_note?: string
  evidence_profile?: ResearchProfileValue
  open_questions?: string[]
  commitments?: string[]
  mechanism?: string
  keywords?: string[]
  citations: Citation[]
  claim_reviews?: ClaimReview[]
  review_state?: 'verified-seed' | 'provisional' | 'needs-review'
}

export interface CatalogResponse {
  items: TheoryRecord[]
  total: number
  offset: number
  limit: number
}

export interface SourceUse {
  record_id: string
  authority: string
  verification: NonNullable<Citation['verification']>
  url: string
}

// Bibliographic source metadata is distinct from a citation's role and review state.
export interface SourceMetadataVariant {
  title: string
  authors: string
  year: number | string
  url: string
  doi: string | null
  venue: string | null
  retrieved: string | null
  record_ids: string[]
}

export interface SourceRecord extends Omit<Citation, 'authority' | 'verification'> {
  id: string
  source_uid: string
  used_by: string[]
  uses: SourceUse[]
  authority_roles: string[]
  verification_states: Array<NonNullable<Citation['verification']>>
  /** Bibliography review leads; never evidence or claim-verification states. */
  work_identity_review_state: 'unreviewed' | 'needs-review'
  metadata_conflict_fields: Array<'title' | 'year'>
  metadata_variants: SourceMetadataVariant[]
}

export interface SourcesResponse {
  items: SourceRecord[]
  total: number
}

export interface DiscoveryProponent {
  name: string
  role: string
  same_as: string[]
}

export interface DiscoveryReference {
  label: string
  authors: string
  title: string
  container: string
  locators: string[]
}

export interface DiscoveryEntry {
  slug: string
  name: string
  url: string
  entry_type: 'theory' | 'overview' | 'collection'
  category: string
  description: string
  term_code?: string
  modified_at?: string
  verified_by_source: boolean
  proponents: DiscoveryProponent[]
  key_takeaways: Array<{ label: string; text: string }>
  references: DiscoveryReference[]
  catalog_match: {
    status: 'likely-present' | 'possible-match' | 'not-matched' | 'not-applicable'
    record_id?: string
    record_name?: string
    score: number
    basis?: 'full-title' | 'possessive-prefix-stripped' | 'not-applicable' | string
  }
}

export interface DiscoveryResponse {
  items: DiscoveryEntry[]
  total: number
  offset: number
  limit: number
  collection: {
    name: string
    source: string
    retrieved: string
    role: string
    source_verification_note: string
    people_note: string
    catalog_match_note: string
    reference_note: string
    entry_count: number
    error_count: number
    catalog_match_counts: Record<string, number>
  }
}

export interface CountDatum {
  name: string
  value: number
}

export interface DiscoveryFrame {
  name: string
  type: string
  status: string
  screened?: number
  target?: number
  indexed?: number
  unmatched?: number
  identity_review?: number
  likely_present?: number
  not_applicable?: number
}

export interface CoverageResponse {
  phase: string
  gate_state: string
  readiness_percent?: number
  record_count: number
  source_count: number
  citation_count: number
  full_research_profile_count: number
  research_profile_gap_count: number
  human_verified_percent: number
  locator_coverage_percent: number
  primary_source_percent: number
  by_kind: CountDatum[]
  by_domain: CountDatum[]
  by_status: CountDatum[]
  by_tradition: CountDatum[]
  discovery_frames: DiscoveryFrame[]
  discovery_registry?: DiscoveryResponse['collection']
  gate_requirements: string[]
  notice: string
}

export interface ProfileQualityGap {
  id: string
  name: string
  kind: string
  domain: string
  missing_fields: string[]
  missing_field_count: number
  pending_metadata_citations: number
  has_primary_citation: boolean
  citation_count: number
  triage_priority: number
}

export interface ProfileQualityReport {
  schema_version: number
  catalog_version: string
  corpus_date: string
  method: string
  limitations: string
  required_profile_fields: string[]
  triage_formula: string
  summary: {
    record_count: number
    complete_profiles: number
    incomplete_profiles: number
    completion_percent: number
    citation_occurrences: number
    citation_verification_counts: Record<string, number>
    missing_required_field_counts: Record<string, number>
  }
  by_kind: Array<{
    kind: string
    records: number
    complete_profiles: number
    incomplete_profiles: number
    records_with_pending_citations: number
    records_with_no_primary_anchor: number
  }>
  backlog: ProfileQualityGap[]
}

export interface CatalogMetadata {
  title: string
  version: string
  generated_at: string
  phase: string
  coverage_gate: string
  readiness_percent: number
  methodology: string
  coverage_notice: string
  [key: string]: unknown
}

export interface GraphNode {
  id: string
  name: string
  node_type: 'phenomenon' | 'locus' | 'domain' | 'record' | 'junction'
  group: string
  domain?: string
  kind?: string
  status?: string
  size: number
  count?: number
  citation_count?: number
  depth?: 0 | 1 | 2 | 3
  parent_id?: string
  semantic_parent_id?: string
  structural?: boolean
  branch_index?: number
  ring_index?: number
  angle?: number
  home_x?: number
  home_y?: number
  x?: number
  y?: number
  vx?: number
  vy?: number
  fx?: number
  fy?: number
}

export interface GraphLink {
  id?: string
  source: string
  target: string
  /** `organizational` remains accepted for stored legacy graphs. */
  kind: 'trunk' | 'branch' | 'classification' | 'organizational'
  group?: string
  domain?: string
  depth?: 1 | 2 | 3
}

export interface TaxonomyGraph {
  nodes: GraphNode[]
  links: GraphLink[]
  edge_policy: string
}

export type SemanticDisposition = 'unreviewed' | 'shortlisted' | 'needs-review' | 'dismissed'

export type SemanticRelationTag =
  | 'possible-convergence'
  | 'possible-contrast'
  | 'shared-mechanism'
  | 'shared-phenomenology'
  | 'shared-method'
  | 'possible-lineage'
  | 'terminological-overlap'
  | 'artifact-risk'

export interface SemanticRecordReference {
  id: string
  name: string
  kind?: string
  domain?: string
  tradition?: string
  summary?: string
}

export interface SemanticRun {
  id: string
  created_at: string
  model: {
    provider: string
    name: string
    digest: string
    dimensions: number
    [key: string]: unknown
  }
  catalog_hash: string
  catalog_version: string
  recipe: {
    metric?: string
    version?: string
    [key: string]: unknown
  }
  record_count: number
  candidate_count: number
  state: 'building' | 'complete' | 'failed' | string
}

export interface SemanticFieldContribution {
  signal?: string
  field_a: string
  field_b: string
  score: number
  percentile?: number
  source_rank?: number
  target_rank?: number
  excerpt_a: string
  excerpt_b: string
  input_hash_a?: string
  input_hash_b?: string
  attribution_note?: string
}

export interface SemanticPriorArtSource {
  title: string
  authors: string
  year: number | string
  url: string
  role: string
}

export interface SemanticPriorArtScreen {
  record_ids: [string, string]
  status: string
  direct_comparison: string
  assessment: string
  caution: string
  recommended_relation_tag?: SemanticRelationTag
  sources: SemanticPriorArtSource[]
}

export interface SemanticCandidateSummary {
  id: string
  record_a: SemanticRecordReference
  record_b: SemanticRecordReference
  semantic_similarity: number
  similarity_percentile?: number
  review_priority?: number
  mutual_rank?: number
  cross_domain?: boolean
  cross_tradition?: boolean
  flags?: string[]
  source_overlap_count?: number
  proponent_overlap_count?: number
  disposition?: SemanticDisposition
  relation_tag?: SemanticRelationTag
  reviewer_note?: string
  updated_at?: string
}

export interface SemanticCandidateDetail extends SemanticCandidateSummary {
  field_contributions?: SemanticFieldContribution[]
  prior_art?: SemanticPriorArtScreen
  run?: SemanticRun
  prior_art_status?: 'not-checked' | 'in-review' | 'known' | 'screened-no-hit' | string
  interpretation_policy?: string
  relationship_synthesis_locked?: boolean
}

export interface SemanticCandidatesResponse {
  items: SemanticCandidateSummary[]
  total: number
  offset: number
  limit: number
  run_id?: string
  relationship_synthesis_locked?: boolean
}

export interface SemanticStatus {
  ready: boolean
  state: 'absent' | 'empty' | 'building' | 'failed' | 'stale' | 'invalid' | 'ready' | string
  detail: string
  schema_version: number
  catalog: {
    version: string
    record_count: number
    fingerprint: string
  }
  run?: SemanticRun | null
  counts: {
    total: number
    by_disposition: Record<string, number>
    by_relation_tag: Record<string, number>
  }
  relationship_synthesis_locked: boolean
}

export interface SemanticReviewUpdate {
  disposition: Exclude<SemanticDisposition, 'unreviewed'>
  relation_tag?: SemanticRelationTag
  reviewer_note?: string
}

export type ViewKey = 'atlas' | 'catalog' | 'relations' | 'sources' | 'coverage' | 'methods'
