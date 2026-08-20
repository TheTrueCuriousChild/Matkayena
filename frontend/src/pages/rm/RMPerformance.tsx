import { useEffect, useState } from 'react';
import { useAuth } from '../../features/auth/AuthContext';
import { getRMPerformance, listAchievements } from '../../api/performance';
import { formatCurrency, capitalize } from '../../utils/format';
import type { PerformanceSnapshot, Achievement } from '../../types';

export default function RMPerformance() {
  const { user } = useAuth();
  const [perf, setPerf] = useState<PerformanceSnapshot | null>(null);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) return;
    Promise.all([
      getRMPerformance(user.user_id).catch(e => { setError(e?.response?.data?.message || 'Performance service unavailable'); return null; }),
      listAchievements(user.user_id).catch(() => []),
    ]).then(([p, a]) => {
      if (p) setPerf(p);
      setAchievements(a as Achievement[]);
    }).finally(() => setLoading(false));
  }, [user]);

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;

  const s = perf?.snapshot;

  return (
    <>
      <div className="page-header">
        <h1>My Performance</h1>
        <p>Period: {s?.period || '2026-Q1'}</p>
      </div>

      {error && (
        <div style={{ padding: 'var(--space-4)', background: 'var(--color-warning-bg)', border: '1px solid rgba(251,191,36,0.2)', borderRadius: 'var(--radius-lg)', marginBottom: 'var(--space-5)', color: 'var(--color-warning)', fontSize: 'var(--font-size-sm)' }}>
          {error}. Showing cached data if available.
        </div>
      )}

      {s && (
        <>
          {/* Main Target vs Achievement */}
          <div className="panel" style={{ marginBottom: 'var(--space-5)' }}>
            <div className="panel-header">
              <span className="panel-title">Target Progress</span>
              <span className={`badge ${s.status === 'EXCEPTIONAL' ? 'badge-success' : s.status === 'HEALTHY' ? 'badge-success' : s.status === 'AT_RISK' ? 'badge-warning' : 'badge-danger'}`}>
                {capitalize(s.status)}
              </span>
            </div>
            <div className="panel-body">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)', fontSize: 'var(--font-size-sm)' }}>
                <span>Achievement: {formatCurrency(s.achievement)}</span>
                <span>Target: {formatCurrency(s.target)}</span>
              </div>
              <div className="progress-bar">
                <div className="progress-bar-fill" style={{
                  width: `${Math.min(100, s.achievement_percent)}%`,
                  background: s.achievement_percent >= 100 ? 'var(--color-success)' : s.achievement_percent >= 70 ? 'var(--color-info)' : s.achievement_percent >= 40 ? 'var(--color-warning)' : 'var(--color-danger)',
                }} />
              </div>
              <div style={{ textAlign: 'center', marginTop: 'var(--space-2)', fontSize: 'var(--font-size-xl)', fontWeight: 700 }}>
                {s.achievement_percent.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className="metric-row">
            <div className="metric-item">
              <div className="metric-label">Conversion Rate</div>
              <div className="metric-value">{(s.conversion_rate * 100).toFixed(1)}%</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Pipeline Value</div>
              <div className="metric-value">{formatCurrency(s.pipeline_value)}</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Activities</div>
              <div className="metric-value">{s.activity_count}</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Overdue Actions</div>
              <div className="metric-value" style={{ color: s.overdue_actions > 0 ? 'var(--color-danger)' : undefined }}>{s.overdue_actions}</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">SLA Score</div>
              <div className="metric-value">{(s.sla_score * 100).toFixed(0)}%</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">SLA Breaches</div>
              <div className="metric-value" style={{ color: s.sla_breaches > 0 ? 'var(--color-danger)' : undefined }}>{s.sla_breaches}</div>
            </div>
          </div>

          {/* Drivers */}
          {(s.primary_drivers?.length > 0 || s.secondary_drivers?.length > 0) && (
            <div className="panel" style={{ marginBottom: 'var(--space-5)' }}>
              <div className="panel-header"><span className="panel-title">Performance Drivers</span></div>
              <div className="panel-body">
                {s.primary_drivers?.length > 0 && (
                  <div style={{ marginBottom: 'var(--space-3)' }}>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 'var(--space-1)' }}>Primary</div>
                    <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                      {s.primary_drivers.map(d => <span key={d} className="badge badge-info">{d}</span>)}
                    </div>
                  </div>
                )}
                {s.secondary_drivers?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 'var(--space-1)' }}>Secondary</div>
                    <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                      {s.secondary_drivers.map(d => <span key={d} className="badge badge-muted">{d}</span>)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {s.recommended_intervention && (
            <div className="panel" style={{ marginBottom: 'var(--space-5)' }}>
              <div className="panel-header"><span className="panel-title">Recommended Focus</span></div>
              <div className="panel-body"><p style={{ color: 'var(--color-text-secondary)', lineHeight: 'var(--line-height-relaxed)' }}>{s.recommended_intervention}</p></div>
            </div>
          )}
        </>
      )}

      {/* Achievements */}
      <div className="section">
        <h3 className="section-title">Achievements</h3>
        {achievements.length === 0 ? (
          <div className="panel"><div className="panel-body empty-state" style={{ padding: '32px' }}><h3>No achievements yet</h3></div></div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead><tr><th>Achievement</th><th>Type</th><th>Period</th><th>Milestone</th></tr></thead>
              <tbody>
                {achievements.map(a => (
                  <tr key={a.id}>
                    <td><div style={{ fontWeight: 500 }}>{a.title}</div>{a.description && <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>{a.description}</div>}</td>
                    <td><span className="badge badge-success">{capitalize(a.achievement_type)}</span></td>
                    <td>{a.period || '—'}</td>
                    <td>{formatCurrency(a.milestone_value || 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
