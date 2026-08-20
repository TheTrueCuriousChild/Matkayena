import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getAction, completeAction, snoozeAction } from '../../api/actions';
import { formatCurrency, formatDateTime, capitalize } from '../../utils/format';
import type { ActionDetailResponse, CompleteActionRequest } from '../../types';

export default function ActionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ActionDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showComplete, setShowComplete] = useState(false);
  const [completeForm, setCompleteForm] = useState<CompleteActionRequest>({ outcome_type: 'CONVERTED', notes: '', converted_value: 0, commission_eligible: true });
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    if (!id) return;
    setLoading(true);
    getAction(id)
      .then(setData)
      .catch(e => setError(e?.response?.data?.message || 'Failed to load action'))
      .finally(() => setLoading(false));
  };

  useEffect(load, [id]);

  const handleComplete = async () => {
    if (!id) return;
    setSubmitting(true);
    try {
      await completeAction(id, completeForm);
      setShowComplete(false);
      load();
    } catch (e: unknown) {
      setError((e as { response?: { data?: { message?: string } } })?.response?.data?.message || 'Failed to complete action');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSnooze = async () => {
    if (!id) return;
    try {
      await snoozeAction(id, { reason: 'Snoozed by RM' });
      load();
    } catch {
      /* ignore */
    }
  };

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;
  if (error && !data) return <div className="error-state"><div className="error-state-icon">⚠</div><h3>{error}</h3></div>;
  if (!data) return null;

  const { action: a, outcome, history } = data;

  return (
    <>
      <div className="back-link" onClick={() => navigate('/rm/actions')}>← Actions</div>

      <div className="detail-header">
        <div>
          <h1>{a.title}</h1>
          <div className="detail-meta">
            <span className="badge badge-info">{capitalize(a.action_type)}</span>
            <span className={`badge ${a.priority === 'CRITICAL' ? 'badge-danger' : a.priority === 'HIGH' ? 'badge-warning' : 'badge-muted'}`}>{a.priority}</span>
            <span className={`badge ${a.status === 'COMPLETED' ? 'badge-success' : a.status === 'SNOOZED' ? 'badge-warning' : 'badge-info'}`}>{capitalize(a.status)}</span>
          </div>
        </div>
        {['ASSIGNED', 'IN_PROGRESS'].includes(a.status) && (
          <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <button className="btn btn-secondary btn-sm" onClick={handleSnooze}>Snooze</button>
            <button className="btn btn-primary btn-sm" onClick={() => setShowComplete(true)}>Complete</button>
          </div>
        )}
      </div>

      <div className="detail-grid">
        <div className="detail-main">
          {a.description && (
            <div className="panel" style={{ marginBottom: 'var(--space-5)' }}>
              <div className="panel-header"><span className="panel-title">Description</span></div>
              <div className="panel-body"><p style={{ color: 'var(--color-text-secondary)', lineHeight: 'var(--line-height-relaxed)' }}>{a.description}</p></div>
            </div>
          )}

          <div className="panel" style={{ marginBottom: 'var(--space-5)' }}>
            <div className="panel-header"><span className="panel-title">Details</span></div>
            <div className="panel-body">
              <div className="info-grid">
                <div className="info-item"><div className="info-label">Customer ID</div><div className="info-value" style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>{a.customer_id?.slice(0, 12)}</div></div>
                <div className="info-item"><div className="info-label">Due Date</div><div className="info-value">{formatDateTime(a.due_date)}</div></div>
                <div className="info-item"><div className="info-label">Created</div><div className="info-value">{formatDateTime(a.created_at)}</div></div>
                {a.opportunity_id && <div className="info-item"><div className="info-label">Opportunity</div><div className="info-value" style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>{a.opportunity_id.slice(0, 12)}</div></div>}
              </div>
            </div>
          </div>

          {outcome && (
            <div className="panel" style={{ marginBottom: 'var(--space-5)' }}>
              <div className="panel-header"><span className="panel-title">Outcome</span></div>
              <div className="panel-body">
                <div className="info-grid">
                  <div className="info-item"><div className="info-label">Result</div><div className="info-value"><span className={`badge ${outcome.outcome_type === 'CONVERTED' ? 'badge-success' : 'badge-muted'}`}>{capitalize(outcome.outcome_type)}</span></div></div>
                  {outcome.converted_value > 0 && <div className="info-item"><div className="info-label">Converted Value</div><div className="info-value">{formatCurrency(outcome.converted_value)}</div></div>}
                  <div className="info-item"><div className="info-label">Commission Eligible</div><div className="info-value">{outcome.commission_eligible ? 'Yes' : 'No'}</div></div>
                </div>
                {outcome.notes && <p style={{ marginTop: 'var(--space-3)', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>{outcome.notes}</p>}
              </div>
            </div>
          )}
        </div>

        <div className="detail-aside">
          <div className="panel">
            <div className="panel-header"><span className="panel-title">History</span></div>
            <div className="panel-body">
              {history.length === 0 ? (
                <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>No history</p>
              ) : (
                <div className="timeline">
                  {history.map(h => (
                    <div key={h.id} className="timeline-item">
                      <div className="timeline-dot" />
                      <div className="timeline-time">{formatDateTime(h.created_at)}</div>
                      <div className="timeline-title">{capitalize(h.to_status)}</div>
                      {h.reason && <div className="timeline-desc">{h.reason}</div>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Complete Action Modal */}
      {showComplete && (
        <div className="modal-overlay" onClick={() => setShowComplete(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header"><h2>Complete Action</h2></div>
            <div className="modal-body">
              {error && <div className="login-error">{error}</div>}
              <div className="form-group">
                <label className="form-label">Outcome</label>
                <select className="form-select" value={completeForm.outcome_type} onChange={e => setCompleteForm(p => ({ ...p, outcome_type: e.target.value }))}>
                  <option value="CONVERTED">Converted</option>
                  <option value="INTERESTED_FOLLOWUP">Interested — Follow Up</option>
                  <option value="REJECTED">Rejected</option>
                  <option value="NOT_REACHABLE">Not Reachable</option>
                </select>
              </div>
              {completeForm.outcome_type === 'CONVERTED' && (
                <div className="form-group">
                  <label className="form-label">Converted Value (₹)</label>
                  <input type="number" className="form-input" value={completeForm.converted_value || ''} onChange={e => setCompleteForm(p => ({ ...p, converted_value: parseFloat(e.target.value) || 0 }))} />
                </div>
              )}
              <div className="form-group">
                <label className="form-label">Notes</label>
                <textarea className="form-textarea" value={completeForm.notes || ''} onChange={e => setCompleteForm(p => ({ ...p, notes: e.target.value }))} placeholder="Interaction summary..." />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowComplete(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleComplete} disabled={submitting}>{submitting ? 'Submitting...' : 'Complete Action'}</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
