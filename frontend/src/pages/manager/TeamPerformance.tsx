import { useEffect, useState } from 'react';
import { getManagerAlerts } from '../../api/manager';
import { capitalize } from '../../utils/format';
import type { ManagerAlert } from '../../types';

interface RMSummary {
  rm_id: string;
  alerts: ManagerAlert[];
  criticalCount: number;
  hasEscalation: boolean;
  hasAchievement: boolean;
}

export default function TeamPerformance() {
  const [alerts, setAlerts] = useState<ManagerAlert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getManagerAlerts().then(setAlerts).catch(() => {}).finally(() => setLoading(false));
  }, []);

  // Group alerts by RM
  const rmMap = new Map<string, ManagerAlert[]>();
  alerts.forEach(a => {
    const existing = rmMap.get(a.rm_id) || [];
    existing.push(a);
    rmMap.set(a.rm_id, existing);
  });

  const rmSummaries: RMSummary[] = Array.from(rmMap.entries()).map(([rm_id, rmAlerts]) => ({
    rm_id,
    alerts: rmAlerts,
    criticalCount: rmAlerts.filter(a => a.severity === 'CRITICAL' || a.severity === 'HIGH').length,
    hasEscalation: rmAlerts.some(a => a.alert_type === 'ESCALATION'),
    hasAchievement: rmAlerts.some(a => a.alert_type === 'ACHIEVEMENT'),
  }));

  rmSummaries.sort((a, b) => b.criticalCount - a.criticalCount);

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;

  return (
    <>
      <div className="page-header">
        <h1>Team Performance</h1>
        <p>Intelligence-driven team view across {rmSummaries.length} RMs</p>
      </div>

      {rmSummaries.length === 0 ? (
        <div className="panel">
          <div className="panel-body empty-state">
            <div className="empty-state-icon">⊟</div>
            <h3>No Team Data</h3>
            <p>Performance data will appear once agents evaluate RMs for the current period.</p>
          </div>
        </div>
      ) : (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>RM</th>
                <th>Alerts</th>
                <th>Critical/High</th>
                <th>Escalation</th>
                <th>Achievement</th>
                <th>Top Alert</th>
              </tr>
            </thead>
            <tbody>
              {rmSummaries.map(rm => (
                <tr key={rm.rm_id}>
                  <td style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-sm)', fontWeight: 500 }}>{rm.rm_id.slice(0, 20)}</td>
                  <td>{rm.alerts.length}</td>
                  <td>
                    <span className={`badge ${rm.criticalCount > 0 ? 'badge-danger' : 'badge-success'}`}>
                      {rm.criticalCount}
                    </span>
                  </td>
                  <td>
                    {rm.hasEscalation ? <span className="badge badge-danger">Yes</span> : <span className="badge badge-muted">No</span>}
                  </td>
                  <td>
                    {rm.hasAchievement ? <span className="badge badge-success">Yes</span> : <span className="badge badge-muted">No</span>}
                  </td>
                  <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    {rm.alerts[0]?.title || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
