import { useEffect, useState } from 'react'
import { loadProfileQuality } from '../api'
import type { ProfileQualityReport } from '../types'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { CoverageResponse } from '../types'

export function CoverageView({ coverage, onInspectRecord }: {
  coverage: CoverageResponse
  onInspectRecord?: (recordId: string) => void
}) {
  const [quality, setQuality] = useState<ProfileQualityReport | null>(null)
  const [qualityError, setQualityError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    loadProfileQuality(controller.signal)
      .then((report) => {
        if (!controller.signal.aborted) setQuality(report)
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setQualityError(reason instanceof Error ? reason.message : 'Profile audit unavailable.')
        }
      })
    return () => controller.abort()
  }, [])

  return (
    <section className="coverage-view view-frame" aria-labelledby="coverage-title">
      <h1 id="coverage-title" className="sr-only">Collection audit</h1>

      <div className="coverage-scroll">
        <section className="coverage-priority" aria-label="Collection metrics">
          <div className="coverage-metrics">
            <article><span>Records</span><strong>{coverage.record_count}</strong><small>typed, cited entries</small></article>
            <article><span>Source records</span><strong>{coverage.source_count}</strong><small>{coverage.citation_count} retained citations</small></article>
            <article><span>Primary reach</span><strong>{coverage.primary_source_percent}%</strong><small>original or self-exposition</small></article>
            <article><span>Human review</span><strong>{coverage.human_verified_percent}%</strong><small>metadata independently matched</small></article>
          </div>
        </section>
        <p className="coverage-notice">{coverage.notice}</p>

        <section className="protocol-card profile-quality-audit" aria-labelledby="profile-quality-title">
          <header><h2 id="profile-quality-title">Research profile depth</h2></header>
          {quality ? (
            <>
              <div className="profile-quality-summary">
                <div>
                  <strong>{quality.summary.complete_profiles} of {quality.summary.record_count}</strong>
                  <span>records with all four research-profile fields</span>
                </div>
                <div>
                  <strong>{quality.summary.incomplete_profiles}</strong>
                  <span>records needing editorial enrichment</span>
                </div>
                <div>
                  <strong>{quality.summary.completion_percent}%</strong>
                  <span>field completeness, not evidential verification</span>
                </div>
              </div>
              <p className="profile-quality-caveat">{quality.limitations}</p>
              <div className="profile-quality-kinds">
                {quality.by_kind.map((row) => (
                  <div key={row.kind}>
                    <span>{row.kind}</span>
                    <strong>{row.complete_profiles}/{row.records}</strong>
                    <small>{row.incomplete_profiles} incomplete</small>
                  </div>
                ))}
              </div>
              {quality.backlog.length > 0 && (
                <details className="profile-quality-backlog">
                  <summary>Open prioritized editorial queue ({quality.backlog.length} records)</summary>
                  <p>Priority reflects missing fields and source-metadata follow-up, not scientific importance. Select a record to inspect its existing citations.</p>
                  <ol>
                    {quality.backlog.slice(0, 15).map((item) => (
                      <li key={item.id}>
                        <button type="button" disabled={!onInspectRecord} onClick={() => onInspectRecord?.(item.id)}>
                          {item.name}
                        </button>
                        <small>{item.kind} · {item.missing_field_count} missing fields · {item.pending_metadata_citations} pending citation metadata</small>
                      </li>
                    ))}
                  </ol>
                </details>
              )}
            </>
          ) : (
            <p className="profile-quality-caveat" role="status">
              {qualityError ? `Current profile audit unavailable: ${qualityError}` : 'Loading research profile quality…'}
              {' '}The existing collection metrics remain available.
            </p>
          )}
        </section>

        <section className="coverage-work" aria-label="Coverage blockers and evidence">
          <article className="protocol-card coverage-blockers">
            <header><h2>Requirements before synthesis</h2></header>
            <ul>
              {coverage.gate_requirements.map((requirement, index) => (
                <li key={requirement}><b>{String(index + 1).padStart(2, '0')}</b><span>{requirement}</span></li>
              ))}
            </ul>
          </article>

          <article className="frames-card coverage-frames">
            <header><h2>Discovery frames</h2></header>
            <div className="frame-list">
              {coverage.discovery_frames.map((frame) => {
                const progress = frame.target ? Math.min(100, Math.round(100 * (frame.screened ?? 0) / frame.target)) : 0
                const detail = frame.indexed
                  ? `${frame.type} · ${frame.indexed} indexed${frame.likely_present !== undefined ? ` · ${frame.likely_present} strong title candidates` : ''}${frame.identity_review !== undefined ? ` · ${frame.identity_review} require identity review` : ''}${frame.unmatched !== undefined ? ` · ${frame.unmatched} without a title candidate` : ''}`
                  : frame.type
                return <div className="frame-row" key={frame.name}><span className={`frame-status ${frame.status}`} /><div><strong>{frame.name}</strong><small>{detail}</small></div><div className="frame-progress"><span style={{ width: `${progress}%` }} /></div><b>{frame.status}</b></div>
              })}
            </div>
          </article>

          <article className="chart-card coverage-domain-chart">
            <header><h2>Records by domain</h2></header>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={coverage.by_domain.slice(0, 10)} layout="vertical" margin={{ left: 6, right: 24, top: 6, bottom: 6 }}>
                  <CartesianGrid stroke="#d8d3c8" horizontal={false} />
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" width={164} tick={{ fill: '#555951', fontSize: 9 }} tickFormatter={(value: string) => value.length > 25 ? `${value.slice(0, 24)}…` : value} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: '#ebe7de' }} contentStyle={{ color: '#171915', background: '#fbfaf6', border: '1px solid #171915', borderRadius: 0, fontSize: 10 }} />
                  <Bar dataKey="value" fill="#263fc0" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </article>
        </section>
      </div>
    </section>
  )
}
