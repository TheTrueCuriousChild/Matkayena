export function formatCurrency(value: number): string {
  if (value >= 10000000) return `₹${(value / 10000000).toFixed(1)}Cr`;
  if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
  if (value >= 1000) return `₹${(value / 1000).toFixed(1)}K`;
  return `₹${value.toLocaleString('en-IN')}`;
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function formatRelativeTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHrs = Math.floor(diffMins / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateStr);
}

export function getScoreColor(score: number): string {
  if (score >= 0.8) return 'var(--color-success)';
  if (score >= 0.5) return 'var(--color-warning)';
  return 'var(--color-danger)';
}

export function getPriorityColor(priority: string): string {
  switch (priority?.toUpperCase()) {
    case 'CRITICAL': return 'var(--color-danger)';
    case 'HIGH': return 'var(--color-warning)';
    case 'MEDIUM': return 'var(--color-info)';
    case 'LOW': return 'var(--color-muted)';
    default: return 'var(--color-muted)';
  }
}

export function getStatusColor(status: string): string {
  switch (status?.toUpperCase()) {
    case 'COMPLETED': case 'CONVERTED': case 'ANCHORED': case 'HEALTHY': case 'EXCEPTIONAL': case 'ACTIVE':
      return 'var(--color-success)';
    case 'IN_PROGRESS': case 'ASSIGNED': case 'DETECTED': case 'CONTACTED': case 'INTERESTED': case 'PENDING':
      return 'var(--color-info)';
    case 'SNOOZED': case 'PROPOSED': case 'CONTACT_PENDING': case 'MEDIUM':
      return 'var(--color-warning)';
    case 'FAILED': case 'EXPIRED': case 'REJECTED': case 'LOST': case 'AT_RISK': case 'CRITICAL': case 'OVERDUE':
      return 'var(--color-danger)';
    default:
      return 'var(--color-muted)';
  }
}

export function capitalize(str: string): string {
  return str.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}
