import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'
import * as api from './api'

const navItems = [
  ['command', '◈', 'Command'],
  ['sites', '▦', 'Live Sites'],
  ['agents', '✦', 'Agents'],
  ['activity', '◷', 'Activity'],
  ['system', '◉', 'System'],
]

function StatusDot({ ok }) {
  return <i className={ok ? 'status-dot live' : 'status-dot'} />
}

function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await api.login(email, password)
      onLogin()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-shell">
      <div className="login-card">
        <div className="genie-mark">🧞</div>
        <p className="eyebrow">GENIE COMMAND CENTER</p>
        <h1>Back to the lamp.</h1>
        <p className="subtitle">Your private command center for the systems you built together.</p>
        <form className="login-form" onSubmit={submit}>
          <input aria-label="Email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Admin email" autoComplete="username" />
          <input aria-label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" autoComplete="current-password" />
          {error && <div className="error-box">{error}</div>}
          <button className="primary" disabled={busy}>{busy ? 'Opening Genie…' : 'Enter Command Center'}</button>
        </form>
      </div>
    </main>
  )
}

function LiveDesktop({ events }) {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const [active, setActive] = useState(false)
  const [error, setError] = useState('')
  const latestEvents = events.slice(-12).reverse()

  useEffect(() => () => streamRef.current?.getTracks().forEach((t) => t.stop()), [])

  async function start() {
    setError('')
    try {
      if (!navigator.mediaDevices?.getDisplayMedia) throw new Error('Live desktop capture is not available in this browser.')
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: { frameRate: { ideal: 30, max: 60 } }, audio: false })
      streamRef.current = stream
      videoRef.current.srcObject = stream
      await videoRef.current.play()
      setActive(true)
      stream.getVideoTracks()[0].addEventListener('ended', () => {
        setActive(false)
        streamRef.current = null
      })
    } catch (err) {
      setError(err.message)
    }
  }

  function stop() {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    setActive(false)
  }

  return (
    <section className="live-stage">
      <div className="stage-head">
        <div>
          <p className="eyebrow">GENIE LIVE</p>
          <h2>Watch Genie work.</h2>
          <p className="stage-copy">Keep the desktop, clicks, and local command center in the same window.</p>
        </div>
        <div className="stage-actions">
          {!active
            ? <button className="primary" onClick={start}>Start Live View</button>
            : <button className="ghost" onClick={stop}>Stop Live View</button>}
        </div>
      </div>
      <div className="screen-frame">
        {active
          ? <video ref={videoRef} muted playsInline />
          : <div className="screen-placeholder"><div className="orb">🧞</div><strong>Desktop feed is ready.</strong><span>Click Start Live View and choose the screen or window Genie is operating.</span></div>}
        <div className="feed-badge"><StatusDot ok={active} />{active ? 'LIVE DESKTOP' : 'STANDBY'}</div>
      </div>
      {error && <div className="error-box">{error}</div>}
      <div className="live-timeline">
        <div className="section-title"><span>Click & action trail</span><span>{events.length} events</span></div>
        {latestEvents.length
          ? latestEvents.map((event, i) => <div className="timeline-row" key={event.id || i}><span className="timeline-time">{new Date(event.at).toLocaleTimeString()}</span><strong>{event.action || 'Action'}</strong><span>{event.target || event.detail || 'Genie activity'}</span></div>)
          : <div className="timeline-empty">Agent click telemetry will appear here when a connected tool reports activity.</div>}
      </div>
    </section>
  )
}

function SiteViewer({ site }) {
  const [loaded, setLoaded] = useState(false)
  useEffect(() => setLoaded(false), [site?.url])

  if (!site) {
    return <div className="empty-viewer"><strong>Select a live site</strong><span>Choose a running local service from the left.</span></div>
  }

  return (
    <section className="site-view">
      <div className="site-view-head">
        <div>
          <p className="eyebrow">EMBEDDED WORKSPACE</p>
          <h2>{site.label}</h2>
          <span className="site-url">{site.url}</span>
        </div>
        <div className="site-view-actions">
          <a className="ghost" href={site.url} target="_blank" rel="noreferrer">Pop out</a>
          <span className="live-chip"><StatusDot ok={site.up} />{site.up ? 'LIVE' : 'OFFLINE'}</span>
        </div>
      </div>
      <div className="iframe-shell">
        {site.up && site.http
          ? <>
              {!loaded && <div className="iframe-loading">Connecting to {site.label}…</div>}
              <iframe title={site.label} src={site.url} onLoad={() => setLoaded(true)} />
            </>
          : <div className="screen-placeholder"><div className="mini-orb">◈</div><strong>{site.http ? 'Site is starting.' : 'No web UI detected.'}</strong><span>{site.error || 'Genie can still keep the service visible in status while it comes online.'}</span></div>}
      </div>
    </section>
  )
}

function SiteRail({ sites, selected, onSelect, onRefresh }) {
  const groups = useMemo(() => sites.reduce((acc, site) => {
    const key = site.group || 'Local'
    acc[key] = [...(acc[key] || []), site]
    return acc
  }, {}), [sites])

  return (
    <aside className="site-rail">
      <div className="rail-top">
        <div>
          <p className="eyebrow">YOUR WORKSPACE</p>
          <h3>Local Sites</h3>
        </div>
        <button className="icon-button" onClick={onRefresh} title="Refresh local sites" aria-label="Refresh local sites">↻</button>
      </div>
      {Object.entries(groups).map(([group, items]) => (
        <div className="rail-group" key={group}>
          <span className="rail-label">{group}</span>
          {items.map((site) => (
            <button key={site.id} className={selected?.id === site.id ? 'site-card active' : 'site-card'} onClick={() => onSelect(site)}>
              <span className="site-card-icon">{site.icon || '◈'}</span>
              <span className="site-card-copy"><strong>{site.label}</strong><small>{site.port ? 'localhost:' + site.port : site.url}</small></span>
              <StatusDot ok={site.up} />
            </button>
          ))}
        </div>
      ))}
      {!sites.length && <div className="timeline-empty">No configured local sites are online yet.</div>}
    </aside>
  )
}

function App() {
  const [loggedIn, setLoggedIn] = useState(api.isLoggedIn())
  const [tab, setTab] = useState('command')
  const [sites, setSites] = useState([])
  const [selectedSite, setSelectedSite] = useState(null)
  const [events, setEvents] = useState([])
  const [refreshing, setRefreshing] = useState(false)

  async function refreshSites() {
    if (!api.isLoggedIn()) return
    setRefreshing(true)
    try {
      const data = await api.listSites()
      setSites(data.sites || [])
      if (selectedSite) {
        const refreshed = (data.sites || []).find((s) => s.id === selectedSite.id)
        if (refreshed) setSelectedSite(refreshed)
      }
      if (!selectedSite && data.sites?.length) setSelectedSite(data.sites.find((s) => s.up && s.http) || data.sites[0])
    } catch {
      setSites([])
    } finally {
      setRefreshing(false)
    }
  }

  async function refreshEvents() {
    if (!api.isLoggedIn()) return
    try {
      const data = await api.listLiveEvents()
      setEvents(data.events || [])
    } catch {
      // Keep the last known event trail.
    }
  }

  useEffect(() => {
    if (!loggedIn) return
    refreshSites()
    refreshEvents()
    const sitesTimer = setInterval(refreshSites, 5000)
    const eventsTimer = setInterval(refreshEvents, 1500)
    return () => {
      clearInterval(sitesTimer)
      clearInterval(eventsTimer)
    }
  }, [loggedIn])

  if (!loggedIn) return <Login onLogin={() => setLoggedIn(true)} />

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">🧞</div>
          <div><h1>GENIE</h1><p>Personal command center</p></div>
        </div>
        <div className="nav">
          {navItems.map(([id, icon, label]) => (
            <button key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}>
              <span>{icon}</span><strong>{label}</strong>
            </button>
          ))}
        </div>
        <div className="runtime-card">
          <span>Runtime</span>
          <strong><StatusDot ok /> Alive</strong>
          <p>One window. One command center. Your systems stay together.</p>
        </div>
        <button className="ghost logout" onClick={() => { api.logout(); setLoggedIn(false) }}>Lock Genie</button>
      </aside>

      <section className="main">
        {tab === 'command' && (
          <>
            <header className="header">
              <div><p className="eyebrow">THE MAGIC IS THE SYSTEM</p><h2>Welcome back, Boss.</h2><p className="subtitle">Everything you built is getting a place here.</p></div>
              <div className="status"><StatusDot ok />GENIE ONLINE</div>
            </header>
            <LiveDesktop events={events} />
          </>
        )}

        {tab === 'sites' && (
          <div className="sites-layout">
            <SiteRail sites={sites} selected={selectedSite} onSelect={setSelectedSite} onRefresh={refreshSites} />
            <SiteViewer site={selectedSite} />
          </div>
        )}

        {tab === 'agents' && (
          <section className="panel feature-panel">
            <p className="eyebrow">AGENT OPS</p><h2>Bring every worker into Genie.</h2>
            <p>DAI, Agent-S, OpenCode, OpenClaw, Omni, and the rest of the local stack can become named control surfaces instead of separate destinations.</p>
            <div className="cards"><div><span>Control</span><strong>Run</strong></div><div><span>Health</span><strong>Audit</strong></div><div><span>Recovery</span><strong>Repair</strong></div><div><span>Visibility</span><strong>Show</strong></div></div>
          </section>
        )}

        {tab === 'activity' && (
          <section className="panel feature-panel">
            <p className="eyebrow">LIVE ACTIVITY</p><h2>See what Genie is doing.</h2>
            <div className="live-timeline full"><div className="section-title"><span>Recent activity</span><span>{events.length}</span></div>{events.slice().reverse().map((event, i) => <div className="timeline-row" key={event.id || i}><span className="timeline-time">{new Date(event.at).toLocaleTimeString()}</span><strong>{event.action || 'Action'}</strong><span>{event.target || event.detail || 'Genie activity'}</span></div>)}</div>
          </section>
        )}

        {tab === 'system' && (
          <section className="panel feature-panel">
            <p className="eyebrow">SYSTEM</p><h2>Everything has a home.</h2>
            <div className="system-grid">
              <div><span>Live sites</span><strong>{sites.filter((s) => s.up).length}</strong></div>
              <div><span>HTTP workspaces</span><strong>{sites.filter((s) => s.up && s.http).length}</strong></div>
              <div><span>Events</span><strong>{events.length}</strong></div>
              <div><span>Refresh</span><strong>{refreshing ? 'Working…' : '5 sec'}</strong></div>
            </div>
          </section>
        )}
      </section>
    </main>
  )
}

export default App
