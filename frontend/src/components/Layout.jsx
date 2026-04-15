import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV = [
  { path: '/dashboard',   icon: '⊞', label: 'Dashboard' },
  { path: '/academic',    icon: '📊', label: 'Academic' },
  { path: '/notes',       icon: '📚', label: 'Knowledge Hub' },
  { path: '/content',     icon: '🎨', label: 'Content Generator' },
  { path: '/career',      icon: '💼', label: 'Career Center' },
  { path: '/roadmap',     icon: '🎯', label: 'Roadmap' },
  { path: '/chat',        icon: '🤖', label: 'AI Chatbot' },
  { path: '/vault',       icon: '🗂', label: 'Doc Vault' },
  { path: '/code',        icon: '🔧', label: 'Code Explainer' },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0d0f14', fontFamily: "'DM Sans', sans-serif" }}>
      
      {/* Sidebar */}
      <aside style={{
        width: collapsed ? 64 : 220,
        background: '#13161e',
        borderRight: '1px solid #1e2230',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.2s ease',
        position: 'fixed',
        top: 0, left: 0, bottom: 0,
        zIndex: 100,
        overflow: 'hidden',
      }}>
        {/* Logo */}
        <div style={{ padding: '18px 16px', borderBottom: '1px solid #1e2230', display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, flexShrink: 0 }}>E</div>
          {!collapsed && <span style={{ fontWeight: 700, fontSize: 15, color: '#e2e8f0', letterSpacing: '-0.3px' }}>EduAI Suite</span>}
          <button onClick={() => setCollapsed(!collapsed)} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#4a5568', cursor: 'pointer', fontSize: 16, padding: 0, flexShrink: 0 }}>
            {collapsed ? '›' : '‹'}
          </button>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
          {NAV.map(item => {
            const active = location.pathname === item.path;
            return (
              <Link key={item.path} to={item.path} style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '9px 10px', borderRadius: 8, marginBottom: 2,
                textDecoration: 'none',
                background: active ? '#1e2745' : 'transparent',
                color: active ? '#818cf8' : '#6b7280',
                transition: 'all 0.15s',
                fontSize: 13,
                fontWeight: active ? 600 : 400,
                whiteSpace: 'nowrap',
              }}>
                <span style={{ fontSize: 16, flexShrink: 0 }}>{item.icon}</span>
                {!collapsed && <span>{item.label}</span>}
                {!collapsed && active && <span style={{ marginLeft: 'auto', width: 6, height: 6, borderRadius: '50%', background: '#818cf8', flexShrink: 0 }} />}
              </Link>
            );
          })}
        </nav>

        {/* User */}
        <div style={{ padding: '12px 8px', borderTop: '1px solid #1e2230' }}>
          {!collapsed && user && (
            <div style={{ padding: '8px 10px', marginBottom: 4, borderRadius: 8, background: '#0d0f14' }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: '#e2e8f0', marginBottom: 2 }}>{user.name || user.email}</div>
              <div style={{ fontSize: 11, color: '#4a5568' }}>{user.college || 'Student'}</div>
            </div>
          )}
          <button onClick={handleLogout} style={{
            width: '100%', padding: '8px 10px', borderRadius: 8, border: 'none',
            background: 'transparent', color: '#ef4444', cursor: 'pointer',
            textAlign: collapsed ? 'center' : 'left', fontSize: 13,
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <span>⎋</span>{!collapsed && 'Logout'}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{
        flex: 1,
        marginLeft: collapsed ? 64 : 220,
        transition: 'margin-left 0.2s ease',
        padding: '28px 32px',
        minHeight: '100vh',
        color: '#e2e8f0',
      }}>
        {children}
      </main>
    </div>
  );
}