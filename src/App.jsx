import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  Bug,
  CheckCircle2,
  Clock,
  Database,
  RefreshCw,
  Send,
  Sparkles,
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const emptyForm = {
  title: '',
  description: '',
  stack_trace: '',
  severity: 'medium',
  environment: '',
}

const sampleBug = {
  title: 'Checkout fails after payment token refresh',
  description:
    'Several customers report that checkout loops back to the payment step immediately after confirming a saved card.',
  stack_trace:
    'PaymentTokenExpired: token refresh completed after checkout session lock\n  at CheckoutService.authorize\n  at PaymentGatewayClient.charge',
  severity: 'high',
  environment: 'production-us-east',
}

function StatusPill({ ok, label }) {
  return (
    <span className={`status-pill ${ok ? 'status-ok' : 'status-warn'}`}>
      {ok ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}
      {label}
    </span>
  )
}

function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  )
}

function confidenceLabel(value) {
  if (value >= 0.8) return 'High'
  if (value >= 0.55) return 'Medium'
  return 'Low'
}

export default function App() {
  const [health, setHealth] = useState(null)
  const [bugs, setBugs] = useState([])
  const [detail, setDetail] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const selectedBugId = detail?.bug?.id
  const confidence = detail?.analysis?.confidence ?? 0

  const sortedMatches = useMemo(() => detail?.matches || [], [detail])

  async function request(path, options) {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(body.detail || `Request failed with ${response.status}`)
    }
    return response.json()
  }

  async function loadHealth() {
    try {
      setHealth(await request('/health'))
    } catch {
      setHealth({ app: 'bugtrace', database: false, mock_fallback_enabled: true })
    }
  }

  async function loadBugs() {
    try {
      setBugs(await request('/bugs?limit=20'))
    } catch (err) {
      setError(err.message)
    }
  }

  async function loadBug(id) {
    setError('')
    try {
      setDetail(await request(`/bugs/${id}`))
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    loadHealth()
    loadBugs()
  }, [])

  async function submitBug(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const payload = {
        ...form,
        stack_trace: form.stack_trace || null,
        environment: form.environment || null,
      }
      const result = await request('/bugs', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setDetail(result)
      setForm(emptyForm)
      await loadBugs()
      await loadHealth()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function updateForm(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand-row">
            <Bug size={26} />
            <h1>bugtrace</h1>
          </div>
          <p>AI-assisted issue triage for customer reports and CI failure history.</p>
        </div>
        <div className="status-cluster">
          <StatusPill ok={Boolean(health?.database)} label="Postgres" />
          <StatusPill
            ok={Boolean(health?.mock_fallback_enabled)}
            label={health?.mock_fallback_enabled ? 'Fallback ready' : 'Gemini only'}
          />
          <button className="icon-button" type="button" onClick={() => { loadHealth(); loadBugs() }}>
            <RefreshCw size={17} />
          </button>
        </div>
      </header>

      {error && (
        <section className="notice">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </section>
      )}

      <section className="workspace">
        <aside className="submit-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Submission</span>
              <h2>New customer bug</h2>
            </div>
            <button className="ghost-button" type="button" onClick={() => setForm(sampleBug)}>
              <Sparkles size={16} />
              Sample
            </button>
          </div>

          <form onSubmit={submitBug} className="form-stack">
            <Field label="Title">
              <input
                value={form.title}
                onChange={(event) => updateForm('title', event.target.value)}
                placeholder="Short failure summary"
                required
                minLength={4}
              />
            </Field>
            <Field label="Description">
              <textarea
                value={form.description}
                onChange={(event) => updateForm('description', event.target.value)}
                placeholder="Customer impact, reproduction notes, or symptoms"
                required
                minLength={10}
                rows={5}
              />
            </Field>
            <Field label="Stack trace or logs">
              <textarea
                value={form.stack_trace}
                onChange={(event) => updateForm('stack_trace', event.target.value)}
                placeholder="Paste raw logs, exception text, or trace snippets"
                rows={7}
                className="mono-input"
              />
            </Field>
            <div className="two-col">
              <Field label="Severity">
                <select value={form.severity} onChange={(event) => updateForm('severity', event.target.value)}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </Field>
              <Field label="Environment">
                <input
                  value={form.environment}
                  onChange={(event) => updateForm('environment', event.target.value)}
                  placeholder="production-us-east"
                />
              </Field>
            </div>
            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? <RefreshCw className="spin" size={17} /> : <Send size={17} />}
              {loading ? 'Analyzing' : 'Submit and analyze'}
            </button>
          </form>
        </aside>

        <section className="triage-panel">
          {!detail ? (
            <div className="empty-state">
              <Activity size={38} />
              <h2>No active analysis</h2>
              <p>Submit a bug or select a recent item to inspect AI triage output and matched test failures.</p>
            </div>
          ) : (
            <>
              <div className="detail-header">
                <div>
                  <span className="eyebrow">Analysis #{detail.bug.id}</span>
                  <h2>{detail.bug.title}</h2>
                  <p>{detail.bug.description}</p>
                </div>
                <div className="score-card">
                  <span>{confidenceLabel(confidence)}</span>
                  <strong>{Math.round(confidence * 100)}%</strong>
                </div>
              </div>

              <div className="metrics-grid">
                <div><span>Severity</span><strong>{detail.bug.severity}</strong></div>
                <div><span>Category</span><strong>{detail.analysis?.category || 'unknown'}</strong></div>
                <div><span>Status</span><strong>{detail.analysis?.status || detail.bug.status}</strong></div>
                <div><span>Mode</span><strong>{detail.analysis?.used_fallback ? 'Fallback' : 'Gemini'}</strong></div>
              </div>

              <div className="analysis-grid">
                <article>
                  <h3>Root cause</h3>
                  <p>{detail.analysis?.root_cause}</p>
                </article>
                <article>
                  <h3>Suggested fix</h3>
                  <p>{detail.analysis?.suggested_fix}</p>
                </article>
              </div>

              <section className="matches">
                <div className="panel-heading tight">
                  <div>
                    <span className="eyebrow">Retrieval</span>
                    <h3>Matched historical failures</h3>
                  </div>
                  <span className="count-badge">{sortedMatches.length}</span>
                </div>
                <div className="match-list">
                  {sortedMatches.map((match) => (
                    <article className="match-card" key={match.failure.id}>
                      <div className="match-title">
                        <strong>{match.failure.test_name}</strong>
                        <span>{Math.round(match.score * 100)}%</span>
                      </div>
                      <p>{match.failure.failure_signature}</p>
                      <code>{match.failure.stack_trace}</code>
                    </article>
                  ))}
                </div>
              </section>
            </>
          )}
        </section>

        <aside className="recent-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">History</span>
              <h2>Recent bugs</h2>
            </div>
            <Database size={18} />
          </div>
          <div className="recent-list">
            {bugs.length === 0 && <p className="muted">No submissions yet.</p>}
            {bugs.map((bug) => (
              <button
                type="button"
                className={`recent-item ${selectedBugId === bug.id ? 'selected' : ''}`}
                key={bug.id}
                onClick={() => loadBug(bug.id)}
              >
                <span>{bug.title}</span>
                <small>
                  <Clock size={13} />
                  {new Date(bug.created_at).toLocaleString()}
                </small>
              </button>
            ))}
          </div>
        </aside>
      </section>
    </main>
  )
}
