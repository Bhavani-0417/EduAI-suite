import { useState } from 'react';
import { codeAPI } from '../services/api';

const LANGUAGES = ['Python', 'Java', 'C', 'C++', 'JavaScript', 'SQL'];
const ACTIONS = [
  { key: 'explain', label: '🔍 Explain Error', color: '#6366f1', desc: 'Understand what went wrong' },
  { key: 'fix',     label: '🔧 Fix Code',       color: '#10b981', desc: 'Get corrected code' },
  { key: 'review',  label: '✨ Review Code',    color: '#f59e0b', desc: 'Quality & best practices' },
];

export default function CodeExplainer() {
  const [code, setCode]       = useState('');
  const [error, setError]     = useState('');
  const [lang, setLang]       = useState('Python');
  const [action, setAction]   = useState('explain');
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!code.trim()) return alert('Paste your code first');
    setLoading(true); setResult(null);
    try {
      let r;
      if (action === 'explain') r = await codeAPI.explainError({ code, error_message: error, language: lang.toLowerCase() });
      else if (action === 'fix')    r = await codeAPI.fixCode({ code, error_message: error, language: lang.toLowerCase() });
      else                          r = await codeAPI.reviewCode({ code, language: lang });
      setResult(r.data);
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={h1}>Code Explainer</h1>
        <p style={sub}>AI explains errors, fixes bugs, and reviews code quality — Python, Java, C, JS, SQL</p>
      </div>

      {/* Action selector */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        {ACTIONS.map(a => (
          <button key={a.key} onClick={() => setAction(a.key)} style={{
            flex: 1, padding: '12px 16px', borderRadius: 10,
            border: `1px solid ${action === a.key ? a.color : '#1e2230'}`,
            background: action === a.key ? a.color + '22' : '#13161e',
            color: action === a.key ? a.color : '#4a5568',
            cursor: 'pointer', textAlign: 'left',
          }}>
            <div style={{ fontSize: 14, fontWeight: 600 }}>{a.label}</div>
            <div style={{ fontSize: 12, marginTop: 2, opacity: 0.7 }}>{a.desc}</div>
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Input */}
        <div style={card}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <h3 style={{ ...cardTitle, margin: 0 }}>Your Code</h3>
            <div style={{ display: 'flex', gap: 4 }}>
              {LANGUAGES.map(l => (
                <button key={l} onClick={() => setLang(l)} style={{
                  padding: '4px 10px', borderRadius: 5, border: `1px solid ${lang === l ? '#6366f1' : '#1e2230'}`,
                  background: lang === l ? '#1e2745' : 'transparent',
                  color: lang === l ? '#818cf8' : '#4a5568', fontSize: 11, cursor: 'pointer',
                }}>{l}</button>
              ))}
            </div>
          </div>

          <textarea
            rows={14}
            placeholder={`Paste your ${lang} code here...`}
            value={code}
            onChange={e => setCode(e.target.value)}
            style={{ ...inputStyle, fontFamily: 'monospace', fontSize: 13, lineHeight: 1.6, resize: 'vertical' }}
          />

          {(action === 'explain' || action === 'fix') && (
            <div style={{ marginTop: 12 }}>
              <label style={lbl}>Error Message (optional but helps)</label>
              <textarea
                rows={3}
                placeholder="Paste the error/traceback here..."
                value={error}
                onChange={e => setError(e.target.value)}
                style={{ ...inputStyle, fontFamily: 'monospace', fontSize: 12, resize: 'vertical' }}
              />
            </div>
          )}

          <button onClick={run} disabled={loading} style={{ ...actionBtns[action], width: '100%', marginTop: 14 }}>
            {loading ? '⏳ Analyzing with Gemini...' : ACTIONS.find(a => a.key === action)?.label}
          </button>
        </div>

        {/* Output */}
        <div style={card}>
          <h3 style={cardTitle}>
            {action === 'explain' ? '🔍 Explanation' : action === 'fix' ? '🔧 Fixed Code' : '✨ Code Review'}
          </h3>

          {loading && (
            <div style={{ color: '#818cf8', fontSize: 14, textAlign: 'center', padding: '40px 0' }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>🧠</div>
              Gemini 1.5 Flash analyzing your code...
            </div>
          )}

          {!loading && !result && (
            <div style={{ color: '#4a5568', fontSize: 14, textAlign: 'center', padding: '40px 0' }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>💡</div>
              Results will appear here
            </div>
          )}

          {result && (
            <div>
              {result.simple_explanation && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 12, color: '#6366f1', fontWeight: 500, marginBottom: 8 }}>
                    Explanation
                  </div>
                  <div style={{ fontSize: 14, color: '#9ca3af', whiteSpace: 'pre-wrap' }}>
                    {result.simple_explanation}
                  </div>
                </div>
          )}

              {result.fixed_code && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                    <div style={{ fontSize: 12, color: '#10b981', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Fixed Code</div>
                    <button onClick={() => navigator.clipboard.writeText(result.fixed_code)} style={{ padding: '3px 10px', borderRadius: 5, border: '1px solid #1e2230', background: 'transparent', color: '#6b7280', fontSize: 11, cursor: 'pointer' }}>📋 Copy</button>
                  </div>
                  <pre style={{ background: '#0d0f14', border: '1px solid #1e2230', borderRadius: 8, padding: '12px 14px', fontSize: 12, color: '#86efac', lineHeight: 1.6, overflowX: 'auto', margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                    {result.fixed_code}
                  </pre>
                </div>
              )}

              {result.review && (
                <div style={{ fontSize: 14, color: '#9ca3af', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{result.review}</div>
              )}

              {result.how_to_fix && (
                <div>
                  <div style={{ fontSize: 12, color: '#10b981' }}>How to Fix</div>
                  <div>{result.how_to_fix}</div>
                </div>
              )}

              {result.suggestions?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 12, color: '#f59e0b', fontWeight: 500, marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Suggestions</div>
                  {result.suggestions.map((s, i) => (
                    <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 8 }}>
                      <span style={{ color: '#f59e0b', flexShrink: 0 }}>→</span>
                      <span style={{ fontSize: 13, color: '#9ca3af' }}>{s}</span>
                    </div>
                  ))}
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
const actionBtns = {
  explain: { background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', borderRadius: 8, padding: '9px 18px', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
  fix:     { background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none', borderRadius: 8, padding: '9px 18px', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
  review:  { background: 'linear-gradient(135deg, #f59e0b, #d97706)', border: 'none', borderRadius: 8, padding: '9px 18px', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
};