import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listCustomers } from '../../api/customers';
import { formatCurrency, formatDate, capitalize } from '../../utils/format';
import type { Customer } from '../../types';

export default function CustomerList() {
  const navigate = useNavigate();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [segmentFilter, setSegmentFilter] = useState('');

  useEffect(() => {
    listCustomers(100).then(setCustomers).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const filtered = customers.filter(c => {
    const matchSearch = !search || c.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      c.customer_code?.toLowerCase().includes(search.toLowerCase()) ||
      c.email?.toLowerCase().includes(search.toLowerCase());
    const matchSegment = !segmentFilter || c.segment === segmentFilter;
    return matchSearch && matchSegment;
  });

  const segments = [...new Set(customers.map(c => c.segment).filter(Boolean))];
  const basePath = window.location.pathname.startsWith('/manager') ? '/manager' : '/rm';

  if (loading) return <div className="page-loading"><div className="spinner" /></div>;

  return (
    <>
      <div className="page-header">
        <h1>Customers</h1>
        <p>{customers.length} customers in portfolio</p>
      </div>

      <div className="data-table-wrap">
        <div className="table-toolbar">
          <div className="table-toolbar-left">
            <input
              className="table-search"
              placeholder="Search by name, code, or email..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            <select className="table-filter" value={segmentFilter} onChange={e => setSegmentFilter(e.target.value)}>
              <option value="">All Segments</option>
              {segments.map(s => <option key={s} value={s}>{capitalize(s)}</option>)}
            </select>
          </div>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Customer</th>
              <th>Code</th>
              <th>Segment</th>
              <th>Potential Value</th>
              <th>Status</th>
              <th>Last Contact</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)' }}>No customers found</td></tr>
            ) : filtered.map(c => (
              <tr key={c.id} className="clickable" onClick={() => navigate(`${basePath}/customers/${c.id}`)}>
                <td>
                  <div style={{ fontWeight: 500 }}>{c.full_name}</div>
                  {c.email && <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>{c.email}</div>}
                </td>
                <td style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>{c.customer_code}</td>
                <td><span className={`badge ${c.segment === 'ULTRA_HNI' || c.segment === 'HNI' ? 'badge-warning' : 'badge-muted'}`}>{capitalize(c.segment)}</span></td>
                <td>{formatCurrency(c.potential_value || 0)}</td>
                <td><span className={`badge ${c.lifecycle_status === 'ACTIVE' ? 'badge-success' : c.lifecycle_status === 'DORMANT' ? 'badge-danger' : 'badge-muted'}`}>{capitalize(c.lifecycle_status || 'Unknown')}</span></td>
                <td style={{ color: 'var(--color-text-secondary)' }}>{formatDate(c.last_contact_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
