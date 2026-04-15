import { useEffect, useState } from 'react';
import { academicAPI } from '../services/api';

export default function Academic() {
  const [marks, setMarks]           = useState([]);
  const [cgpa, setCgpa]             = useState(null);
  const [weaknesses, setWeaknesses] = useState(null);
  const [roadmap, setRoadmap]       = useState(null);
  const [form, setForm]             = useState({ subject: '', marks_obtained: '', total_marks: '100', semester: '1' });
  const [loading, setLoading]       = useState(false);
  const [tab, setTab]               = useState('marks');

  const load = () => {
    academicAPI.getMarks().then(r => setMarks(r.data)).catch(() => {});
    academicAPI.getCGPA().then(r => setCgpa(r.data)).catch(() => {});
    academicAPI.getWeaknesses().then(r => setWeaknesses(r.data)).catch(() => {});
  };

  useEffect(() => { load(); }, []);

  const addMark = async (e) => {
    e.preventDefault(); setLoading(true);
    try {
      await academicAPI.addMark({ ...form, marks_obtained: +form.marks_obtained, total_marks: +form.total_marks, semester: +form.semester });
      setForm({ subject: '', marks_obtained: '', total_marks: '100', semester: form.semester });
      load();
    } catch (err) { alert(err.response?.data?.detail || 'Error adding mark'); }
    finally { setLoading(false); }
  };

  const deleteMark = async (id) => {
    await academicAPI.deleteMark(id);
    load();
  };

  const getAIRoadmap = async () => {
    try {
      const r = await academicAPI.getRoadmap();
      setRoadmap(r.data); setTab('roadmap');
    } catch { alert('Add marks first to generate roadmap'); }
  };

  const pct = (m) => Math.round((m.marks_obtained / m.total_marks) * 100);
  const pctColor = (p) => p >= 70 ? '#10b981' : p >= 50 ? '#f59e0b' : '#ef4444';

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <h1 style={h1}>Academic Dashboard</h1>
          <p style={sub}>Track marks, CGPA, and get AI improvement plans</p>
        </div>
        <button onClick={getAIRoadmap} style={purpleBtn}>✨ Generate AI Roadmap</button>
      </div>

      {/* CGPA card */}
      {cgpa && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 28 }}>
          <Stat label="CGPA" value={cgpa.cgpa} color="#6366f1" />
          <Stat label="Percentage" value={`${cgpa.percentage}%`} color="#10b981" />
          <Stat label="Subjects" value={marks.length} color="#f59e0b" />
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, background: '#13161e', border: '1px solid #1e2230', borderRadius: 10, padding: 4, width: 'fit-content' }}>
        {['marks', 'analysis', 'roadmap'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '7px 18px', borderRadius: 7, border: 'none', cursor: 'pointer',
            background: tab === t ? '#1e2745' : 'transparent',
            color: tab === t ? '#818cf8' : '#4a5568',
            fontSize: 13, fontWeight: tab === t ? 600 : 400, textTransform: 'capitalize',
          }}>{t}</button>
        ))}
      </div>

      {/* Marks Tab */}
      {tab === 'marks' && (
        <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 20 }}>
          {/* Add form */}
          <div style={card}>
            <h3 style={cardTitle}>Add Marks</h3>
            <form onSubmit={addMark}>
              {[['Subject', 'subject', 'text', 'e.g. DBMS'],
                ['Marks Obtained', 'marks_obtained', 'number', '78'],
                ['Total Marks', 'total_marks', 'number', '100'],
                ['Semester', 'semester', 'number', '3']].map(([label, key, type, ph]) => (
                <div key={key} style={{ marginBottom: 12 }}>
                  <label style={lbl}>{label}</label>
                  <input type={type} required placeholder={ph} value={form[key]}
                    onChange={e => setForm({ ...form, [key]: e.target.value })}
                    style={inputStyle} />
                </div>
              ))}
              <button type="submit" disabled={loading} style={{ ...purpleBtn, width: '100%', marginTop: 4 }}>
                {loading ? 'Adding...' : '+ Add Mark'}
              </button>
            </form>
          </div>

          {/* Marks table */}
          <div style={card}>
            <h3 style={cardTitle}>Your Marks ({marks.length})</h3>
            {marks.length === 0 ? (
              <p style={{ color: '#4a5568', fontSize: 14 }}>No marks added yet. Add your first subject!</p>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                  <thead>
                    <tr>{['Subject', 'Marks', 'Total', 'Percentage', 'Sem', ''].map(h => (
                      <th key={h} style={{ textAlign: 'left', color: '#4a5568', padding: '8px 10px', borderBottom: '1px solid #1e2230', fontWeight: 500, fontSize: 12 }}>{h}</th>
                    ))}</tr>
                  </thead>
                  <tbody>
                    {marks.map(m => (
                      <tr key={m.id}>
                        <td style={td}>{m.subject}</td>
                        <td style={td}>{m.marks_obtained}</td>
                        <td style={td}>{m.total_marks}</td>
                        <td style={td}>
                          <span style={{ color: pctColor(pct(m)), fontWeight: 600 }}>{pct(m)}%</span>
                        </td>
                        <td style={td}>Sem {m.semester}</td>
                        <td style={td}>
                          <button onClick={() => deleteMark(m.id)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: 16 }}>×</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Analysis Tab */}
      {tab === 'analysis' && weaknesses && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <div style={card}>
            <h3 style={{ ...cardTitle, color: '#ef4444' }}>⚠️ Weak Subjects</h3>
            {weaknesses.weak_subjects?.length === 0 ? (
              <p style={{ color: '#10b981', fontSize: 14 }}>No weak subjects! 🎉</p>
            ) : (
              weaknesses.weak_subjects?.map(s => (
                <div key={s.subject} style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontSize: 14, color: '#e2e8f0' }}>{s.subject}</span>
                    <span style={{ fontSize: 14, color: '#ef4444', fontWeight: 600 }}>{Math.round(s.percentage)}%</span>
                  </div>
                  <div style={{ height: 6, background: '#1e2230', borderRadius: 3 }}>
                    <div style={{ height: '100%', width: `${s.percentage}%`, background: '#ef4444', borderRadius: 3 }} />
                  </div>
                  <p style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>{weaknesses.improvement_tips?.[s.subject]}</p>
                </div>
              ))
            )}
          </div>
          <div style={card}>
            <h3 style={{ ...cardTitle, color: '#10b981' }}>✅ Strong Subjects</h3>
            {weaknesses.strong_subjects?.map(s => (
              <div key={s} style={{ padding: '10px 14px', background: '#0d150e', border: '1px solid #14532d', borderRadius: 8, marginBottom: 8, color: '#86efac', fontSize: 14 }}>
                {s}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Roadmap Tab */}
      {tab === 'roadmap' && roadmap && (
        <div style={card}>
          <h3 style={cardTitle}>🗺️ AI Improvement Roadmap</h3>
          <div style={{ fontSize: 14, color: '#9ca3af', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
            {typeof roadmap === 'string' ? roadmap : roadmap.roadmap || JSON.stringify(roadmap, null, 2)}
          </div>
        </div>
      )}
      {tab === 'roadmap' && !roadmap && (
        <div style={card}>
          <p style={{ color: '#4a5568', fontSize: 14 }}>Click "Generate AI Roadmap" above to get your personalized improvement plan.</p>
        </div>
      )}
    </div>
  );
}

const Stat = ({ label, value, color }) => (
  <div style={{ background: '#13161e', border: '1px solid #1e2230', borderRadius: 12, padding: '16px 20px' }}>
    <div style={{ fontSize: 12, color: '#4a5568', marginBottom: 6 }}>{label}</div>
    <div style={{ fontSize: 30, fontWeight: 700, color }}>{value}</div>
  </div>
);

const h1 = { fontSize: 24, fontWeight: 700, color: '#e2e8f0', margin: 0, letterSpacing: '-0.5px' };
const sub = { color: '#4a5568', fontSize: 13, margin: '4px 0 0' };
const card = { background: '#13161e', border: '1px solid #1e2230', borderRadius: 12, padding: '20px 22px' };
const cardTitle = { fontSize: 15, fontWeight: 600, color: '#e2e8f0', margin: '0 0 16px' };
const lbl = { display: 'block', color: '#9ca3af', fontSize: 12, marginBottom: 5 };
const inputStyle = { width: '100%', background: '#0d0f14', border: '1px solid #1e2230', borderRadius: 7, padding: '9px 12px', color: '#e2e8f0', fontSize: 13, outline: 'none', boxSizing: 'border-box' };
const purpleBtn = { background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', borderRadius: 8, padding: '9px 18px', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' };
const td = { padding: '10px', borderBottom: '1px solid #1e2230', color: '#9ca3af' };