import { useEffect, useState, useRef } from 'react';
import { chatAPI } from '../services/api';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [recording, setRec]     = useState(false);
  const [mode, setMode]         = useState('auto'); // auto | notes | general
  const messagesEnd             = useRef(null);
  const mediaRef                = useRef(null);
  const chunksRef               = useRef([]);

  useEffect(() => {
    chatAPI.getHistory().then(r => setMessages(r.data || [])).catch(() => {});
  }, []);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;
    const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setInput(''); setLoading(true);
    try {
      const r = await chatAPI.sendMessage({ message: text, mode });
      const botMsg = { role: 'assistant', content: r.data.answer || r.data.response || JSON.stringify(r.data), timestamp: new Date().toISOString(), sources: r.data.sources };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, something went wrong. Please try again.', timestamp: new Date().toISOString() }]);
    } finally { setLoading(false); }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRef.current = new MediaRecorder(stream);
      chunksRef.current = [];
      mediaRef.current.ondataavailable = e => chunksRef.current.push(e.data);
      mediaRef.current.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        try {
          const r = await chatAPI.transcribeVoice(blob);
          const text = r.data.text || r.data.transcript;
          if (text) sendMessage(text);
        } catch { alert('Voice transcription failed'); }
      };
      mediaRef.current.start();
      setRec(true);
    } catch { alert('Microphone access denied'); }
  };

  const stopRecording = () => {
    mediaRef.current?.stop();
    setRec(false);
  };

  const clearHistory = async () => {
    await chatAPI.clearHistory().catch(() => {});
    setMessages([]);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 56px)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <h1 style={h1}>AI Chatbot</h1>
          <p style={sub}>LangGraph agent · RAG from your notes · Voice input</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 12, color: '#4a5568' }}>Mode:</span>
          {['auto', 'notes', 'general'].map(m => (
            <button key={m} onClick={() => setMode(m)} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid', borderColor: mode === m ? '#6366f1' : '#1e2230', background: mode === m ? '#1e2745' : 'transparent', color: mode === m ? '#818cf8' : '#4a5568', fontSize: 12, cursor: 'pointer', textTransform: 'capitalize' }}>{m}</button>
          ))}
          <button onClick={clearHistory} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid #1e2230', background: 'transparent', color: '#6b7280', fontSize: 12, cursor: 'pointer', marginLeft: 8 }}>Clear</button>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', background: '#13161e', border: '1px solid #1e2230', borderRadius: 12, padding: '16px', marginBottom: 12 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px 20px' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🤖</div>
            <h3 style={{ color: '#6b7280', fontSize: 16, margin: '0 0 8px' }}>EduAI Assistant</h3>
            <p style={{ color: '#4a5568', fontSize: 14 }}>Ask me anything from your notes, get help with studies, or request career advice!</p>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 16, flexWrap: 'wrap' }}>
              {['Explain normalization in DBMS', 'Generate a study plan for OS', 'Review my resume for ML jobs', 'What hackathons are coming up?'].map(q => (
                <button key={q} onClick={() => sendMessage(q)} style={{ padding: '7px 14px', borderRadius: 20, border: '1px solid #1e2230', background: '#0d0f14', color: '#818cf8', fontSize: 12, cursor: 'pointer' }}>{q}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: 14 }}>
            {msg.role === 'assistant' && (
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, marginRight: 8, flexShrink: 0, alignSelf: 'flex-end' }}>🤖</div>
            )}
            <div style={{
              maxWidth: '70%', padding: '10px 14px', borderRadius: msg.role === 'user' ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
              background: msg.role === 'user' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : '#0d0f14',
              border: msg.role === 'assistant' ? '1px solid #1e2230' : 'none',
            }}>
              <div style={{ fontSize: 14, color: '#e2e8f0', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{msg.content}</div>
              {msg.sources?.length > 0 && (
                <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 11, color: '#4a5568' }}>Sources:</span>
                  {msg.sources.map((s, j) => <span key={j} style={{ fontSize: 11, background: '#1e2230', color: '#818cf8', padding: '2px 8px', borderRadius: 4 }}>{s}</span>)}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 14 }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, marginRight: 8 }}>🤖</div>
            <div style={{ padding: '10px 14px', background: '#0d0f14', border: '1px solid #1e2230', borderRadius: '12px 12px 12px 4px' }}>
              <div style={{ display: 'flex', gap: 4 }}>
                {[0, 1, 2].map(i => <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: '#818cf8', animation: `pulse 1s ${i * 0.2}s infinite` }} />)}
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEnd} />
      </div>

      {/* Input */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
        <textarea
          rows={1}
          placeholder="Ask anything... (Enter to send, Shift+Enter for newline)"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }}
          style={{ flex: 1, background: '#13161e', border: '1px solid #1e2230', borderRadius: 10, padding: '10px 14px', color: '#e2e8f0', fontSize: 14, outline: 'none', resize: 'none', lineHeight: 1.5, fontFamily: 'inherit' }}
        />
        <button onClick={recording ? stopRecording : startRecording} style={{
          width: 42, height: 42, borderRadius: 10, border: 'none', cursor: 'pointer', fontSize: 18,
          background: recording ? '#ef4444' : '#1e2230', flexShrink: 0,
          animation: recording ? 'pulse 1s infinite' : 'none',
        }} title="Voice input">🎤</button>
        <button onClick={() => sendMessage(input)} disabled={loading || !input.trim()} style={{ height: 42, padding: '0 18px', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', borderRadius: 10, color: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 600, flexShrink: 0 }}>
          Send →
        </button>
      </div>

      <style>{`@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.8)} }`}</style>
    </div>
  );
}

const h1 = { fontSize: 24, fontWeight: 700, color: '#e2e8f0', margin: 0, letterSpacing: '-0.5px' };
const sub = { color: '#4a5568', fontSize: 13, margin: '4px 0 0' };