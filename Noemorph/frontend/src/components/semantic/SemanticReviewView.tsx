import { useCallback, useEffect, useState } from 'react'
import {
  loadSemanticCandidate,
  loadSemanticCandidates,
  loadSemanticStatus,
  updateSemanticReview,
} from '../../api'
import type {
  SemanticCandidateDetail,
  SemanticCandidateSummary,
  SemanticReviewUpdate,
  SemanticStatus,
  TheoryRecord,
} from '../../types'
import { SemanticCandidateQueue } from './SemanticCandidateQueue'
import { SemanticPairComparison } from './SemanticPairComparison'
import './semantic-review.css'

type QueueState = 'unreviewed' | 'shortlisted' | 'needs-review' | 'dismissed'
type Focus = 'cross-domain' | 'cross-tradition' | 'all'

const PAGE_SIZE = 40

const STATE_TABS: Array<{ value: QueueState; label: string }> = [
  { value: 'unreviewed', label: 'New' },
  { value: 'shortlisted', label: 'Shortlisted' },
  { value: 'needs-review', label: 'Needs review' },
  { value: 'dismissed', label: 'Dismissed' },
]

interface SemanticReviewViewProps {
  records: TheoryRecord[]
  query: string
  onOpenRecord: (record: TheoryRecord) => void
}

function isAbort(reason: unknown): boolean {
  return reason instanceof DOMException && reason.name === 'AbortError'
}

export function SemanticReviewView({ records, query, onOpenRecord }: SemanticReviewViewProps) {
  const [status, setStatus] = useState<SemanticStatus>()
  const [statusState, setStatusState] = useState<'loading' | 'ready' | 'error'>('loading')
  const [statusError, setStatusError] = useState<string>()
  const [queueState, setQueueState] = useState<QueueState>('unreviewed')
  const [focus, setFocus] = useState<Focus>('cross-domain')
  const [minimumPriority, setMinimumPriority] = useState(0.75)
  const [offset, setOffset] = useState(0)
  const [items, setItems] = useState<SemanticCandidateSummary[]>([])
  const [total, setTotal] = useState(0)
  const [queueLoading, setQueueLoading] = useState(false)
  const [queueError, setQueueError] = useState<string>()
  const [queueRevision, setQueueRevision] = useState(0)
  const [selectedId, setSelectedId] = useState<string>()
  const [detail, setDetail] = useState<SemanticCandidateDetail>()
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<string>()
  const [detailRevision, setDetailRevision] = useState(0)
  const [reviewPending, setReviewPending] = useState(false)
  const [reviewError, setReviewError] = useState<string>()

  const refreshStatus = useCallback(() => {
    const controller = new AbortController()
    setStatusState('loading')
    setStatusError(undefined)
    loadSemanticStatus(controller.signal)
      .then((response) => {
        setStatus(response)
        setStatusState('ready')
      })
      .catch((reason: unknown) => {
        if (isAbort(reason)) return
        setStatusError(reason instanceof Error ? reason.message : 'The semantic index status could not be read.')
        setStatusState('error')
      })
    return () => controller.abort()
  }, [])

  useEffect(() => refreshStatus(), [refreshStatus])

  useEffect(() => {
    setOffset(0)
    setSelectedId(undefined)
    setDetail(undefined)
    setDetailError(undefined)
  }, [focus, minimumPriority, query, queueState])

  useEffect(() => {
    if (statusState !== 'ready' || status?.ready === false) return
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      setQueueLoading(true)
      setQueueError(undefined)
      loadSemanticCandidates({
        disposition: queueState,
        focus,
        q: query,
        minPriority: minimumPriority,
        offset,
        limit: PAGE_SIZE,
        signal: controller.signal,
      })
        .then((response) => {
          setItems(response.items)
          setTotal(response.total)
        })
        .catch((reason: unknown) => {
          if (isAbort(reason)) return
          setQueueError(reason instanceof Error ? reason.message : 'The semantic candidate queue could not be read.')
        })
        .finally(() => {
          if (!controller.signal.aborted) setQueueLoading(false)
        })
    }, 180)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [focus, minimumPriority, offset, query, queueRevision, queueState, status?.ready, statusState])

  useEffect(() => {
    if (!selectedId) {
      setDetail(undefined)
      return
    }
    const controller = new AbortController()
    setDetailLoading(true)
    setDetailError(undefined)
    setReviewError(undefined)
    loadSemanticCandidate(selectedId, controller.signal)
      .then(setDetail)
      .catch((reason: unknown) => {
        if (isAbort(reason)) return
        setDetailError(reason instanceof Error ? reason.message : 'The selected candidate could not be read.')
      })
      .finally(() => {
        if (!controller.signal.aborted) setDetailLoading(false)
      })
    return () => controller.abort()
  }, [detailRevision, selectedId])

  const selectCandidate = (candidate: SemanticCandidateSummary) => {
    setSelectedId(candidate.id)
    setDetail(undefined)
  }

  const submitReview = async (review: SemanticReviewUpdate) => {
    if (!selectedId) return
    setReviewPending(true)
    setReviewError(undefined)
    try {
      const updated = await updateSemanticReview(selectedId, review)
      setDetail((current) => current ? { ...current, ...updated } : updated)
      setItems((current) => current.filter((candidate) => candidate.id !== selectedId))
      setTotal((current) => Math.max(0, current - 1))
      setQueueRevision((current) => current + 1)
    } catch (reason: unknown) {
      setReviewError(reason instanceof Error ? reason.message : 'The review disposition could not be saved.')
    } finally {
      setReviewPending(false)
    }
  }

  const statusText = status?.state === 'ready' && status.run
    ? `Local index · ${status.run.model.name} · ${new Date(status.run.created_at).toLocaleDateString()}`
    : status?.detail ?? 'Local semantic index status unavailable.'

  if (statusState === 'loading') {
    return <div className="semantic-service-state"><strong>Reading semantic index</strong><p>Checking the local analysis run and review ledger.</p></div>
  }

  if (statusState === 'error') {
    return (
      <div className="semantic-service-state" role="alert">
        <strong>Semantic review unavailable</strong>
        <p>{statusError}</p>
        <button type="button" onClick={refreshStatus}>Retry</button>
      </div>
    )
  }

  if (status?.ready === false) {
    return (
      <div className="semantic-service-state">
        <strong>{status.state === 'building' ? 'Building local semantic index' : 'No current semantic index is available'}</strong>
        <p>{statusText}</p>
        <button type="button" onClick={refreshStatus}>Refresh status</button>
      </div>
    )
  }

  return (
    <section className={`semantic-review-workspace ${selectedId ? 'detail-open' : ''}`} aria-labelledby="semantic-review-title">
      <h1 id="semantic-review-title" className="sr-only">Relationship review</h1>
      <header className="semantic-review-toolbar">
        <div className="semantic-state-tabs" role="tablist" aria-label="Review disposition">
          {STATE_TABS.map((tab) => (
            <button
              type="button"
              role="tab"
              aria-selected={queueState === tab.value}
              className={queueState === tab.value ? 'active' : ''}
              key={tab.value}
              onClick={() => setQueueState(tab.value)}
            >{tab.label}{status?.counts.by_disposition[tab.value] !== undefined ? <small>{status.counts.by_disposition[tab.value]}</small> : null}</button>
          ))}
        </div>
        <label className="semantic-focus-control">
          <span>Focus</span>
          <select value={focus} onChange={(event) => setFocus(event.target.value as Focus)}>
            <option value="cross-domain">Cross-domain</option>
            <option value="cross-tradition">Cross-tradition</option>
            <option value="all">All candidates</option>
          </select>
        </label>
        <details className="semantic-filter-control">
          <summary>Filters</summary>
          <div>
            <label>
              <span>Minimum review priority</span>
              <select value={minimumPriority} onChange={(event) => setMinimumPriority(Number(event.target.value))}>
                <option value={0.9}>Very high · 90%</option>
                <option value={0.75}>High · 75%</option>
                <option value={0.5}>Moderate · 50%</option>
                <option value={0}>All retained candidates</option>
              </select>
            </label>
          </div>
        </details>
        <p className={status?.state === 'stale' ? 'semantic-index-note warning' : 'semantic-index-note'}>{statusText}</p>
      </header>

      {queueError ? (
        <div className="semantic-service-state" role="alert">
          <strong>Candidate queue unavailable</strong>
          <p>{queueError}</p>
          <button type="button" onClick={() => setQueueRevision((current) => current + 1)}>Retry</button>
        </div>
      ) : (
        <div className="semantic-review-body">
          <SemanticCandidateQueue
            items={items}
            total={total}
            offset={offset}
            limit={PAGE_SIZE}
            selectedId={selectedId}
            loading={queueLoading}
            onSelect={selectCandidate}
            onPageChange={(nextOffset) => {
              setOffset(nextOffset)
              setSelectedId(undefined)
              setDetail(undefined)
            }}
          />
          <SemanticPairComparison
            candidate={detail}
            records={records}
            loading={detailLoading}
            error={detailError}
            reviewPending={reviewPending}
            reviewError={reviewError}
            onRetry={() => setDetailRevision((current) => current + 1)}
            onOpenRecord={onOpenRecord}
            onReview={submitReview}
            onBack={() => {
              setSelectedId(undefined)
              setDetail(undefined)
            }}
          />
        </div>
      )}
    </section>
  )
}
