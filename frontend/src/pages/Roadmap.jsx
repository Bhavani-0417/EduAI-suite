import { useEffect, useState } from 'react';
import { roadmapAPI } from '../services/api';

export default function Roadmap() {
  const [roadmaps, setRoadmaps] = useState([]);
  const [form, setForm]         = useState({ goal: '', current_skills: '', target_role: '', timeline_months: '6' });
  const [generating, setGen]    = useState(false);
  const [selected, setSelected] = useState(null);

  const load = () => roadmapAPI.getRoadmaps().then(r => setRoadmaps(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const generate = async (e) => {
    e.preventDefault(); setGen(true);
    try {
      const r = await roadmapAPI.generateRoadmap({ ...form, timeline_months: +form.timeline_months });
      load(); setSelected(r.data);
    } catch (err) { alert(err.response?.data?.detail || 'Error generating roadmap'); }
    finally { setGen(false); }
  };

  const markComplete = async (roadmapId, topicId) => {
    try { await roadmapAPI.markComplete(roadmapId, topicId); load(); } catch {}
  };

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={h1}>Goal & Roadmap Engine</h1>
        <p style={sub}>Set your career goal — LangGraph AI builds your personalized learning roadmap</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 20 }}>
        {/* Generate form */}
        <div>
          <div style={card}>
            <h3 style={cardTitle}>🎯 Generate Roadmap</h3>
            <form onSubmit={generate}>
              <div style={{ marginBottom: 13 }}>
                <label style={lbl}>Your Goal</label>
                <input required placeholder="e.g. Get a Data Science job at Google" value={form.goal} onChange={e => setForm({ ...form, goal: e.target.value })} style={inputStyle} />
              </div>
              <div style={{ marginBottom: 13 }}>
                <label style={lbl}>Current Skills</label>
                <textarea rows={3} placeholder="Python, basic ML, some SQL..." value={form.current_skills} onChange={e => setForm({ ...form, current_skills: e.target.value })} style={{ ...inputStyle, resize: 'vertical' }} />
              </div>
              <div style={{ marginBottom: 13 }}>
                <label style={lbl}>Target Role (optional)</label>
                <input placeholder="e.g. ML Engineer, Full-Stack Developer" value={form.target_role} onChange={e => setForm({ ...form, target_role: e.target.value })} style={inputStyle} />
              </div>
              <div style={{ marginBottom: 18 }}>
                <label style={lbl}>Timeline (months)</label>
                <select value={form.timeline_months} onChange={e => setForm({ ...form, timeline_months: e.target.value })} style={{ ...inputStyle, appearance: 'none' }}>
                  {[3, 6, 12, 18].map(m => <option key={m} value={m}>{m} months</option>)}
                </select>
              </div>
              <button type="submit" disabled={generating} style={{ ...purpleBtn, width: '100%' }}>
                {generating ? '⏳ LangGraph is planning...' : '✨ Generate AI Roadmap'}
              </button>
            </form>
          </div>

          {/* Past roadmaps */}
          {roadmaps.length > 0 && (
            <div style={{ ...card, marginTop: 16 }}>
              <h3 style={cardTitle}>Past Roadmaps</h3>
              {roadmaps.map(r => (
                <div key={r.id} onClick={() => setSelected(r)} style={{ padding: '10px 12px', background: selected?.id === r.id ? '#1e2745' : '#0d0f14', border: `1px solid ${selected?.id === r.id ? '#6366f1' : '#1e2230'}`, borderRadius: 8, marginBottom: 8, cursor: 'pointer' }}>
                  <div style={{ fontSize: 13, fontWeight: 500, color: '#e2e8f0' }}>{r.goal}</div>
                  <div style={{ fontSize: 12, color: '#4a5568', marginTop: 2 }}>{r.target_role} · {r.timeline_months}mo</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Roadmap display */}
        <div>
          {!selected && (
            <div style={{ ...card, textAlign: 'center', padding: '48px 24px' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>🗺️</div>
              <h3 style={{ color: '#6b7280', fontSize: 16, margin: 0 }}>Your roadmap will appear here</h3>
              <p style={{ color: '#4a5568', fontSize: 14, marginTop: 8 }}>Fill in your goal and click generate</p>
            </div>
          )}
          {selected && (
            <div style={card}>
              <div style={{ marginBottom: 20 }}>
                <h2 style={{ fontSize: 18, fontWeight: 700, color: '#e2e8f0', margin: '0 0 4px' }}>{selected.goal}</h2>
                {selected.target_role && <div style={{ fontSize: 13, color: '#818cf8' }}>→ {selected.target_role}</div>}
              </div>
              {/* Render roadmap content */}
              {selected.phases ? (
                selected.phases.map((phase, i) => (
                  <div key={i} style={{ marginBottom: 24 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                      <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 13, fontWeight: 700 }}>{i + 1}</div>
                      <div style={{ fontSize: 15, fontWeight: 600, color: '#e2e8f0' }}>{phase.title || `Phase ${i + 1}`}</div>
                      <div style={{ marginLeft: 'auto', fontSize: 12, color: '#4a5568' }}>{phase.duration}</div>
                    </div>
                    {phase.topics?.map((topic, j) => (
                      <div key={j} onClick={() => markComplete(selected.id, topic.id)} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', background: topic.completed ? '#0c1a0e' : '#0d0f14', border: `1px solid ${topic.completed ? '#14532d' : '#1e2230'}`, borderRadius: 8, marginBottom: 6, cursor: 'pointer' }}>
                        <div style={{ width: 18, height: 18, borderRadius: '50%', border: `2px solid ${topic.completed ? '#10b981' : '#1e2230'}`, background: topic.completed ? '#10b981' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, color: '#fff', flexShrink: 0 }}>
                          {topic.completed ? '✓' : ''}
                        </div>
                        <span style={{ fontSize: 13, color: topic.completed ? '#86efac' : '#9ca3af' }}>{typeof topic === 'string' ? topic : topic.name}</span>
                      </div>
                    ))}
                  </div>
                ))
              ) : (
                <div style={{ fontSize: 14, color: '#9ca3af', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                  {typeof selected.roadmap === 'string' ? selected.roadmap : JSON.stringify(selected, null, 2)}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const h1 = { fontSize: 24, fontWeight: 700, color: '#e2e8f0', margin: 0, letterSpacing: '-0.5px' };
const sub = { color: '#4a5568', fontSize: 13, margin: '4px 0 0' };
const card = { background: '#13161e', border: '1px solid #1e2230', borderRadius: 12, padding: '20px 22px' };
const cardTitle = { fontSize: 15, fontWeight: 600, color: '#e2e8f0', margin: '0 0 16px' };
const lbl = { display: 'block', color: '#9ca3af', fontSize: 12, marginBottom: 5 };
const inputStyle = { width: '100%', background: '#0d0f14', border: '1px solid #1e2230', borderRadius: 7, padding: '9px 12px', color: '#e2e8f0', fontSize: 13, outline: 'none', boxSizing: 'border-box' };
const purpleBtn = { background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', borderRadius: 8, padding: '9px 18px', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' };