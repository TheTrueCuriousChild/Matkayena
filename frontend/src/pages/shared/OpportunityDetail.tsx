import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getOpportunity } from '../../api/opportunities';
import { formatCurrency, formatDate, capitalize } from '../../utils/format';
import type { Opportunity } from '../../types';

export default function OpportunityDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [opp, setOpp] = useState<Opportunity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    getOpportunity(id)
      .then(setOpp)
      .catch(e => setError(e?.response?.data?.message || 'Failed to load opportunity'))
      .finally(() => setLoading(false));
  }, [id]);

  const basePath = window.location.pathname.startsWith('/manager') ? '/manager' : '/rm';

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;
  if (error || !opp) return <div className="error-state"><div className="error-state-icon">⚠</div><h3>{error || 'Opportunity not found'}</h3></div>;

  const evidence = opp.evidence || {};
  const signals = (evidence.signals || {}) as Record<string, { signal: number; weight: number; weighted: number }>;

  return (
    <>
      <div className="back-link" onClick={() => navigate(`${basePath}/opportunities`)}>← Opportunities</div>

      <div className="detail-header">
        <div>
          <h1>{opp.title || 'Opportunity'}</h1>
          <div className="detail-meta">
            <span className={`badge badge-info`}>{capitalize(opp.opportunity_type)}</span>
            <span className={`badge ${opp.priority === 'CRITICAL' ? 'badge-danger' : opp.priority === 'HIGH' ? 'badge-warning' : 'badge-muted'}`}>{opp.priority || 'Medium'}</span>
            <span className={`badge ${opp.status === 'CONVERTED' ? 'badge-success' : opp.status === 'LOST' ? 'badge-danger' : 'badge-info'}`}>{capitalize(opp.status)}</span>
            <span className="detail-meta-item" style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>{opp.id.slice(0, 16)}</span>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="metric-label">Score</div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: (opp.score || 0) >= 0.7 ? 'var(--color-success)' : 'var(--color-warning)' }}>
            {((opp.score || 0) * 100).toFixed(0)}
          </div>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-main">
          {/* Core Info */}
          <div className="panel" style={{ marginBottom: 'var(--space-5)' }}>
            <div className="panel-header"><span className="panel-title">Opportunity Details</span></div>
            <div className="panel-body">
              <div className="info-grid">
                <div className="info-item"><div className="info-label">Customer ID</div><div className="info-value" style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>{opp.customer_id?.slice(0, 12)}</div></div>
                <div className="info-item"><div className="info-label">Est. Value</div><div className="info-value">{formatCurrency(opp.potential_value || 0)}</div></div>
                <div className="info-item"><div className="info-label">Detected</div><div className="info-value">{formatDate(opp.detected_at || opp.created_at)}</div></div>
                <div className="info-item"><div className="info-label">Expires</div><div className="info-value">{formatDate(opp.expires_at)}</div></div>
              </div>
            </div>
          </div>

          {/* Recommended Action */}
          {opp.recommended_action && (
            <div className="panel" style={{ marginBottom: 'var(--space-5)' }}>
              <div className="panel-header"><span className="panel-title">Recommended Action</span></div>
              <div className="panel-body">
                <p style={{ color: 'var(--color-text-secondary)', lineHeight: 'var(--line-height-relaxed)' }}>{opp.recommended_action}</p>
              </div>
            </div>
          )}

          {/* Explainability */}
          <div className="evidence-section">
            <div className="evidence-title">Intelligence Explainability</div>
            {evidence.what ? <p style={{ marginBottom: 'var(--space-3)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}><strong>What:</strong> {String(evidence.what)}</p> : null}
            {evidence.why ? <p style={{ marginBottom: 'var(--space-3)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}><strong>Why:</strong> {String(evidence.why)}</p> : null}

            {Object.keys(signals).length > 0 && (
              <>
                <div className="evidence-title" style={{ marginTop: 'var(--space-4)' }}>Score Breakdown</div>
                <ul className="signal-list">
                  {Object.entries(signals).map(([key, val]) => (
                    <li key={key} className="signal-item">
                      <span className="signal-name">{capitalize(key)}</span>
                      <span className="signal-value">
                        {typeof val === 'object' ? `${(val.weighted || 0).toFixed(2)} (signal: ${(val.signal || 0).toFixed(2)} × weight: ${(val.weight || 0).toFixed(2)})` : String(val)}
                      </span>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </div>

        <div className="detail-aside">
          {/* Reason Codes */}
          {opp.reason_codes && opp.reason_codes.length > 0 && (
            <div className="panel" style={{ marginBottom: 'var(--space-5)' }}>
              <div className="panel-header"><span className="panel-title">Reason Codes</span></div>
              <div className="panel-body">
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                  {opp.reason_codes.map(rc => (
                    <span key={rc} className="badge badge-info">{capitalize(rc)}</span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="panel">
            <div className="panel-header"><span className="panel-title">Metadata</span></div>
            <div className="panel-body">
              <div className="info-item"><div className="info-label">Correlation ID</div><div className="info-value" style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)', wordBreak: 'break-all' }}>{opp.correlation_id || '—'}</div></div>
              <div className="info-item"><div className="info-label">Source Event</div><div className="info-value" style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)', wordBreak: 'break-all' }}>{opp.source_event_id || '—'}</div></div>
              <div className="info-item"><div className="info-label">Agent Version</div><div className="info-value">{(evidence.agent_version as string) || '—'}</div></div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
