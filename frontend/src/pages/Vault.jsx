import { useEffect, useState, useRef } from 'react';
import { vaultAPI } from '../services/api';

const DOC_TYPES = ['Certificate', 'Transcript', 'ID Card', 'Marksheet', 'Internship Letter', 'Other'];
const DOC_ICONS = { Certificate: '🏆', Transcript: '📜', 'ID Card': '🪪', Marksheet: '📊', 'Internship Letter': '💼', Other: '📄' };

export default function Vault() {
  const [docs, setDocs]       = useState([]);
  const [uploading, setUpl]   = useState(false);
  const [docType, setDocType] = useState('Certificate');
  const [file, setFile]       = useState(null);
  const [shareLinks, setLinks] = useState({});
  const [expiry, setExpiry]   = useState(24);
  const fileRef               = useRef();

  const load = () => vaultAPI.getDocuments().then(r => setDocs(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const upload = async (e) => {
    e.preventDefault();
    if (!file) return alert('Select a file first');
    setUpl(true);
    try {
      await vaultAPI.uploadDocument(file, docType);
      setFile(null); fileRef.current.value = ''; load();
    } catch (err) { alert(err.response?.data?.detail || 'Upload failed'); }
    finally { setUpl(false); }
  };

  const share = async (id) => {
    try {
      const r = await vaultAPI.shareDocument(id, expiry);
      setLinks(prev => ({ ...prev, [id]: r.data.share_url || r.data.url }));
    } catch (err) { alert(err.response?.data?.detail || 'Error generating link'); }
  };

  const deleteDoc = async (id) => {
    if (!confirm('Delete this document?')) return;
    await vaultAPI.deleteDocument(id).catch(() => {});
    load();
  };

  const grouped = DOC_TYPES.reduce((acc, t) => {
    acc[t] = docs.filter(d => d.doc_type === t);
    return acc;
  }, {});

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={h1}>Document Vault</h1>
        <p style={sub}>AES-256 encrypted storage · OCR · Time-limited secure share links</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 20 }}>
        {/* Upload */}
        <div>
          <div style={card}>
            <h3 style={cardTitle}>⬆ Upload Document</h3>
            <form onSubmit={upload}>
              <div style={{ marginBottom: 14 }}>
                <label style={lbl}>Document Type</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                  {DOC_TYPES.map(t => (
                    <button key={t} type="button" onClick={() => setDocType(t)} style={{
                      padding: '7px 8px', borderRadius: 7, border: `1px solid ${docType === t ? '#6366f1' : '#1e2230'}`,
                      background: docType === t ? '#1e2745' : '#0d0f14',
                      color: docType === t ? '#818cf8' : '#4a5568',
                      fontSize: 12, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5,
                    }}>
                      <span>{DOC_ICONS[t]}</span><span>{t}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: 18 }}>
                <label style={lbl}>File (PDF, Image)</label>
                <div style={{ border: '2px dashed #1e2230', borderRadius: 10, padding: '20px 16px', textAlign: 'center', cursor: 'pointer' }}
                  onClick={() => fileRef.current.click()}>
                  <div style={{ fontSize: 28, marginBottom: 6 }}>🔒</div>
                  <div style={{ color: '#4a5568', fontSize: 12 }}>{file ? file.name : 'Click to select file'}</div>
                  <div style={{ color: '#374151', fontSize: 11, marginTop: 4 }}>Encrypted with AES-256</div>
                </div>
                <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg" style={{ display: 'none' }} onChange={e => setFile(e.target.files[0])} />
              </div>

              <button type="submit" disabled={uploading} style={{ ...greenBtn, width: '100%' }}>
                {uploading ? '🔐 Encrypting & Uploading...' : '🔐 Encrypt & Upload'}
              </button>
            </form>
          </div>

          <div style={{ ...card, marginTop: 14 }}>
            <h3 style={cardTitle}>Share Settings</h3>
            <label style={lbl}>Link expiry</label>
            <select value={expiry} onChange={e => setExpiry(+e.target.value)} style={{ ...inputStyle, appearance: 'none' }}>
              {[1, 6, 24, 48, 168].map(h => <option key={h} value={h}>{h < 24 ? `${h}h` : `${h / 24}d`}</option>)}
            </select>
          </div>

          <div style={{ ...card, marginTop: 14, background: '#0c1a1a', border: '1px solid #065f46' }}>
            <div style={{ fontSize: 13, color: '#6ee7b7', fontWeight: 500, marginBottom: 6 }}>🔒 Security Features</div>
            {['AES-256 encryption at rest', 'Time-limited share links', 'OCR on uploaded scans', 'Signed URL generation'].map(f => (
              <div key={f} style={{ fontSize: 12, color: '#34d399', marginBottom: 3 }}>✓ {f}</div>
            ))}
          </div>
        </div>

        {/* Documents */}
        <div style={card}>
          <h3 style={cardTitle}>My Documents ({docs.length})</h3>
          {docs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 16px', color: '#4a5568', fontSize: 14 }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>🔒</div>
              No documents yet. Upload your first document securely!
            </div>
          ) : (
            DOC_TYPES.map(type => grouped[type]?.length > 0 && (
              <div key={type} style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 12, color: '#4a5568', fontWeight: 500, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {DOC_ICONS[type]} {type}s ({grouped[type].length})
                </div>
                {grouped[type].map(doc => (
                  <div key={doc.id} style={{ background: '#0d0f14', border: '1px solid #1e2230', borderRadius: 10, padding: '12px 14px', marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ fontSize: 24 }}>{DOC_ICONS[doc.doc_type] || '📄'}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, fontWeight: 500, color: '#e2e8f0' }}>{doc.file_name}</div>
                        <div style={{ fontSize: 11, color: '#4a5568', marginTop: 2 }}>
                          {new Date(doc.uploaded_at).toLocaleDateString()} · Encrypted ✓
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button onClick={() => share(doc.id)} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid #1e4620', background: '#0c1a0e', color: '#10b981', fontSize: 12, cursor: 'pointer' }}>
                          🔗 Share
                        </button>
                        <button onClick={() => deleteDoc(doc.id)} style={{ padding: '5px 10px', borderRadius: 6, border: '1px solid #7f1d1d', background: '#1a0c0c', color: '#ef4444', fontSize: 12, cursor: 'pointer' }}>
                          ×
                        </button>
                      </div>
                    </div>
                    {shareLinks[doc.id] && (
                      <div style={{ marginTop: 10, padding: '8px 10px', background: '#0c1a1a', borderRadius: 6, border: '1px solid #065f46' }}>
                        <div style={{ fontSize: 11, color: '#4a5568', marginBottom: 4 }}>Share link (expires in {expiry}h):</div>
                        <div style={{ fontSize: 12, color: '#6ee7b7', wordBreak: 'break-all', cursor: 'pointer' }}
                          onClick={() => navigator.clipboard.writeText(shareLinks[doc.id])}>
                          📋 {shareLinks[doc.id]}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ))
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
const greenBtn = { background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none', borderRadius: 8, padding: '9px 18px', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' };