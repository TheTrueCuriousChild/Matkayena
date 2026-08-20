import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCustomer360 } from '../../api/customers';
import { formatCurrency, formatDate, formatDateTime, capitalize } from '../../utils/format';
import type { Customer360Response } from '../../types';

type TabKey = 'overview' | 'holdings' | 'activity' | 'leads';

export default function CustomerDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<Customer360Response | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<TabKey>('overview');

  useEffect(() => {
    if (!id) return;
    getCustomer360(id)
      .then(setData)
      .catch(e => setError(e?.response?.data?.message || 'Failed to load customer'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;
  if (error || !data) return <div className="error-state"><div className="error-state-icon">⚠</div><h3>{error || 'Customer not found'}</h3></div>;

  const { customer: c, holdings, recent_transactions: txns, recent_interactions: intxns, active_leads: leads } = data;
  const basePath = window.location.pathname.startsWith('/manager') ? '/manager' : '/rm';

  return (
    <>
      <div className="back-link" onClick={() => navigate(`${basePath}/customers`)}>← Customers</div>

      <div className="detail-header">
        <div>
          <h1>{c.full_name}</h1>
          <div className="detail-meta">
            <span className="detail-meta-item">{c.customer_code}</span>
            <span className={`badge ${c.segment === 'ULTRA_HNI' || c.segment === 'HNI' ? 'badge-warning' : 'badge-muted'}`}>{capitalize(c.segment)}</span>
            <span className={`badge ${c.lifecycle_status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}`}>{capitalize(c.lifecycle_status)}</span>
          </div>
        </div>
      </div>

      <div className="tabs">
        {(['overview', 'holdings', 'activity', 'leads'] as TabKey[]).map(t => (
          <button key={t} className={`tab${tab === t ? ' active' : ''}`} onClick={() => setTab(t)}>
            {t === 'overview' ? 'Overview' : t === 'holdings' ? `Holdings (${holdings.length})` : t === 'activity' ? 'Activity' : `Leads (${leads.length})`}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="detail-grid">
          <div className="detail-main">
            <div className="panel" style={{ marginBottom: 'var(--space-5)' }}>
              <div className="panel-header"><span className="panel-title">Customer Information</span></div>
              <div className="panel-body">
                <div className="info-grid">
                  <div className="info-item"><div className="info-label">Email</div><div className="info-value">{c.email || '—'}</div></div>
                  <div className="info-item"><div className="info-label">Phone</div><div className="info-value">{c.phone || '—'}</div></div>
                  <div className="info-item"><div className="info-label">City</div><div className="info-value">{c.city || '—'}</div></div>
                  <div className="info-item"><div className="info-label">Segment</div><div className="info-value">{capitalize(c.segment)}</div></div>
                  <div className="info-item"><div className="info-label">Potential Value</div><div className="info-value">{formatCurrency(c.potential_value || 0)}</div></div>
                  <div className="info-item"><div className="info-label">Last Contact</div><div className="info-value">{formatDate(c.last_contact_at)}</div></div>
                </div>
              </div>
            </div>
          </div>
          <div className="detail-aside">
            <div className="panel">
              <div className="panel-header"><span className="panel-title">Quick Summary</span></div>
              <div className="panel-body">
                <div className="info-item"><div className="info-label">Holdings</div><div className="info-value">{holdings.length} active</div></div>
                <div className="info-item"><div className="info-label">Active Leads</div><div className="info-value">{leads.length}</div></div>
                <div className="info-item"><div className="info-label">Recent Transactions</div><div className="info-value">{txns.length}</div></div>
                <div className="info-item"><div className="info-label">Interactions</div><div className="info-value">{intxns.length}</div></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {tab === 'holdings' && (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead><tr><th>Product ID</th><th>Status</th><th>Value</th><th>Acquired</th></tr></thead>
            <tbody>
              {holdings.length === 0 ? (
                <tr><td colSpan={4} style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)' }}>No holdings</td></tr>
              ) : holdings.map(h => (
                <tr key={h.id}>
                  <td style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>{h.product_id.slice(0, 12)}...</td>
                  <td><span className={`badge ${h.status === 'ACTIVE' ? 'badge-success' : 'badge-muted'}`}>{h.status}</span></td>
                  <td>{formatCurrency(h.relationship_value || 0)}</td>
                  <td>{formatDate(h.acquired_on)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'activity' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-5)' }}>
          <div>
            <h3 className="section-title">Recent Transactions</h3>
            <div className="data-table-wrap">
              <table className="data-table">
                <thead><tr><th>Type</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
                <tbody>
                  {txns.length === 0 ? (
                    <tr><td colSpan={4} style={{ textAlign: 'center', padding: '32px', color: 'var(--color-text-muted)' }}>No transactions</td></tr>
                  ) : txns.map(t => (
                    <tr key={t.id}>
                      <td>{capitalize(t.transaction_type)}</td>
                      <td>{formatCurrency(t.amount)}</td>
                      <td><span className={`badge ${t.status === 'COMPLETED' ? 'badge-success' : 'badge-info'}`}>{t.status}</span></td>
                      <td>{formatDateTime(t.transaction_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div>
            <h3 className="section-title">Recent Interactions</h3>
            <div className="panel">
              {intxns.length === 0 ? (
                <div className="panel-body" style={{ textAlign: 'center', color: 'var(--color-text-muted)' }}>No interactions</div>
              ) : (
                <div className="panel-body">
                  <div className="timeline">
                    {intxns.slice(0, 10).map(i => (
                      <div key={i.id} className="timeline-item">
                        <div className="timeline-dot" />
                        <div className="timeline-time">{formatDateTime(i.occurred_at)}</div>
                        <div className="timeline-title">{capitalize(i.interaction_type)}</div>
                        {i.outcome && <div className="timeline-desc">Outcome: {i.outcome}</div>}
                        {i.notes && <div className="timeline-desc">{i.notes}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {tab === 'leads' && (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead><tr><th>Lead</th><th>Source</th><th>Stage</th><th>Value</th><th>Priority</th><th>Next Follow-up</th></tr></thead>
            <tbody>
              {leads.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)' }}>No active leads</td></tr>
              ) : leads.map(l => (
                <tr key={l.id}>
                  <td style={{ fontWeight: 500 }}>{l.lead_code || l.id.slice(0, 12)}</td>
                  <td>{l.source || '—'}</td>
                  <td><span className="badge badge-info">{capitalize(l.stage)}</span></td>
                  <td>{formatCurrency(l.potential_value || 0)}</td>
                  <td><span className={`badge ${l.priority === 'HIGH' || l.priority === 'CRITICAL' ? 'badge-danger' : 'badge-muted'}`}>{l.priority}</span></td>
                  <td>{formatDate(l.next_followup_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
