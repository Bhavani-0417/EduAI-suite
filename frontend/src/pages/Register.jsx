import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../services/api';

const COLLEGES = [
  { id: 'smec', name: "St. Martin's Engineering College" },
  { id: 'jntuh', name: 'JNTUH' },
  { id: 'osmania', name: 'Osmania University' },
  { id: 'bits', name: 'BITS Pilani Hyderabad' },
  { id: 'iit', name: 'IIT Hyderabad' },
];

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '', college_id: '', branch: '', year: '2', role: 'student' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError('');
    try {
      await authAPI.register(form);
      navigate('/login');
    } catch (err) {
      const backendError = err.response?.data?.detail;

if (Array.isArray(backendError)) {
  setError(backendError[0]?.msg || "Registration failed");
} else if (typeof backendError === "string") {
  setError(backendError);
} else {
  setError("Registration failed");
}
    } finally { setLoading(false); }
  };

  const f = (key) => ({ value: form[key], onChange: (e) => setForm({ ...form, [key]: e.target.value }) });

  return (
    <div style={{ minHeight: '100vh', background: '#0d0f14', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans', sans-serif", padding: 24 }}>
      <div style={{ width: '100%', maxWidth: 460 }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ width: 48, height: 48, borderRadius: 14, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, margin: '0 auto 12px' }}>E</div>
          <h1 style={{ color: '#e2e8f0', fontSize: 22, fontWeight: 700, margin: 0 }}>Create Account</h1>
        </div>

        <div style={{ background: '#13161e', border: '1px solid #1e2230', borderRadius: 16, padding: 28 }}>
          {error && <div style={{ background: '#1a0c0c', border: '1px solid #ef4444', borderRadius: 8, padding: '10px 14px', marginBottom: 18, color: '#ef4444', fontSize: 13 }}>{error}</div>}
          <form onSubmit={handleSubmit}>
            {[['Full Name', 'name', 'text', 'Your full name'],
              ['Email', 'email', 'email', 'you@college.edu'],
              ['Password', 'password', 'password', '••••••••']].map(([label, key, type, ph]) => (
              <div key={key} style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 5 }}>{label}</label>
                <input type={type} required placeholder={ph} {...f(key)} style={inputStyle} />
              </div>
            ))}

            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 5 }}>College</label>
              <select required {...f('college_id')} style={{ ...inputStyle, appearance: 'none' }}>
                <option value="">-- Select --</option>
                {COLLEGES.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 5 }}>Branch</label>
                <select {...f('branch')} style={{ ...inputStyle, appearance: 'none' }}>
                  <option value="">-- Select --</option>
                  <option value="AI&DS">B.Tech AI & DS</option>
                  <option value="CSE">B.Tech CSE</option>
                  <option value="ECE">B.Tech ECE</option>
                  <option value="MBBS">MBBS</option>
                  <option value="Intermediate">Intermediate</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 5 }}>Year</label>
                <select {...f('year')} style={{ ...inputStyle, appearance: 'none' }}>
                  <option value="1">1st Year</option>
                  <option value="2">2nd Year</option>
                  <option value="3">3rd Year</option>
                  <option value="4">4th Year</option>
                </select>
              </div>
            </div>

            <button type="submit" disabled={loading} style={btnStyle}>
              {loading ? 'Creating...' : 'Create Account →'}
            </button>
          </form>
          <p style={{ textAlign: 'center', color: '#4a5568', fontSize: 13, marginTop: 18, marginBottom: 0 }}>
            Already have an account? <Link to="/login" style={{ color: '#818cf8', textDecoration: 'none' }}>Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

const inputStyle = { width: '100%', background: '#0d0f14', border: '1px solid #1e2230', borderRadius: 8, padding: '10px 14px', color: '#e2e8f0', fontSize: 14, outline: 'none', boxSizing: 'border-box' };
const btnStyle = { width: '100%', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', borderRadius: 8, padding: '11px', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer', marginTop: 8 };