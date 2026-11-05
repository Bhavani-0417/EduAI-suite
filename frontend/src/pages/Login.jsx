import { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [message] = useState(location.state?.message || '');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(form);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0d0f14', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans', sans-serif", padding: 24 }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{ width: 56, height: 56, borderRadius: 16, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, margin: '0 auto 16px' }}>E</div>
          <h1 style={{ color: '#e2e8f0', fontSize: 24, fontWeight: 700, margin: 0, letterSpacing: '-0.5px' }}>EduAI Suite</h1>
          <p style={{ color: '#4a5568', fontSize: 14, margin: '6px 0 0' }}>AI-Powered Academic Platform</p>
        </div>

        <div style={{ background: '#13161e', border: '1px solid #1e2230', borderRadius: 16, padding: 32 }}>
          <h2 style={{ color: '#e2e8f0', fontSize: 18, fontWeight: 600, margin: '0 0 24px', letterSpacing: '-0.3px' }}>Sign in to your account</h2>
          {message && <div role="status" style={{ background: '#0c1a15', border: '1px solid #16a34a', borderRadius: 8, padding: '10px 14px', marginBottom: 20, color: '#86efac', fontSize: 13 }}>{message}</div>}
          {error && <div role="alert" style={{ background: '#1a0c0c', border: '1px solid #ef4444', borderRadius: 8, padding: '10px 14px', marginBottom: 20, color: '#ef4444', fontSize: 13 }}>{error}</div>}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 16 }}>
              <label htmlFor="email" style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 6 }}>Email address</label>
              <input id="email" type="email" required autoComplete="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="you@college.edu" style={inputStyle} />
            </div>
            <div style={{ marginBottom: 24 }}>
              <label htmlFor="password" style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 6 }}>Password</label>
              <input id="password" type="password" required autoComplete="current-password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder="Your password" style={inputStyle} />
            </div>
            <button type="submit" disabled={loading} style={btnStyle}>{loading ? 'Signing in…' : 'Sign In →'}</button>
          </form>

          <p style={{ textAlign: 'center', color: '#4a5568', fontSize: 13, marginTop: 20, marginBottom: 0 }}>
            Don't have an account? <Link to="/register" style={{ color: '#818cf8', textDecoration: 'none' }}>Create one</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

const inputStyle = { width: '100%', background: '#0d0f14', border: '1px solid #1e2230', borderRadius: 8, padding: '10px 14px', color: '#e2e8f0', fontSize: 14, outline: 'none', boxSizing: 'border-box' };
const btnStyle = { width: '100%', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', borderRadius: 8, padding: '12px', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer', letterSpacing: '-0.2px' };
