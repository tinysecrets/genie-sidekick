import React, { useEffect, useRef, useState } from 'react'
import * as api from './api'

export default function App() {
  const [authed, setAuthed] = useState(api.isLoggedIn())

  if (!authed) return <Login onSuccess={() => setAuthed(true)} />
  return <Chat onLogout={() => { api.logout(); setAuthed(false) }} />
}

function Login({ onSuccess }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setErr(''); setBusy(true)
    try {
      await api.login(email, password)
      onSuccess()
    } catch (e) {
      setErr(e.message || 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-shell" data-testid="login-shell">
      <form className="login-card" onSubmit={submit}>
        <div className="lamp">🪔</div>
        <h1>Genie</h1>
        <p className="sub">Your personal sidekick.</p>
        <input
          data-testid="login-email"
          type="email" placeholder="email" autoComplete="username"
          value={email} onChange={e => setEmail(e.target.value)} required
        />
        <input
          data-testid="login-password"
          type="password" placeholder="password" autoComplete="current-password"
          value={password} onChange={e => setPassword(e.target.value)} required
        />
        {err && <div className="err" data-testid="login-error">{err}</div>}
        <button data-testid="login-submit" disabled={busy} type="submit">
          {busy ? 'Rubbing the lamp…' : 'Enter'}
        </button>
      </form>
    </div>
  )
}

function Chat({ onLogout }) {
  const [providers, setProviders] = useState([])
  const [provider, setProvider] = useState('')
  const [sessions, setSessions] = useState([])
  const [sessionId, setSessionId] = useState('')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const scrollRef = useRef(null)

  // initial load
  useEffect(() => {
    (async () => {
      try {
        const p = await api.listProviders()
        setProviders(p.providers || [])
        setProvider(p.default || '')
        const s = await api.listSessions()
        setSessions(s)
        if (s.length) await openSession(s[0].session_id)
        else await startNew()
      } catch (e) {
        setErr(e.message)
        if (/auth|forbidden|401|403/i.test(e.message)) onLogout()
      }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [messages])

  async function openSession(id) {
    setSessionId(id); setMessages([]); setErr('')
    try {
      const h = await api.loadHistory(id)
      setMessages(h.messages || [])
    } catch (e) { setErr(e.message) }
  }

  async function startNew() {
    try {
      const r = await api.newSession()
      setSessionId(r.session_id); setMessages([])
    } catch (e) { setErr(e.message) }
  }

  async function send(e) {
    e?.preventDefault?.()
    const msg = input.trim()
    if (!msg || busy) return
    setInput(''); setBusy(true); setErr('')
    setMessages(m => [...m, { role: 'user', content: msg, at: new Date().toISOString() }])
    try {
      const r = await api.chat(msg, sessionId, provider)
      if (r.session_id && r.session_id !== sessionId) setSessionId(r.session_id)
      setMessages(m => [...m, { role: 'assistant', content: r.reply, at: new Date().toISOString(), provider: r.provider }])
      // refresh sidebar
      api.listSessions().then(setSessions).catch(() => {})
    } catch (e) {
      setErr(e.message)
      setMessages(m => [...m, { role: 'assistant', content: `⚠️ ${e.message}`, at: new Date().toISOString(), error: true }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="chat-shell" data-testid="chat-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="lamp">🪔</span>
          <span>Genie</span>
        </div>
        <button className="new-btn" data-testid="new-session-btn" onClick={startNew}>+ New chat</button>
        <div className="sessions">
          {sessions.map(s => (
            <button
              key={s.session_id}
              data-testid={`session-${s.session_id}`}
              className={`session ${s.session_id === sessionId ? 'active' : ''}`}
              onClick={() => openSession(s.session_id)}
              title={s.preview}
            >
              <div className="prev">{s.preview || 'New chat'}</div>
              <div className="meta">{s.message_count} msg</div>
            </button>
          ))}
          {!sessions.length && <div className="empty">No chats yet.</div>}
        </div>
        <div className="footer">
          <select
            data-testid="provider-select"
            value={provider}
            onChange={e => setProvider(e.target.value)}
            title="Switch brain"
          >
            {providers.map(p => (
              <option key={p.id} value={p.id} disabled={!p.enabled}>
                {p.emoji} {p.label}{p.enabled ? '' : ' (off)'}
              </option>
            ))}
          </select>
          <button className="logout" data-testid="logout-btn" onClick={onLogout}>Logout</button>
        </div>
      </aside>

      <main className="main">
        <div className="messages" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="welcome">
              <div className="lamp big">🪔</div>
              <p>Ask me anything, Boss.</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}${m.error ? ' err' : ''}`} data-testid={`msg-${m.role}-${i}`}>
              <div className="bubble">{m.content}</div>
            </div>
          ))}
          {busy && (
            <div className="msg assistant" data-testid="msg-typing">
              <div className="bubble typing"><span/><span/><span/></div>
            </div>
          )}
        </div>

        {err && <div className="banner-err" data-testid="chat-error">{err}</div>}

        <form className="composer" onSubmit={send}>
          <textarea
            data-testid="composer-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
            }}
            placeholder="Talk to Genie… (Enter to send, Shift+Enter for newline)"
            rows={1}
          />
          <button data-testid="send-btn" type="submit" disabled={busy || !input.trim()}>
            Send
          </button>
        </form>
      </main>
    </div>
  )
}
