import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listActions } from '../../api/actions';
import { formatRelativeTime, capitalize } from '../../utils/format';
import type { Action } from '../../types';

export default function ActionQueue() {
  const navigate = useNavigate();
  const [actions, setActions] = useState<Action[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    listActions({ limit: 100 }).then(setActions).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const now = new Date();
  const grouped = {
    overdue: actions.filter(a => ['ASSIGNED', 'IN_PROGRESS'].includes(a.status) && a.due_date && new Date(a.due_date) < now),
    today: actions.filter(a => ['ASSIGNED', 'IN_PROGRESS'].includes(a.status) && (!a.due_date || new Date(a.due_date) >= now)),
    snoozed: actions.filter(a => a.status === 'SNOOZED'),
    completed: actions.filter(a => ['COMPLETED', 'REJECTED', 'FAILED', 'EXPIRED'].includes(a.status)),
  };

  const filtered = statusFilter
    ? actions.filter(a => a.status === statusFilter)
    : null;

  const displayList = filtered || [
    ...grouped.overdue,
    ...grouped.today,
    ...grouped.snoozed,
    ...grouped.completed,
  ];

  const getBadgeClass = (status: string) => {
    if (['COMPLETED'].includes(status)) return 'badge-success';
    if (['ASSIGNED', 'IN_PROGRESS'].includes(status)) return 'badge-info';
    if (['SNOOZED', 'PROPOSED'].includes(status)) return 'badge-warning';
    if (['FAILED', 'EXPIRED', 'REJECTED'].includes(status)) return 'badge-danger';
    return 'badge-muted';
  };

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;

  return (
    <>
      <div className="page-header">
        <h1>My Actions</h1>
        <p>{actions.length} total actions · {grouped.overdue.length} overdue · {grouped.today.length + grouped.overdue.length} active</p>
      </div>

      <div className="metric-row">
        <div className="metric-item">
          <div className="metric-label">Overdue</div>
          <div className="metric-value" style={{ color: grouped.overdue.length > 0 ? 'var(--color-danger)' : undefined }}>{grouped.overdue.length}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Active</div>
          <div className="metric-value">{grouped.today.length}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Snoozed</div>
          <div className="metric-value">{grouped.snoozed.length}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Completed</div>
          <div className="metric-value">{grouped.completed.length}</div>
        </div>
      </div>

      <div className="data-table-wrap">
        <div className="table-toolbar">
          <div className="table-toolbar-left">
            <select className="table-filter" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
              <option value="">All Statuses</option>
              {['ASSIGNED', 'IN_PROGRESS', 'SNOOZED', 'COMPLETED', 'REJECTED', 'FAILED', 'EXPIRED'].map(s => (
                <option key={s} value={s}>{capitalize(s)}</option>
              ))}
            </select>
          </div>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 4 }}></th>
              <th>Action</th>
              <th>Type</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Due</th>
            </tr>
          </thead>
          <tbody>
            {displayList.length === 0 ? (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)' }}>No actions found</td></tr>
            ) : displayList.map(a => {
              const isOverdue = ['ASSIGNED', 'IN_PROGRESS'].includes(a.status) && a.due_date && new Date(a.due_date) < now;
              return (
                <tr key={a.id} className="clickable" onClick={() => navigate(`/rm/actions/${a.id}`)}>
                  <td><div style={{ width: 4, height: 32, borderRadius: 2, background: isOverdue ? 'var(--color-danger)' : a.priority === 'CRITICAL' ? 'var(--color-danger)' : a.priority === 'HIGH' ? 'var(--color-warning)' : 'var(--color-info)' }} /></td>
                  <td>
                    <div style={{ fontWeight: 500 }}>{a.title}</div>
                    {a.description && <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', maxWidth: 360, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.description}</div>}
                  </td>
                  <td><span className="badge badge-muted">{capitalize(a.action_type)}</span></td>
                  <td><span className={`badge ${a.priority === 'CRITICAL' ? 'badge-danger' : a.priority === 'HIGH' ? 'badge-warning' : 'badge-muted'}`}>{a.priority}</span></td>
                  <td><span className={`badge ${getBadgeClass(a.status)}`}>{capitalize(a.status)}</span></td>
                  <td style={{ color: isOverdue ? 'var(--color-danger)' : 'var(--color-text-secondary)', fontWeight: isOverdue ? 600 : 400 }}>
                    {a.due_date ? formatRelativeTime(a.due_date) : '—'}
                    {isOverdue && <span style={{ fontSize: 'var(--font-size-xs)', display: 'block' }}>OVERDUE</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
