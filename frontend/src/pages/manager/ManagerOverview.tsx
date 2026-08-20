import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthContext';
import { getManagerAlerts } from '../../api/manager';
import { listOpportunities } from '../../api/opportunities';
import { capitalize } from '../../utils/format';
import type { ManagerAlert, Opportunity } from '../../types';

export default function ManagerOverview() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<ManagerAlert[]>([]);
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getManagerAlerts().catch(() => []),
      listOpportunities({ limit: 20 }).catch(() => []),
    ]).then(([a, o]) => {
      setAlerts(a);
      setOpps(o);
    }).finally(() => setLoading(false));
  }, []);

  const criticalAlerts = alerts.filter(a => a.severity === 'CRITICAL' || a.severity === 'HIGH');
  const openOpps = opps.filter(o => ['DETECTED', 'ASSIGNED'].includes(o.status));

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;

  return (
    <>
      <div className="page-header">
        <h1>Manager Overview</h1>
        <p>Welcome, {user?.full_name?.split(' ')[0]}. Team intelligence summary.</p>
      </div>

      <div className="metric-row">
        <div className="metric-item">
          <div className="metric-label">Active Alerts</div>
          <div className="metric-value" style={{ color: criticalAlerts.length > 0 ? 'var(--color-danger)' : undefined }}>{alerts.length}</div>
          <div className="metric-sub">{criticalAlerts.length} high/critical</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Open Opportunities</div>
          <div className="metric-value">{openOpps.length}</div>
          <div className="metric-sub">Across team</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Escalations</div>
          <div className="metric-value">{alerts.filter(a => a.alert_type === 'ESCALATION').length}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Achievements</div>
          <div className="metric-value">{alerts.filter(a => a.alert_type === 'ACHIEVEMENT').length}</div>
        </div>
      </div>

      {/* Critical Alerts */}
      <div className="section">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
          <h3 className="section-title" style={{ marginBottom: 0 }}>Priority Alerts</h3>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/manager/intelligence')}>View All →</button>
        </div>
        {criticalAlerts.length === 0 ? (
          <div className="panel"><div className="panel-body" style={{ textAlign: 'center', color: 'var(--color-text-muted)', padding: '32px' }}>No critical alerts</div></div>
        ) : criticalAlerts.slice(0, 4).map(a => (
          <div key={a.alert_id} className="alert-card">
            <div className="alert-card-header">
              <span className="alert-card-title">{a.title}</span>
              <span className={`badge ${a.severity === 'CRITICAL' ? 'badge-danger' : 'badge-warning'}`}>{a.severity}</span>
            </div>
            <div className="alert-card-body">{a.summary}</div>
            <div className="alert-card-footer">
              <span>{capitalize(a.alert_type)}</span> · <span>RM: {a.rm_id.slice(0, 12)}</span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
