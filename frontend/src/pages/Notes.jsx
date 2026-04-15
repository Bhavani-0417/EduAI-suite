import { useEffect, useState, useRef } from 'react';
import { notesAPI } from '../services/api';

export default function Notes() {
  const [notes, setNotes]     = useState([]);
  const [tab, setTab]         = useState('upload');
  const [subject, setSubject] = useState('');
  const [topic, setTopic]     = useState('');
  const [file, setFile]       = useState(null);
  const [uploading, setUploading] = useState(false);
  const [question, setQuestion]   = useState('');
  const [answer, setAnswer]       = useState('');
  const [asking, setAsking]       = useState(false);
  const fileRef = useRef();

  const load = () => notesAPI.getNotes().then(r => setNotes(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const uploadNote = async (e) => {
    e.preventDefault();
    if (!file) return alert('Select a file first');
    setUploading(true);
    try {
      await notesAPI.uploadNote(file, subject, topic);
      setFile(null); setSubject(''); setTopic('');
      fileRef.current.value = '';
      load();
    } catch (err) { alert(err.response?.data?.detail || 'Upload failed'); }
    finally { setUploading(false); }
  };

  const askQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    setAsking(true); setAnswer('');
    try {
      const r = await notesAPI.askQuestion(question, subject || undefined);
      setAnswer(r.data.answer || JSON.stringify(r.data));
    } catch (err) { setAnswer(err.response?.data?.detail || 'Error getting answer'); }
    finally { setAsking(false); }
  };

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={h1}>Knowledge Hub</h1>
        <p style={sub}>Upload notes, PDFs, images — ask questions using RAG AI</p>
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, background: '#13161e', border: '1px solid #1e2230', borderRadius: 10, padding: 4, width: 'fit-content' }}>
        {['upload', 'my notes', 'ask AI'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ padding: '7px 18px', borderRadius: 7, border: 'none', cursor: 'pointer', background: tab === t ? '#1e2745' : 'transparent', color: tab === t ? '#818cf8' : '#4a5568', fontSize: 13, fontWeight: tab === t ? 600 : 400, textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'upload' && (
        <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 20 }}>
          <div style={card}>
            <h3 style={cardTitle}>Upload Notes</h3>
            <form onSubmit={uploadNote}>
              <div style={{ marginBottom: 14 }}>
                <label style={lbl}>Subject</label>
                <input required placeholder="e.g. DBMS, OS, Networks" value={subject} onChange={e => setSubject(e.target.value)} style={inputStyle} />
              </div>
              <div style={{ marginBottom: 14 }}>
                <label style={lbl}>Topic (optional)</label>
                <input placeholder="e.g. Normalization" value={topic} onChange={e => setTopic(e.target.value)} style={inputStyle} />
              </div>
              <div style={{ marginBottom: 18 }}>
                <label style={lbl}>File (PDF, Image, PPT)</label>
                <div style={{ border: '2px dashed #1e2230', borderRadius: 10, padding: '24px 16px', textAlign: 'center', cursor: 'pointer' }}
                  onClick={() => fileRef.current.click()}>
                  <div style={{ fontSize: 28, marginBottom: 8 }}>📄</div>
                  <div style={{ color: '#4a5568', fontSize: 13 }}>{file ? file.name : 'Click to select file'}</div>
                </div>
                <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg,.pptx" style={{ display: 'none' }} onChange={e => setFile(e.target.files[0])} />
              </div>
              <button type="submit" disabled={uploading} style={{ ...purpleBtn, width: '100%' }}>
                {uploading ? 'Uploading & Processing...' : '⬆ Upload & Index Note'}
              </button>
            </form>
          </div>
          <div style={card}>
            <h3 style={cardTitle}>How it works</h3>
            {[['📄 Upload', 'PDF, image, or PPT note uploaded'],
              ['🔍 OCR/Extract', 'Text extracted via PyMuPDF or Tesseract'],
              ['🏷 Auto-classify', 'AI identifies subject, topic, chapter'],
              ['🧩 Chunk & Embed', 'Split into 500-token chunks, vectorized'],
              ['📦 Store in ChromaDB', 'Searchable vector database'],
              ['💬 Ask questions', 'RAG retrieves relevant chunks → Gemini answers'],
            ].map(([step, desc]) => (
              <div key={step} style={{ display: 'flex', gap: 12, marginBottom: 14 }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, background: '#1e2230', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, flexShrink: 0 }}>{step.split(' ')[0]}</div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: '#e2e8f0' }}>{step.split(' ').slice(1).join(' ')}</div>
                  <div style={{ fontSize: 12, color: '#4a5568' }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'my notes' && (
        <div style={card}>
          <h3 style={cardTitle}>My Notes ({notes.length})</h3>
          {notes.length === 0 ? (
            <p style={{ color: '#4a5568', fontSize: 14 }}>No notes yet. Upload your first note!</p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
              {notes.map(n => (
                <div key={n.id} style={{ background: '#0d0f14', border: '1px solid #1e2230', borderRadius: 10, padding: '14px 16px' }}>
                  <div style={{ fontSize: 22, marginBottom: 8 }}>📚</div>
                  <div style={{ fontSize: 14, fontWeight: 500, color: '#e2e8f0', marginBottom: 4 }}>{n.file_name}</div>
                  <div style={{ fontSize: 12, color: '#818cf8', marginBottom: 4 }}>{n.subject}</div>
                  {n.summary && <div style={{ fontSize: 12, color: '#4a5568', marginBottom: 8, lineHeight: 1.5 }}>{n.summary.slice(0, 100)}...</div>}
                  <button onClick={async () => { await notesAPI.deleteNote(n.id); load(); }} style={{ background: 'none', border: '1px solid #7f1d1d', borderRadius: 6, padding: '4px 10px', color: '#ef4444', cursor: 'pointer', fontSize: 12 }}>Delete</button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'ask AI' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <div style={card}>
            <h3 style={cardTitle}>💬 Ask from Your Notes (RAG)</h3>
            <form onSubmit={askQuestion}>
              <div style={{ marginBottom: 14 }}>
                <label style={lbl}>Filter by Subject (optional)</label>
                <input placeholder="Leave blank to search all notes" value={subject} onChange={e => setSubject(e.target.value)} style={inputStyle} />
              </div>
              <div style={{ marginBottom: 16 }}>
                <label style={lbl}>Your Question</label>
                <textarea required rows={4} placeholder="Ask anything from your uploaded notes..." value={question} onChange={e => setQuestion(e.target.value)} style={{ ...inputStyle, resize: 'vertical', lineHeight: 1.6 }} />
              </div>
              <button type="submit" disabled={asking} style={{ ...purpleBtn, width: '100%' }}>
                {asking ? 'Searching notes & generating...' : '🔍 Ask AI'}
              </button>
            </form>
          </div>
          <div style={card}>
            <h3 style={cardTitle}>Answer</h3>
            {asking && <p style={{ color: '#818cf8', fontSize: 14 }}>🔍 Searching your notes...</p>}
            {answer && <div style={{ fontSize: 14, color: '#9ca3af', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{answer}</div>}
            {!asking && !answer && <p style={{ color: '#4a5568', fontSize: 14 }}>Your answer will appear here.</p>}
          </div>
        </div>
      )}
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