import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { login as apiLogin, getCurrentUser } from '../../api/auth';
import type { User, LoginRequest } from '../../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isRM: boolean;
  isManager: boolean;
  isLoading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [isLoading, setIsLoading] = useState(!!token);

  const isAuthenticated = !!user && !!token;
  const isRM = user?.roles?.includes('RM') ?? false;
  const isManager = user?.roles?.some((r: string) => ['MANAGER', 'ADMIN', 'REGIONAL_MANAGER', 'TEAM_LEAD'].includes(r)) ?? false;

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }, []);

  const login = useCallback(async (data: LoginRequest) => {
    const res = await apiLogin(data);
    localStorage.setItem('access_token', res.access_token);
    setToken(res.access_token);
    const u: User = {
      user_id: res.user_id,
      email: res.email,
      roles: res.roles,
      full_name: res.full_name,
      manager_id: res.manager_id,
      org_unit_id: res.org_unit_id,
      is_active: true,
    };
    setUser(u);
    localStorage.setItem('user', JSON.stringify(u));
  }, []);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }
    getCurrentUser()
      .then((u: User) => {
        setUser(u);
        localStorage.setItem('user', JSON.stringify(u));
      })
      .catch(() => {
        // Backend unreachable — fall back to cached user from localStorage (demo mode)
        const cached = localStorage.getItem('user');
        if (cached) {
          try {
            setUser(JSON.parse(cached) as User);
          } catch {
            logout();
          }
        } else {
          logout();
        }
      })
      .finally(() => setIsLoading(false));
  }, [token, logout]);

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, isRM, isManager, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
