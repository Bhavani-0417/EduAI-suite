import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';

import Login        from './pages/Login';
import Register     from './pages/Register';
import Dashboard    from './pages/Dashboard';
import Academic     from './pages/Academic';
import Notes        from './pages/Notes';
import Content      from './pages/Content';
import Career       from './pages/Career';
import Roadmap      from './pages/Roadmap';
import Chat         from './pages/Chat';
import Vault        from './pages/Vault';
import CodeExplainer from './pages/CodeExplainer';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return (
    <div style={{ minHeight: '100vh', background: '#0d0f14', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ color: '#818cf8', fontSize: 16 }}>Loading EduAI Suite...</div>
    </div>
  );
  if (!user) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/dashboard" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/academic"  element={<ProtectedRoute><Academic /></ProtectedRoute>} />
      <Route path="/notes"     element={<ProtectedRoute><Notes /></ProtectedRoute>} />
      <Route path="/content"   element={<ProtectedRoute><Content /></ProtectedRoute>} />
      <Route path="/career"    element={<ProtectedRoute><Career /></ProtectedRoute>} />
      <Route path="/roadmap"   element={<ProtectedRoute><Roadmap /></ProtectedRoute>} />
      <Route path="/chat"      element={<ProtectedRoute><Chat /></ProtectedRoute>} />
      <Route path="/vault"     element={<ProtectedRoute><Vault /></ProtectedRoute>} />
      <Route path="/code"      element={<ProtectedRoute><CodeExplainer /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}