import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { academicAPI } from '../services/api';

const MODULES = [
  { path: '/academic',  icon: '📊', label: 'Academic',       color: '#6366f1', desc: 'CGPA · Marks · Weakness' },
  { path: '/notes',     icon: '📚', label: 'Knowledge Hub',  color: '#10b981', desc: 'Notes · RAG Q&A · PDF' },
  { path: '/content',   icon: '🎨', label: 'Content Gen',    color: '#f59e0b', desc: 'PPT · Docs · Lab Manual' },
  { path: '/career',    icon: '💼', label: 'Career',         color: '#ec4899', desc: 'Resume · Jobs · JD Match' },
  { path: '/roadmap',   icon: '🎯', label: 'Roadmap',        color: '#8b5cf6', desc: 'Goals · Learning Path' },
  { path: '/chat',      icon: '🤖', label: 'AI Chatbot',     color: '#06b6d4', desc: 'Voice · RAG · Multi-tool' },
  { path: '/vault',     icon: '🗂', label: 'Doc Vault',      color: '#84cc16', desc: 'Encrypted · OCR · Share' },
  { path: '/code',      icon: '🔧', label: 'Code Explainer', color: '#f97316', desc: 'Debug · Fix · Review' },
];

export default function Dashboard() {
  const { user } = useAuth();
  const [cgpa, setCgpa] = useState(null);
  const [weaknesses, setWeaknesses] = useState(null);

  useEffect(() => {
    academicAPI.getCGPA().then(r => setCgpa(r.data)).catch(() => {});
    academicAPI.getWeaknesses().then(r => setWeaknesses(r.data)).catch(() => {});
  }, []);

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, color: '#e2e8f0', margin: 0, letterSpacing: '-0.5px' }}>
          Welcome back, {user?.name?.split(' ')[0] || 'Student'} 👋
        </h1>
        <p style={{ color: '#4a5568', fontSize: 14, margin: '6px 0 0' }}>
          {user?.branch} · {user?.college} · Year {user?.year}
        </p>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 32 }}>
        {[
          { label: 'Current CGPA', value: cgpa?.cgpa ?? '—', sub: cgpa ? `${cgpa.percentage}%` : 'Add marks to calculate', color: '#6366f1' },
          { label: 'Weak Subjects', value: weaknesses?.weak_subjects?.length ?? '—', sub: weaknesses ? 'Needs attention' : 'Add marks first', color: '#ef4444' },
          { label: 'Strong Subjects', value: weaknesses?.strong_subjects?.length ?? '—', sub: 'Performing well', color: '#10b981' },
          { label: 'API Endpoints', value: '45+', sub: 'Backend 100% done ✓', color: '#f59e0b' },
        ].map(stat => (
          <div key={stat.label} style={{ background: '#13161e', border: '1px solid #1e2230', borderRadius: 12, padding: '18px 20px' }}>
            <div style={{ fontSize: 12, color: '#4a5568', marginBottom: 6 }}>{stat.label}</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: stat.color, marginBottom: 4 }}>{stat.value}</div>
            <div style={{ fontSize: 12, color: '#6b7280' }}>{stat.sub}</div>
          </div>
        ))}
      </div>

      {/* Weakness alert */}
      {weaknesses?.weak_subjects?.length > 0 && (
        <div style={{ background: '#1a0c0c', border: '1px solid #7f1d1d', borderRadius: 12, padding: '14px 18px', marginBottom: 28, display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 20 }}>⚠️</span>
          <div>
            <div style={{ color: '#fca5a5', fontSize: 14, fontWeight: 500 }}>Weak subjects detected</div>
            <div style={{ color: '#6b7280', fontSize: 13 }}>
              {weaknesses.weak_subjects.map(s => `${s.subject} (${Math.round(s.percentage)}%)`).join(', ')}
            </div>
          </div>
          <Link to="/academic" style={{ marginLeft: 'auto', color: '#818cf8', fontSize: 13, textDecoration: 'none' }}>View roadmap →</Link>
        </div>
      )}

      {/* Module grid */}
      <h2 style={{ fontSize: 16, fontWeight: 600, color: '#9ca3af', marginBottom: 16, letterSpacing: '0.05em', textTransform: 'uppercase', fontSize: 12 }}>All Modules</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
        {MODULES.map(mod => (
          <Link key={mod.path} to={mod.path} style={{ textDecoration: 'none' }}>
            <div style={{
              background: '#13161e', border: '1px solid #1e2230', borderRadius: 12, padding: '18px 16px',
              transition: 'all 0.15s', cursor: 'pointer',
            }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = mod.color; e.currentTarget.style.background = '#16192a'; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = '#1e2230'; e.currentTarget.style.background = '#13161e'; }}>
              <div style={{ fontSize: 28, marginBottom: 10 }}>{mod.icon}</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0', marginBottom: 4 }}>{mod.label}</div>
              <div style={{ fontSize: 12, color: '#4a5568' }}>{mod.desc}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}