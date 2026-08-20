import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthContext';

export default function AppLayout() {
  const { user, isRM, isManager, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const initials = user?.full_name
    ?.split(' ')
    .map((n: string) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2) || 'U';

  const primaryRole = isManager ? 'Manager' : 'Relationship Manager';
  const basePath = isManager ? '/manager' : '/rm';

  return (
    <div className="app-shell">
      <aside className="sidebar" role="navigation" aria-label="Main navigation">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">M</div>
          <div>
            <div className="sidebar-brand-text">Matkayena</div>
            <div className="sidebar-brand-sub">Sales Intelligence</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section-label">Navigation</div>

          <NavLink to={basePath} end className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
            <span className="nav-icon">◉</span> Overview
          </NavLink>

          <NavLink to={`${basePath}/customers`} className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
            <span className="nav-icon">⊞</span> Customers
          </NavLink>

          <NavLink to={`${basePath}/opportunities`} className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
            <span className="nav-icon">◈</span> Opportunities
          </NavLink>

          {isRM && !isManager && (
            <NavLink to="/rm/actions" className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
              <span className="nav-icon">☐</span> My Actions
            </NavLink>
          )}

          {isRM && !isManager && (
            <NavLink to="/rm/performance" className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
              <span className="nav-icon">◧</span> Performance
            </NavLink>
          )}

          {isManager && (
            <>
              <div className="sidebar-section-label" style={{ marginTop: '8px' }}>Management</div>
              <NavLink to="/manager/team" className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
                <span className="nav-icon">⊟</span> Team Performance
              </NavLink>
              <NavLink to="/manager/intelligence" className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
                <span className="nav-icon">⚡</span> Intelligence
              </NavLink>
            </>
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-avatar">{initials}</div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{user?.full_name || 'User'}</div>
              <div className="sidebar-user-role">{primaryRole}</div>
            </div>
          </div>
          <button className="btn-logout" onClick={handleLogout} style={{ marginTop: '8px', width: '100%', textAlign: 'left' }}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
