import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthContext';
import { listOpportunities } from '../../api/opportunities';
import { listActions } from '../../api/actions';
import { formatCurrency, formatRelativeTime, capitalize } from '../../utils/format';
import type { Opportunity, Action } from '../../types';

export default function RMOverview() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [actions, setActions] = useState<Action[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    Promise.all([
      listOpportunities({ limit: 10 }).catch(() => []),
      listActions({ limit: 10 }).catch(() => []),
    ]).then(([o, a]) => {
      setOpps(o);
      setActions(a);
    }).finally(() => setLoading(false));
  }, [user]);

  const activeActions = actions.filter(a => ['ASSIGNED', 'IN_PROGRESS'].includes(a.status));
  const overdueActions = activeActions.filter(a => a.due_date && new Date(a.due_date) < new Date());
  const openOpps = opps.filter(o => ['DETECTED', 'ASSIGNED', 'CONTACT_PENDING'].includes(o.status));

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;

  return (
    <>
      <div className="page-header">
        <h1>Overview</h1>
        <p>Welcome back, {user?.full_name?.split(' ')[0] || 'User'}. Here's what needs your attention today.</p>
      </div>

      {/* Metrics */}
      <div className="metric-row">
        <div className="metric-item">
          <div className="metric-label">Open Opportunities</div>
          <div className="metric-value">{openOpps.length}</div>
          <div className="metric-sub">Intelligence-detected</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Active Actions</div>
          <div className="metric-value">{activeActions.length}</div>
          <div className="metric-sub">{overdueActions.length > 0 ? `${overdueActions.length} overdue` : 'All on track'}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Pipeline Value</div>
          <div className="metric-value">{formatCurrency(openOpps.reduce((s, o) => s + (o.potential_value || 0), 0))}</div>
          <div className="metric-sub">From detected opps</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Customers</div>
          <div className="metric-value">—</div>
          <div className="metric-sub">Managed portfolio</div>
        </div>
      </div>

      {/* Priority Actions */}
      <div className="section">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
          <h3 className="section-title" style={{ marginBottom: 0 }}>Priority Actions</h3>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/rm/actions')}>View All →</button>
        </div>
        <div className="panel">
          {activeActions.length === 0 ? (
            <div className="empty-state" style={{ padding: '40px' }}>
              <div className="empty-state-icon">☐</div>
              <h3>No Active Actions</h3>
              <p>Intelligence will generate actions when opportunities are detected.</p>
            </div>
          ) : (
            <ul className="priority-list">
              {activeActions.slice(0, 5).map(a => (
                <li key={a.id} className="priority-item" onClick={() => navigate(`/rm/actions/${a.id}`)}>
                  <div className="priority-indicator" style={{ background: a.priority === 'CRITICAL' ? 'var(--color-danger)' : a.priority === 'HIGH' ? 'var(--color-warning)' : 'var(--color-info)' }} />
                  <div className="priority-body">
                    <div className="priority-title">{a.title}</div>
                    <div className="priority-sub">
                      {capitalize(a.action_type)} · {capitalize(a.priority)} · {a.due_date ? formatRelativeTime(a.due_date) : 'No due date'}
                    </div>
                  </div>
                  <span className="badge badge-info" style={{ flexShrink: 0 }}>{capitalize(a.status)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Recent Opportunities */}
      <div className="section">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
          <h3 className="section-title" style={{ marginBottom: 0 }}>Recent Opportunities</h3>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/rm/opportunities')}>View All →</button>
        </div>
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Opportunity</th>
                <th>Type</th>
                <th>Score</th>
                <th>Value</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {openOpps.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', padding: '32px', color: 'var(--color-text-muted)' }}>No open opportunities</td></tr>
              ) : openOpps.slice(0, 5).map(o => (
                <tr key={o.id} className="clickable" onClick={() => navigate(`/rm/opportunities/${o.id}`)}>
                  <td style={{ fontWeight: 500 }}>{o.title || o.id.slice(0, 12)}</td>
                  <td><span className="badge badge-info">{capitalize(o.opportunity_type)}</span></td>
                  <td>
                    <div className="score-indicator">
                      <div className="score-bar"><div className="score-bar-fill" style={{ width: `${(o.score || 0) * 100}%`, background: (o.score || 0) >= 0.7 ? 'var(--color-success)' : 'var(--color-warning)' }} /></div>
                      {((o.score || 0) * 100).toFixed(0)}
                    </div>
                  </td>
                  <td>{formatCurrency(o.potential_value || 0)}</td>
                  <td><span className="badge badge-info">{capitalize(o.status)}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
