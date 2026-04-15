import { useState } from 'react';
import { contentAPI } from '../services/api';

const PPT_STYLES = ['Professional', 'Academic', 'Creative', 'Minimal'];
const DOC_TYPES  = ['Assignment', 'Project Report', 'Lab Manual', 'IEEE Paper'];

export default function Content() {
  const [tab, setTab]           = useState('ppt');
  const [generating, setGen]    = useState(false);

  // PPT state
  const [pptForm, setPPT] = useState({ topic: '', num_slides: '10', style: 'Academic', college_name: "St. Martin's Engineering College", department: 'AI & Data Science', subject: '', guide_name: '' });

  // Doc state
  const [docForm, setDoc] = useState({ topic: '', doc_type: 'Assignment', subject: '', description: '', college_name: "St. Martin's Engineering College" });

  const download = (blob, filename) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  };

  const generatePPT = async (e) => {
    e.preventDefault(); setGen(true);
    try {
      const r = await contentAPI.generatePPT({ ...pptForm, num_slides: +pptForm.num_slides });
      download(r.data, `${pptForm.topic.replace(/\s+/g, '_')}.pptx`);
    } catch (err) { alert(err.response?.data?.detail || 'Generation failed'); }
    finally { setGen(false); }
  };

  const generateDoc = async (e) => {
    e.preventDefault(); setGen(true);
    try {
      const r = await contentAPI.generateDoc(docForm);
      download(r.data, `${docForm.topic.replace(/\s+/g, '_')}.docx`);
    } catch (err) { alert(err.response?.data?.detail || 'Generation failed'); }
    finally { setGen(false); }
  };

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={h1}>Content Generator</h1>
        <p style={sub}>Generate AI-powered PPTs, documents, and lab manuals with college templates</p>
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, background: '#13161e', border: '1px solid #1e2230', borderRadius: 10, padding: 4, width: 'fit-content' }}>
        {['ppt', 'document', 'lab manual'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ padding: '7px 18px', borderRadius: 7, border: 'none', cursor: 'pointer', background: tab === t ? '#1e2745' : 'transparent', color: tab === t ? '#818cf8' : '#4a5568', fontSize: 13, fontWeight: tab === t ? 600 : 400, textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'ppt' && (
        <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 20 }}>
          <div style={card}>
            <h3 style={cardTitle}>🎨 Generate PPT</h3>
            <form onSubmit={generatePPT}>
              <F label="Topic / Title" value={pptForm.topic} onChange={v => setPPT({ ...pptForm, topic: v })} placeholder="e.g. Machine Learning in Healthcare" required />
              <F label="Subject" value={pptForm.subject} onChange={v => setPPT({ ...pptForm, subject: v })} placeholder="e.g. Artificial Intelligence" />
              <F label="Number of Slides" value={pptForm.num_slides} onChange={v => setPPT({ ...pptForm, num_slides: v })} placeholder="10" type="number" />
              <div style={{ marginBottom: 14 }}>
                <label style={lbl}>Style</label>
                <select value={pptForm.style} onChange={e => setPPT({ ...pptForm, style: e.target.value })} style={{ ...inputStyle, appearance: 'none' }}>
                  {PPT_STYLES.map(s => <option key={s}>{s}</option>)}
                </select>
              </div>
              <F label="College Name" value={pptForm.college_name} onChange={v => setPPT({ ...pptForm, college_name: v })} placeholder="Your college" />
              <F label="Department" value={pptForm.department} onChange={v => setPPT({ ...pptForm, department: v })} placeholder="Department name" />
              <F label="Guide / Faculty Name" value={pptForm.guide_name} onChange={v => setPPT({ ...pptForm, guide_name: v })} placeholder="Mr./Mrs. Name" />
              <button type="submit" disabled={generating} style={{ ...amberBtn, width: '100%', marginTop: 8 }}>
                {generating ? '⏳ Generating PPT...' : '⬇ Generate & Download PPT'}
              </button>
            </form>
          </div>
          <div style={card}>
            <h3 style={cardTitle}>How PPT Generator works</h3>
            {[
              ['🧠 AI Content', 'LangChain + Gemini generates slide content for each slide'],
              ['🎨 Template Applied', 'python-pptx formats with your college branding'],
              ['📥 Auto Download', 'Ready-to-edit .pptx file downloads instantly'],
            ].map(([t, d]) => (
              <div key={t} style={{ display: 'flex', gap: 14, marginBottom: 16, padding: '14px 16px', background: '#0d0f14', borderRadius: 10 }}>
                <span style={{ fontSize: 24 }}>{t.split(' ')[0]}</span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 500, color: '#e2e8f0' }}>{t.split(' ').slice(1).join(' ')}</div>
                  <div style={{ fontSize: 13, color: '#4a5568', marginTop: 3 }}>{d}</div>
                </div>
              </div>
            ))}
            <div style={{ background: '#0c1a1a', border: '1px solid #065f46', borderRadius: 10, padding: '14px 16px', marginTop: 8 }}>
              <div style={{ fontSize: 13, color: '#6ee7b7', fontWeight: 500 }}>✓ Includes college header</div>
              <div style={{ fontSize: 13, color: '#6ee7b7' }}>✓ Title slide with guide & student names</div>
              <div style={{ fontSize: 13, color: '#6ee7b7' }}>✓ Content slides with AI-generated points</div>
              <div style={{ fontSize: 13, color: '#6ee7b7' }}>✓ Reference slide auto-added</div>
            </div>
          </div>
        </div>
      )}

      {tab === 'document' && (
        <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 20 }}>
          <div style={card}>
            <h3 style={cardTitle}>📄 Generate Document</h3>
            <form onSubmit={generateDoc}>
              <F label="Topic / Title" value={docForm.topic} onChange={v => setDoc({ ...docForm, topic: v })} placeholder="e.g. Study of Sorting Algorithms" required />
              <div style={{ marginBottom: 14 }}>
                <label style={lbl}>Document Type</label>
                <select value={docForm.doc_type} onChange={e => setDoc({ ...docForm, doc_type: e.target.value })} style={{ ...inputStyle, appearance: 'none' }}>
                  {DOC_TYPES.map(s => <option key={s}>{s}</option>)}
                </select>
              </div>
              <F label="Subject" value={docForm.subject} onChange={v => setDoc({ ...docForm, subject: v })} placeholder="Subject name" />
              <div style={{ marginBottom: 14 }}>
                <label style={lbl}>Description / Requirements</label>
                <textarea rows={3} placeholder="Any specific requirements..." value={docForm.description} onChange={e => setDoc({ ...docForm, description: e.target.value })} style={{ ...inputStyle, resize: 'vertical' }} />
              </div>
              <F label="College Name" value={docForm.college_name} onChange={v => setDoc({ ...docForm, college_name: v })} placeholder="Your college" />
              <button type="submit" disabled={generating} style={{ ...amberBtn, width: '100%', marginTop: 8 }}>
                {generating ? '⏳ Generating Document...' : '⬇ Generate & Download .docx'}
              </button>
            </form>
          </div>
          <div style={card}>
            <h3 style={cardTitle}>Document Types</h3>
            {[['Assignment', '📝', 'Structured assignment with intro, methodology, conclusion'],
              ['Project Report', '📊', 'IEEE-format project report with all chapters'],
              ['Lab Manual', '🔬', 'Experiment-wise lab manual with aim, procedure, output'],
              ['IEEE Paper', '📰', 'Research paper format with abstract, references'],
            ].map(([t, ic, d]) => (
              <div key={t} style={{ display: 'flex', gap: 12, marginBottom: 14, padding: '12px 14px', background: '#0d0f14', borderRadius: 10, cursor: 'pointer', border: docForm.doc_type === t ? '1px solid #6366f1' : '1px solid transparent' }}
                onClick={() => setDoc({ ...docForm, doc_type: t })}>
                <span style={{ fontSize: 22 }}>{ic}</span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: '#e2e8f0' }}>{t}</div>
                  <div style={{ fontSize: 12, color: '#4a5568' }}>{d}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'lab manual' && (
        <div style={card}>
          <h3 style={cardTitle}>🔬 Lab Manual Generator</h3>
          <p style={{ color: '#4a5568', fontSize: 14, marginBottom: 16 }}>Generate a complete lab manual with multiple experiments — use the Document tab and select "Lab Manual" type.</p>
          <button onClick={() => setTab('document')} style={amberBtn}>→ Go to Document Generator</button>
        </div>
      )}
    </div>
  );
}

function F({ label, value, onChange, placeholder, required, type = 'text' }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={lbl}>{label}</label>
      <input type={type} required={required} placeholder={placeholder} value={value} onChange={e => onChange(e.target.value)} style={inputStyle} />
    </div>
  );
}

const h1 = { fontSize: 24, fontWeight: 700, color: '#e2e8f0', margin: 0, letterSpacing: '-0.5px' };
const sub = { color: '#4a5568', fontSize: 13, margin: '4px 0 0' };
const card = { background: '#13161e', border: '1px solid #1e2230', borderRadius: 12, padding: '20px 22px' };
const cardTitle = { fontSize: 15, fontWeight: 600, color: '#e2e8f0', margin: '0 0 16px' };
const lbl = { display: 'block', color: '#9ca3af', fontSize: 12, marginBottom: 5 };
const inputStyle = { width: '100%', background: '#0d0f14', border: '1px solid #1e2230', borderRadius: 7, padding: '9px 12px', color: '#e2e8f0', fontSize: 13, outline: 'none', boxSizing: 'border-box' };
const amberBtn = { background: 'linear-gradient(135deg, #f59e0b, #d97706)', border: 'none', borderRadius: 8, padding: '9px 18px', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' };