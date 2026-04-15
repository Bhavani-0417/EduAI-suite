import { useEffect, useState } from 'react';
import { careerAPI } from '../services/api';

const STATUS_COLORS = { applied: '#818cf8', interview: '#f59e0b', rejected: '#ef4444', offer: '#10b981', shortlisted: '#06b6d4' };

export default function Career() {
  const [tab, setTab]         = useState('resume');
  const [jobs, setJobs]       = useState([]);
  const [analytics, setAna]   = useState(null);
  const [matchResult, setMatch] = useState(null);
  const [matchForm, setMF]    = useState({ resume_text: '', job_description: '' });
  const [matchLoading, setML] = useState(false);
  const [genLoading, setGL]   = useState(false);
  const [resumeForm, setRF]   = useState({ name: '', email: '', phone: '', college: '', branch: '', year: '', skills: '', experience: '', projects: '', education: '', career_objective: '' });
  const [jobForm, setJF]      = useState({ company: '', role: '', applied_date: '', status: 'applied', job_url: '', notes: '' });
  const [showJobForm, setSJF] = useState(false);

  const load = () => {
    careerAPI.getJobs().then(r => setJobs(r.data)).catch(() => {});
    careerAPI.getAnalytics().then(r => setAna(r.data)).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  const generateResume = async (e) => {
    e.preventDefault(); setGL(true);
    try {
      const r = await careerAPI.generateResume(resumeForm);
      const url = URL.createObjectURL(r.data);
      const a = document.createElement('a'); a.href = url; a.download = `${resumeForm.name}_Resume.pdf`; a.click();
    } catch (err) { alert(err.response?.data?.detail || 'Error generating resume'); }
    finally { setGL(false); }
  };

  const matchJD = async (e) => {
    e.preventDefault(); setML(true); setMatch(null);
    try {
      const r = await careerAPI.matchJD(matchForm);
      setMatch(r.data);
    } catch (err) { alert(err.response?.data?.detail || 'Error matching'); }
    finally { setML(false); }
  };

  const addJob = async (e) => {
    e.preventDefault();
    try { await careerAPI.addJob(jobForm); setSJF(false); setJF({ company: '', role: '', applied_date: '', status: 'applied', job_url: '', notes: '' }); load(); }
    catch (err) { alert(err.response?.data?.detail || 'Error adding job'); }
  };

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={h1}>Career Center</h1>
        <p style={sub}>ATS resume builder, job tracker, JD matching & interview prep</p>
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, background: '#13161e', border: '1px solid #1e2230', borderRadius: 10, padding: 4, width: 'fit-content' }}>
        {['resume', 'job tracker', 'jd matcher'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ padding: '7px 18px', borderRadius: 7, border: 'none', cursor: 'pointer', background: tab === t ? '#1e2745' : 'transparent', color: tab === t ? '#818cf8' : '#4a5568', fontSize: 13, fontWeight: tab === t ? 600 : 400, textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'resume' && (
        <div style={{ display: 'grid', gridTemplateColumns: '420px 1fr', gap: 20 }}>
          <div style={card}>
            <h3 style={cardTitle}>📄 ATS Resume Builder</h3>
            <form onSubmit={generateResume}>
              {[['Full Name', 'name', true], ['Email', 'email', true], ['Phone', 'phone', false],
                ['College', 'college', false], ['Branch / Degree', 'branch', false], ['Year', 'year', false]].map(([l, k, r]) => (
                <div key={k} style={{ marginBottom: 11 }}>
                  <label style={lbl}>{l}</label>
                  <input required={r} placeholder={l} value={resumeForm[k]} onChange={e => setRF({ ...resumeForm, [k]: e.target.value })} style={inputStyle} />
                </div>
              ))}
              {[['Skills (comma separated)', 'skills', 'Python, React, Machine Learning...', 3],
                ['Projects', 'projects', 'Project name: description...', 3],
                ['Experience', 'experience', 'Internships, part-time work...', 2],
                ['Education', 'education', 'Degrees, certifications...', 2],
                ['Career Objective', 'career_objective', 'Your career goal...', 2]].map(([l, k, ph, rows]) => (
                <div key={k} style={{ marginBottom: 11 }}>
                  <label style={lbl}>{l}</label>
                  <textarea rows={rows} placeholder={ph} value={resumeForm[k]} onChange={e => setRF({ ...resumeForm, [k]: e.target.value })} style={{ ...inputStyle, resize: 'vertical', lineHeight: 1.5 }} />
                </div>
              ))}
              <button type="submit" disabled={genLoading} style={{ ...pinkBtn, width: '100%', marginTop: 6 }}>
                {genLoading ? '⏳ Generating ATS Resume...' : '⬇ Generate & Download PDF Resume'}
              </button>
            </form>
          </div>
          <div style={card}>
            <h3 style={cardTitle}>ATS Optimization Tips</h3>
            {[['Include keywords', 'Match terms from job descriptions you target'],
              ['Quantify achievements', "Use numbers: 'improved accuracy by 23%'"],
              ['Clean formatting', 'No tables/columns — ATS scanners prefer simple layout'],
              ['Skills section', 'List technical and soft skills clearly'],
              ['Action verbs', "Start bullet points with: Built, Developed, Implemented..."],
            ].map(([t, d]) => (
              <div key={t} style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
                <div style={{ width: 20, height: 20, borderRadius: '50%', background: '#1e2745', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#818cf8', fontSize: 11, flexShrink: 0, marginTop: 1 }}>✓</div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: '#e2e8f0' }}>{t}</div>
                  <div style={{ fontSize: 12, color: '#4a5568' }}>{d}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'job tracker' && (
        <div>
          {analytics && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 24 }}>
              {[['Total Applied', analytics.total_applied, '#6366f1'],
                ['Interviews', analytics.interviews, '#f59e0b'],
                ['Offers', analytics.offers, '#10b981'],
                ['Match Score Avg', `${analytics.avg_match_score || 0}%`, '#ec4899']].map(([l, v, c]) => (
                <div key={l} style={{ background: '#13161e', border: '1px solid #1e2230', borderRadius: 10, padding: '14px 16px' }}>
                  <div style={{ fontSize: 11, color: '#4a5568', marginBottom: 4 }}>{l}</div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: c }}>{v ?? 0}</div>
                </div>
              ))}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <button onClick={() => setSJF(!showJobForm)} style={purpleBtn}>+ Add Application</button>
          </div>

          {showJobForm && (
            <div style={{ ...card, marginBottom: 20 }}>
              <h3 style={cardTitle}>Add Job Application</h3>
              <form onSubmit={addJob} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {[['Company', 'company', true], ['Role', 'role', true], ['Applied Date', 'applied_date', false, 'date'], ['Job URL', 'job_url', false]].map(([l, k, r, type = 'text']) => (
                  <div key={k}>
                    <label style={lbl}>{l}</label>
                    <input type={type} required={r} placeholder={l} value={jobForm[k]} onChange={e => setJF({ ...jobForm, [k]: e.target.value })} style={inputStyle} />
                  </div>
                ))}
                <div>
                  <label style={lbl}>Status</label>
                  <select value={jobForm.status} onChange={e => setJF({ ...jobForm, status: e.target.value })} style={{ ...inputStyle, appearance: 'none' }}>
                    {Object.keys(STATUS_COLORS).map(s => <option key={s} value={s} style={{ textTransform: 'capitalize' }}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label style={lbl}>Notes</label>
                  <input placeholder="Any notes..." value={jobForm.notes} onChange={e => setJF({ ...jobForm, notes: e.target.value })} style={inputStyle} />
                </div>
                <div style={{ gridColumn: '1 / -1', display: 'flex', gap: 10 }}>
                  <button type="submit" style={purpleBtn}>Save Application</button>
                  <button type="button" onClick={() => setSJF(false)} style={{ ...purpleBtn, background: '#1e2230' }}>Cancel</button>
                </div>
              </form>
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {jobs.length === 0 ? (
              <div style={card}><p style={{ color: '#4a5568', fontSize: 14 }}>No applications tracked yet. Add your first one!</p></div>
            ) : jobs.map(j => (
              <div key={j.id} style={{ ...card, display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: '#1e2230', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18 }}>🏢</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 15, fontWeight: 600, color: '#e2e8f0' }}>{j.role}</div>
                  <div style={{ fontSize: 13, color: '#6b7280' }}>{j.company} · {j.applied_date}</div>
                </div>
                <div style={{ background: STATUS_COLORS[j.status] + '22', color: STATUS_COLORS[j.status], padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600, textTransform: 'capitalize' }}>
                  {j.status}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'jd matcher' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <div style={card}>
            <h3 style={cardTitle}>🔍 Resume-JD Match Scorer</h3>
            <form onSubmit={matchJD}>
              <div style={{ marginBottom: 14 }}>
                <label style={lbl}>Your Resume Text</label>
                <textarea rows={8} required placeholder="Paste your resume text here..." value={matchForm.resume_text} onChange={e => setMF({ ...matchForm, resume_text: e.target.value })} style={{ ...inputStyle, resize: 'vertical' }} />
              </div>
              <div style={{ marginBottom: 16 }}>
                <label style={lbl}>Job Description</label>
                <textarea rows={8} required placeholder="Paste job description here..." value={matchForm.job_description} onChange={e => setMF({ ...matchForm, job_description: e.target.value })} style={{ ...inputStyle, resize: 'vertical' }} />
              </div>
              <button type="submit" disabled={matchLoading} style={{ ...pinkBtn, width: '100%' }}>
                {matchLoading ? '⏳ Analyzing...' : '🔍 Calculate Match Score'}
              </button>
            </form>
          </div>
          <div style={card}>
            <h3 style={cardTitle}>Match Results</h3>
            {matchLoading && <p style={{ color: '#818cf8', fontSize: 14 }}>Calculating TF-IDF cosine similarity...</p>}
            {matchResult && (
              <div>
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                  <div style={{ fontSize: 60, fontWeight: 700, color: matchResult.match_score >= 70 ? '#10b981' : matchResult.match_score >= 50 ? '#f59e0b' : '#ef4444' }}>
                    {matchResult.match_score}%
                  </div>
                  <div style={{ fontSize: 14, color: '#6b7280' }}>Match Score</div>
                  <div style={{ height: 8, background: '#1e2230', borderRadius: 4, marginTop: 12 }}>
                    <div style={{ height: '100%', width: `${matchResult.match_score}%`, background: matchResult.match_score >= 70 ? '#10b981' : matchResult.match_score >= 50 ? '#f59e0b' : '#ef4444', borderRadius: 4 }} />
                  </div>
                </div>
                {matchResult.matched_keywords?.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 13, color: '#10b981', fontWeight: 500, marginBottom: 8 }}>✓ Matched Keywords</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {matchResult.matched_keywords.map(k => (
                        <span key={k} style={{ background: '#0c1a0e', border: '1px solid #14532d', color: '#86efac', padding: '3px 10px', borderRadius: 20, fontSize: 12 }}>{k}</span>
                      ))}
                    </div>
                  </div>
                )}
                {matchResult.missing_keywords?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 13, color: '#ef4444', fontWeight: 500, marginBottom: 8 }}>✗ Missing Keywords</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {matchResult.missing_keywords.map(k => (
                        <span key={k} style={{ background: '#1a0c0c', border: '1px solid #7f1d1d', color: '#fca5a5', padding: '3px 10px', borderRadius: 20, fontSize: 12 }}>{k}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            {!matchLoading && !matchResult && <p style={{ color: '#4a5568', fontSize: 14 }}>Match score and keyword analysis will appear here.</p>}
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
const pinkBtn = { background: 'linear-gradient(135deg, #ec4899, #be185d)', border: 'none', borderRadius: 8, padding: '9px 18px', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' };