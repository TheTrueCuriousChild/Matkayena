import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './features/auth/AuthContext';
import ProtectedRoute from './features/auth/ProtectedRoute';
import AppLayout from './layouts/AppLayout';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RMOverview from './pages/rm/RMOverview';
import CustomerList from './pages/shared/CustomerList';
import CustomerDetail from './pages/shared/CustomerDetail';
import OpportunityList from './pages/shared/OpportunityList';
import OpportunityDetail from './pages/shared/OpportunityDetail';
import ActionQueue from './pages/rm/ActionQueue';
import ActionDetail from './pages/rm/ActionDetail';
import RMPerformance from './pages/rm/RMPerformance';
import ManagerOverview from './pages/manager/ManagerOverview';
import TeamPerformance from './pages/manager/TeamPerformance';
import ManagerIntelligence from './pages/manager/ManagerIntelligence';

export default function App() {
  const { isAuthenticated, isManager } = useAuth();

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={isAuthenticated ? <Navigate to={isManager ? '/manager' : '/rm'} replace /> : <LandingPage />} />
      <Route path="/login" element={isAuthenticated ? <Navigate to={isManager ? '/manager' : '/rm'} replace /> : <LoginPage />} />

      {/* RM routes */}
      <Route path="/rm" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route index element={<RMOverview />} />
        <Route path="customers" element={<CustomerList />} />
        <Route path="customers/:id" element={<CustomerDetail />} />
        <Route path="opportunities" element={<OpportunityList />} />
        <Route path="opportunities/:id" element={<OpportunityDetail />} />
        <Route path="actions" element={<ActionQueue />} />
        <Route path="actions/:id" element={<ActionDetail />} />
        <Route path="performance" element={<RMPerformance />} />
      </Route>

      {/* Manager routes */}
      <Route path="/manager" element={<ProtectedRoute requiredRoles={['MANAGER', 'ADMIN', 'REGIONAL_MANAGER', 'TEAM_LEAD']}><AppLayout /></ProtectedRoute>}>
        <Route index element={<ManagerOverview />} />
        <Route path="customers" element={<CustomerList />} />
        <Route path="customers/:id" element={<CustomerDetail />} />
        <Route path="opportunities" element={<OpportunityList />} />
        <Route path="opportunities/:id" element={<OpportunityDetail />} />
        <Route path="team" element={<TeamPerformance />} />
        <Route path="intelligence" element={<ManagerIntelligence />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
