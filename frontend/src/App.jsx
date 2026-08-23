import { useState, useEffect } from 'react'
import { startTrip, approveTrip, checkHealth } from './api/travel'
import './App.css'

function App() {
  // Top-level Application State
  const [threadId, setThreadId] = useState(null)
  const [status, setStatus] = useState('idle') // idle, loading, awaiting_approval, completed, blocked
  const [messages, setMessages] = useState([])
  const [itinerary, setItinerary] = useState("")
  const [agentsRun, setAgentsRun] = useState([])
  const [feedback, setFeedback] = useState("")
  
  // Health connection state
  const [health, setHealth] = useState({
    supabase_checkpointing: false,
    aviation_mcp: false,
    tavily_mcp: false,
    weather_mcp: false,
    langsmith_observability: false
  })

  // Chat input state
  const [userQuery, setUserQuery] = useState("")

  // Fetch health integrations on load
  useEffect(() => {
    checkHealth()
      .then(res => {
        if (res && res.integrations) {
          setHealth(res.integrations)
        }
      })
      .catch(err => {
        console.error("Health check error:", err)
        appendLog('error', `Connection Alert: FastAPI backend server is offline or unreachable.`)
      })
  }, [])

  // Helper to add lines to logs console panel
  const appendLog = (type, text) => {
    setMessages(prev => [...prev, { type, text, time: new Date().toLocaleTimeString() }])
  }

  // Handle trip planning submission
  const handleSubmit = (e, overrideQuery = null) => {
    if (e) e.preventDefault()
    const queryToUse = overrideQuery || userQuery
    if (!queryToUse || !queryToUse.trim()) {
      return
    }

    const messageToSend = queryToUse.trim()
    setUserQuery("")
    setStatus('loading')
    setItinerary("")
    setFeedback("")
    
    // Log initiation sequence
    setMessages([
      { type: 'system', text: `Initiated session with query: "${messageToSend}"`, time: new Date().toLocaleTimeString() },
      { type: 'system', text: '🔍 Guardrail checking query parameters...', time: new Date().toLocaleTimeString() }
    ])
    
    startTrip(messageToSend, threadId)
      .then(res => {
        setThreadId(res.thread_id)
        setAgentsRun(res.agents_run || [])

        if (res.status === 'blocked') {
          setStatus('blocked')
          appendLog('error', `🚫 Guardrail Blocked: ${res.content}`)
        } else if (res.status === 'awaiting_approval') {
          setStatus('awaiting_approval')
          setItinerary(res.content)
          appendLog('agent', '🤖 Supervisor: Routed query to specialists successfully.')
          appendLog('agent', `💼 Running specialist processes: ${res.agents_run.filter(a => a !== 'supervisor_agent' && a !== 'itinerary_agent').join(', ')}`)
          appendLog('agent', '📝 Itinerary Agent: Day-by-day plan draft compiled.')
          appendLog('alert', '⚠️ Checkpoint Interrupted: Draft paused awaiting human review.')
        } else if (res.status === 'completed') {
          setStatus('completed')
          setItinerary(res.content)
          appendLog('system', '✅ Journey planning complete! Enjoy your trip.')
        }
      })
      .catch(err => {
        setStatus('idle')
        appendLog('error', `Error executing agent pipeline: ${err.message}`)
      })
  }

  // Handle HITL human response approval / revision
  const handleApproval = (approved) => {
    if (!threadId) return

    setStatus('loading')
    const actionText = approved ? 'Confirming approval...' : 'Submitting change request...'
    appendLog('system', `HITL Checkpoint: ${actionText}`)

    approveTrip(threadId, approved, approved ? "" : feedback)
      .then(res => {
        setAgentsRun(res.agents_run || [])
        
        if (res.status === 'awaiting_approval') {
          setStatus('awaiting_approval')
          setItinerary(res.content)
          appendLog('alert', '⚠️ Checkpoint Interrupted: Revised draft paused awaiting review.')
        } else if (res.status === 'completed') {
          setStatus('completed')
          setItinerary(res.content)
          appendLog('system', '✅ Itinerary finalized successfully!')
        } else {
          setStatus(res.status)
          setItinerary(res.content)
        }
      })
      .catch(err => {
        setStatus('awaiting_approval')
        appendLog('error', `Failed to submit review: ${err.message}`)
      })
  }

  const handleReset = () => {
    setThreadId(null)
    setStatus('idle')
    setMessages([])
    setItinerary("")
    setAgentsRun([])
    setFeedback("")
  }

  // Simple, robust Markdown Formatter
  const formatMarkdown = (mdText) => {
    if (!mdText) return null
    return mdText.split('\n').map((line, i) => {
      if (line.startsWith('# ')) {
        return <h1 key={i} className="md-h1">{line.substring(2)}</h1>
      }
      if (line.startsWith('## ')) {
        return <h2 key={i} className="md-h2">{line.substring(3)}</h2>
      }
      if (line.startsWith('### ')) {
        return <h3 key={i} className="md-h3">{line.substring(4)}</h3>
      }
      if (line.startsWith('- ') || line.startsWith('* ')) {
        return <li key={i} className="md-li">{line.substring(2)}</li>
      }
      return <p key={i} className="md-p">{line}</p>
    })
  }

  return (
    <div className="app-container">
      {/* Header Panel */}
      <header className="header">
        <div className="logo-section">
          <span className="logo-icon">✈️</span>
          <span className="logo-text gradient-text">TourAlly</span>
        </div>
        
        <div className="health-indicators">
          {threadId && (
            <button 
              onClick={handleReset} 
              className="reset-btn"
              style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#fca5a5',
                padding: '6px 12px',
                borderRadius: '9999px',
                fontSize: '12px',
                cursor: 'pointer',
                marginRight: '12px',
                fontFamily: 'var(--font-sans)',
                fontWeight: '600',
                transition: 'all 0.2s ease'
              }}
            >
              Reset Session
            </button>
          )}
          
          <div className="health-badge">
            <span className={`health-dot ${health.supabase_checkpointing ? 'active' : 'inactive'}`} />
            Supabase DB
          </div>
          <div className="health-badge">
            <span className={`health-dot ${health.aviation_mcp ? 'active' : 'inactive'}`} />
            Aviation API
          </div>
          <div className="health-badge">
            <span className={`health-dot ${health.weather_mcp ? 'active' : 'inactive'}`} />
            Weather MCP
          </div>
          <div className="health-badge">
            <span className={`health-dot ${health.tavily_mcp ? 'active' : 'inactive'}`} />
            Tavily Web
          </div>
        </div>
      </header>

      {/* Main Workspace Split Grid */}
      <main className="workspace-grid">
        
        {/* Left Column: Form & Logs */}
        <div className="left-column">
          
          {/* Conversational Travel Prompt Input */}
          <section className="glass-panel trip-form-panel">
            <h2 className="panel-title">💬 Plan Your Journey</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-field" style={{ marginBottom: '16px' }}>
                <label className="form-label" style={{ marginBottom: '8px' }}>Ask anything or describe your trip</label>
                <textarea 
                  className="form-input" 
                  style={{ minHeight: '110px', resize: 'vertical' }}
                  value={userQuery}
                  onChange={e => setUserQuery(e.target.value)}
                  placeholder="e.g. Plan a 3-day trip to Paris from London with a $1500 budget"
                  disabled={status === 'loading'}
                />
              </div>

              <div className="suggestion-chips" style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
                <button 
                  type="button" 
                  onClick={() => handleSubmit(null, "Plan a 3-day trip to Paris from London with $1500 budget")}
                  disabled={status === 'loading'}
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-secondary)',
                    padding: '6px 12px',
                    borderRadius: '8px',
                    fontSize: '11.5px',
                    cursor: 'pointer'
                  }}
                >
                  🗼 3-Day Paris from London ($1500)
                </button>
                <button 
                  type="button" 
                  onClick={() => handleSubmit(null, "What is the weather in Tokyo?")}
                  disabled={status === 'loading'}
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-secondary)',
                    padding: '6px 12px',
                    borderRadius: '8px',
                    fontSize: '11.5px',
                    cursor: 'pointer'
                  }}
                >
                  🌤️ Weather in Tokyo
                </button>
                <button 
                  type="button" 
                  onClick={() => handleSubmit(null, "Tell me a programming joke")}
                  disabled={status === 'loading'}
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-secondary)',
                    padding: '6px 12px',
                    borderRadius: '8px',
                    fontSize: '11.5px',
                    cursor: 'pointer'
                  }}
                >
                  🤡 Programming Joke (Guardrail Test)
                </button>
                <button 
                  type="button" 
                  onClick={() => handleSubmit(null, "Search flights from Heathrow to Charles De Gaulle")}
                  disabled={status === 'loading'}
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-secondary)',
                    padding: '6px 12px',
                    borderRadius: '8px',
                    fontSize: '11.5px',
                    cursor: 'pointer'
                  }}
                >
                  ✈️ Flights LHR ➔ CDG
                </button>
              </div>

              <button 
                type="submit" 
                className="submit-btn"
                disabled={status === 'loading'}
              >
                {status === 'loading' ? 'Orchestrating Agent Network...' : 'Analyze Travel Prompt'}
              </button>
            </form>
          </section>

          {/* Console / Agent Logs Stream */}
          <section className="glass-panel console-panel">
            <h2 className="panel-title">📟 Agent Pipeline Logs</h2>
            <div className="log-stream">
              {messages.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 'auto', textAlign: 'center' }}>
                  No active logs. Enter parameters to view agent tasks.
                </p>
              ) : (
                messages.map((m, i) => (
                  <div key={i} className={`log-item ${m.type}`}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>
                      [{m.time}]
                    </span>
                    {m.text}
                  </div>
                ))
              )}
            </div>
          </section>

        </div>

        {/* Right Column: Itinerary Output & HITL */}
        <div className="right-column">
          
          {/* Agent Step Progress Bar */}
          <section className="glass-panel steps-panel">
            <div className="steps-list">
              <div className={`step-item ${status !== 'idle' ? 'completed' : ''}`}>
                <div className="step-dot">🛡️</div>
                <span className="step-label">Guardrail</span>
              </div>
              <div className={`step-item ${agentsRun.includes('supervisor_agent') ? 'completed' : ''}`}>
                <div className="step-dot">👁️</div>
                <span className="step-label">Supervisor</span>
              </div>
              <div className={`step-item ${agentsRun.length > 2 ? 'completed' : ''}`}>
                <div className="step-dot">🤖</div>
                <span className="step-label">Specialists</span>
              </div>
              <div className={`step-item ${status === 'awaiting_approval' ? 'active' : status === 'completed' ? 'completed' : ''}`}>
                <div className="step-dot">✍️</div>
                <span className="step-label">Human Review</span>
              </div>
              <div className={`step-item ${status === 'completed' ? 'completed' : ''}`}>
                <div className="step-dot">🎉</div>
                <span className="step-label">Final Plan</span>
              </div>
            </div>
          </section>

          {/* Human Review Panel */}
          {status === 'awaiting_approval' && (
            <section className="glass-panel hitl-panel">
              <h2 className="panel-title" style={{ color: '#eab308' }}>⚠️ Human-in-the-Loop Review Needed</h2>
              <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                Please review the draft travel plan below. You can approve it to finalize the itinerary, or request adjustments (e.g. changing hotels or adding flights).
              </p>
              <textarea
                className="form-input"
                style={{ minHeight: '80px', resize: 'vertical', marginBottom: '12px' }}
                value={feedback}
                onChange={e => setFeedback(e.target.value)}
                placeholder="Request revisions, e.g. 'Select hotel near Saint-Germain-des-Prés or suggest flight BA308'"
              />
              <div className="hitl-actions">
                <button className="btn-approve" onClick={() => handleApproval(true)}>
                  Approve & Finalize
                </button>
                <button className="btn-reject" onClick={() => handleApproval(false)}>
                  Request Revision
                </button>
              </div>
            </section>
          )}

          {/* synthesized Itinerary Content Card */}
          <section className="glass-panel itinerary-panel">
            {status === 'loading' ? (
              <div className="empty-itinerary-state">
                <div className="pulse-spinner" />
                <h3>Assembling Live Itinerary Context</h3>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px' }}>
                  AviationStack scheduled flights, Tavily listings, and weather forecasts are being gathered...
                </p>
              </div>
            ) : itinerary ? (
              <div className="itinerary-content">
                {formatMarkdown(itinerary)}
              </div>
            ) : (
              <div className="empty-itinerary-state">
                <span className="empty-icon">🗺️</span>
                <h3>Custom Travel Planner</h3>
                <p style={{ fontSize: '14px', maxWidth: '360px', marginTop: '8px' }}>
                  Submit leaving and destination parameters. Real-time flights, weather conditions, and hotel lists will synthesize here.
                </p>
              </div>
            )}
          </section>

        </div>

      </main>
    </div>
  )
}

export default App
