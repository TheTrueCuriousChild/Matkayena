import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthContext';
import GalaxyBackground from '../components/GalaxyBackground';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const doLogin = async (loginEmail: string, roles?: string[]) => {
    setError('');
    setLoading(true);
    try {
      await login({ email: loginEmail, password: password || undefined, roles });
      const stored = localStorage.getItem('user');
      const u = stored ? JSON.parse(stored) : null;
      const hasManagerRole = u?.roles?.some((r: string) => ['MANAGER', 'ADMIN', 'REGIONAL_MANAGER', 'TEAM_LEAD'].includes(r));
      navigate(hasManagerRole ? '/manager' : '/rm', { replace: true });
    } catch {
      setError('Login failed. Make sure the backend server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    doLogin(email);
  };

  return (
    <div className="login-page">
      <GalaxyBackground />
      <div className="login-card">
        <h1>Welcome Back</h1>
        <p className="login-sub">Sign in to Matkayena Sales Intelligence</p>

        {error && <div className="login-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              className="form-input"
              placeholder="priya@crm.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              placeholder="Enter password (optional)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button type="submit" className="btn btn-primary btn-lg" style={{ width: '100%' }} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="divider" />

        <p style={{ textAlign: 'center', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: '12px' }}>
          Quick Demo Access
        </p>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            className="btn btn-secondary"
            style={{ flex: 1 }}
            disabled={loading}
            onClick={() => doLogin('priya@crm.com', ['RM'])}
          >
            Login as RM<br />
            <span style={{ fontSize: 'var(--font-size-xs)', opacity: 0.7 }}>Priya Sharma</span>
          </button>
          <button
            className="btn btn-secondary"
            style={{ flex: 1 }}
            disabled={loading}
            onClick={() => doLogin('vikram@crm.com', ['MANAGER'])}
          >
            Login as Manager<br />
            <span style={{ fontSize: 'var(--font-size-xs)', opacity: 0.7 }}>Vikram Seth</span>
          </button>
        </div>
      </div>
    </div>
  );
}
