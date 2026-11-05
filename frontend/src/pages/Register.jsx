import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api, { authAPI } from '../services/api';

const BRANCHES = [
  { value: 'btech_aids', label: 'B.Tech AI & DS' },
  { value: 'btech_cs', label: 'B.Tech CSE' },
  { value: 'btech_ece', label: 'B.Tech ECE' },
  { value: 'mbbs', label: 'MBBS' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'school', label: 'School' },
  { value: 'other', label: 'Other' },
];

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '', email: '', password: '', college_id: '',
    branch: '', year: '2',
  });
  const [colleges, setColleges] = useState([]);
  const [collegesLoading, setCollegesLoading] = useState(true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    api.get('/api/colleges/')
      .then(({ data }) => {
        if (active) setColleges(data.colleges || []);
      })
      .catch(() => {
        if (active) setError('Unable to load colleges. Please refresh or contact the administrator.');
      })
      .finally(() => {
        if (active) setCollegesLoading(false);
      });
    return () => { active = false; };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await authAPI.register({ ...form, year: Number(form.year) });
      navigate('/login', { state: { message: 'Account created. Please sign in.' } });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail)
        ? detail.map(item => item.msg).join(', ')
        : (detail || 'Registration failed. Please check your details.'));
    } finally {
      setLoading(false);
    }
  };

  const update = (key) => (e) => setForm(current => ({ ...current, [key]: e.target.value }));

  return (
    <div style={{ minHeight: '100vh', background: '#0d0f14', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans', sans-serif", padding: 24 }}>
      <div style={{ width: '100%', maxWidth: 460 }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ width: 48, height: 48, borderRadius: 14, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, margin: '0 auto 12px' }}>E</div>
          <h1 style={{ color: '#e2e8f0', fontSize: 22, fontWeight: 700, margin: 0 }}>Create Account</h1>
          <p style={{ color: '#9ca3af', fontSize: 13 }}>New accounts receive the student role.</p>
        </div>

        <div style={{ background: '#13161e', border: '1px solid #1e2230', borderRadius: 16, padding: 28 }}>
          {error && <div role="alert" style={{ background: '#1a0c0c', border: '1px solid #ef4444', borderRadius: 8, padding: '10px 14px', marginBottom: 18, color: '#ef4444', fontSize: 13 }}>{error}</div>}
          <form onSubmit={handleSubmit}>
            {[['Full Name', 'name', 'text', 'Your full name'], ['Email', 'email', 'email', 'you@college.edu'], ['Password', 'password', 'password', 'At least 12 characters']].map(([label, key, type, ph]) => (
              <div key={key} style={{ marginBottom: 14 }}>
                <label htmlFor={key} style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 5 }}>{label}</label>
                <input id={key} type={type} required minLength={key === 'password' ? 12 : undefined} maxLength={key === 'password' ? 72 : undefined} autoComplete={key === 'password' ? 'new-password' : key === 'email' ? 'email' : 'name'} placeholder={ph} value={form[key]} onChange={update(key)} style={inputStyle} />
              </div>
            ))}

            <div style={{ marginBottom: 14 }}>
              <label htmlFor="college_id" style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 5 }}>College</label>
              <select id="college_id" required value={form.college_id} onChange={update('college_id')} disabled={collegesLoading || colleges.length === 0} style={{ ...inputStyle, appearance: 'none' }}>
                <option value="">{collegesLoading ? 'Loading colleges…' : '-- Select your college --'}</option>
                {colleges.map(college => <option key={college.id} value={college.id}>{college.name}{college.city ? ` — ${college.city}` : ''}</option>)}
              </select>
              {!collegesLoading && colleges.length === 0 && <p style={{ color: '#fca5a5', fontSize: 12 }}>No colleges are available yet. Please contact the administrator.</p>}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
              <div>
                <label htmlFor="branch" style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 5 }}>Branch</label>
                <select id="branch" required value={form.branch} onChange={update('branch')} style={{ ...inputStyle, appearance: 'none' }}>
                  <option value="">-- Select --</option>
                  {BRANCHES.map(branch => <option key={branch.value} value={branch.value}>{branch.label}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="year" style={{ display: 'block', color: '#9ca3af', fontSize: 13, marginBottom: 5 }}>Year</label>
                <select id="year" value={form.year} onChange={update('year')} style={{ ...inputStyle, appearance: 'none' }}>
                  <option value="1">1st Year</option><option value="2">2nd Year</option>
                  <option value="3">3rd Year</option><option value="4">4th Year</option>
                </select>
              </div>
            </div>

            <button type="submit" disabled={loading || collegesLoading || colleges.length === 0} style={btnStyle}>
              {loading ? 'Creating…' : 'Create Account →'}
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
