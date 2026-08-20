import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listOpportunities } from '../../api/opportunities';
import { formatCurrency, capitalize } from '../../utils/format';
import type { Opportunity } from '../../types';

const TYPE_OPTIONS = ['', 'CROSS_SELL', 'UPSELL', 'DORMANT_REACTIVATION', 'HIGH_INTENT_LEAD', 'PRODUCT_GAP'];
const STATUS_OPTIONS = ['', 'DETECTED', 'ASSIGNED', 'CONTACT_PENDING', 'CONTACTED', 'INTERESTED', 'CONVERTED', 'LOST'];

export default function OpportunityList() {
  const navigate = useNavigate();
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    listOpportunities({ limit: 100 }).then(setOpps).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const filtered = opps.filter(o => {
    if (typeFilter && o.opportunity_type !== typeFilter) return false;
    if (statusFilter && o.status !== statusFilter) return false;
    if (search && !(o.title || '').toLowerCase().includes(search.toLowerCase()) && !o.id.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const basePath = window.location.pathname.startsWith('/manager') ? '/manager' : '/rm';

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;

  return (
    <>
      <div className="page-header">
        <h1>Opportunities</h1>
        <p>{opps.length} opportunities detected by intelligence</p>
      </div>

      <div className="data-table-wrap">
        <div className="table-toolbar">
          <div className="table-toolbar-left">
            <input className="table-search" placeholder="Search opportunities..." value={search} onChange={e => setSearch(e.target.value)} />
            <select className="table-filter" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
              <option value="">All Types</option>
              {TYPE_OPTIONS.filter(Boolean).map(t => <option key={t} value={t}>{capitalize(t)}</option>)}
            </select>
            <select className="table-filter" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
              <option value="">All Statuses</option>
              {STATUS_OPTIONS.filter(Boolean).map(s => <option key={s} value={s}>{capitalize(s)}</option>)}
            </select>
          </div>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Opportunity</th>
              <th>Type</th>
              <th>Score</th>
              <th>Priority</th>
              <th>Est. Value</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)' }}>No opportunities match filters</td></tr>
            ) : filtered.map(o => (
              <tr key={o.id} className="clickable" onClick={() => navigate(`${basePath}/opportunities/${o.id}`)}>
                <td>
                  <div style={{ fontWeight: 500 }}>{o.title || o.id.slice(0, 16)}</div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>{o.id.slice(0, 12)}</div>
                </td>
                <td><span className="badge badge-info">{capitalize(o.opportunity_type)}</span></td>
                <td>
                  <div className="score-indicator">
                    <div className="score-bar">
                      <div className="score-bar-fill" style={{ width: `${(o.score || 0) * 100}%`, background: (o.score || 0) >= 0.7 ? 'var(--color-success)' : (o.score || 0) >= 0.4 ? 'var(--color-warning)' : 'var(--color-danger)' }} />
                    </div>
                    {((o.score || 0) * 100).toFixed(0)}
                  </div>
                </td>
                <td>
                  <span className={`badge ${o.priority === 'CRITICAL' ? 'badge-danger' : o.priority === 'HIGH' ? 'badge-warning' : 'badge-muted'}`}>
                    {o.priority || '—'}
                  </span>
                </td>
                <td>{formatCurrency(o.potential_value || 0)}</td>
                <td>
                  <span className={`badge ${o.status === 'CONVERTED' ? 'badge-success' : o.status === 'LOST' ? 'badge-danger' : 'badge-info'}`}>
                    {capitalize(o.status)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
