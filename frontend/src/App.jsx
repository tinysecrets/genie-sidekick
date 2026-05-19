import React, { useState } from 'react'

const workers = [
  { name: 'Repo Builder', status: 'Ready', detail: 'Project setup and file organization.' },
  { name: 'UI Designer', status: 'Ready', detail: 'Dashboard screens and app layout.' },
  { name: 'Backend Builder', status: 'Ready', detail: 'API and local service structure.' },
  { name: 'Quality Check', status: 'Active', detail: 'Checks install, run, and release steps.' },
]

const projects = [
  { name: 'Genie Command Center', status: 'Running' },
  { name: 'Team Workspace', status: 'Ready' },
  { name: 'Voice Mode', status: 'Next' },
  { name: 'Desktop App Wrapper', status: 'Next' },
]

export default function App() {
  const [tab, setTab] = useState('Home')
  const [items, setItems] = useState(['Genie dashboard started.', 'Local app shell is running.', 'Workspace panels loaded.'])
  const [text, setText] = useState('')

  function submit(e) {
    e.preventDefault()
    if (!text.trim()) return
    setItems([`Mission: ${text.trim()}`, 'Genie: Received. I am organizing the next build step.', ...items])
    setText('')
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">G</div>
          <div>
            <h1>GENIE</h1>
            <p>Command Center</p>
          </div>
        </div>

        {['Home', 'Team', 'Projects', 'Voice', 'Settings'].map(name => (
          <button key={name} className={tab === name ? 'nav active' : 'nav'} onClick={() => setTab(name)}>
            {name}
          </button>
        ))}

        <div className="runtime-card">
          <span>Runtime</span>
          <strong>Local First</strong>
          <p>Desktop and mobile friendly app foundation.</p>
        </div>
      </aside>

      <main className="main">
        <header className="header">
          <div>
            <span className="eyebrow">xgraphicalx interface online</span>
            <h2>{tab}</h2>
          </div>
          <div className="status"><i /> LIVE</div>
        </header>

        <section className="cards">
          <div><span>Status</span><strong>Alive</strong></div>
          <div><span>Mode</span><strong>Local</strong></div>
          <div><span>Workers</span><strong>{workers.length}</strong></div>
          <div><span>Build</span><strong>Dashboard</strong></div>
        </section>

        {tab === 'Home' && (
          <div className="grid two">
            <section className="hero">
              <div className="orb">✦</div>
              <h3>Welcome back, Justin.</h3>
              <p>Genie is online as your main command screen. Use this page as the app foundation and keep building from here.</p>
              <form onSubmit={submit} className="command">
                <input value={text} onChange={e => setText(e.target.value)} placeholder="Tell Genie what to build next..." />
                <button>Send</button>
              </form>
            </section>

            <section className="panel">
              <h3>Live Feed</h3>
              <div className="feed">
                {items.map((item, index) => <div key={index}>{item}</div>)}
              </div>
            </section>
          </div>
        )}

        {tab === 'Team' && (
          <section className="panel">
            <h3>Team Workspace</h3>
            <div className="worker-grid">
              {workers.map(worker => (
                <article key={worker.name} className="worker">
                  <div><h4>{worker.name}</h4><span>{worker.status}</span></div>
                  <p>{worker.detail}</p>
                </article>
              ))}
            </div>
          </section>
        )}

        {tab === 'Projects' && (
          <section className="panel">
            <h3>Projects</h3>
            <div className="project-list">
              {projects.map(project => (
                <div key={project.name} className="project"><strong>{project.name}</strong><span>{project.status}</span></div>
              ))}
            </div>
          </section>
        )}

        {tab === 'Voice' && (
          <section className="panel voice">
            <div className="voice-orb">◉</div>
            <h3>Live Voice Mode</h3>
            <p>Interface prepared. Next step connects microphone input and spoken responses.</p>
            <button className="primary">Prepare Voice</button>
          </section>
        )}

        {tab === 'Settings' && (
          <section className="panel">
            <h3>Settings</h3>
            <div className="settings">
              <div><strong>Theme</strong><span>xgraphicalx dark command center</span></div>
              <div><strong>App Type</strong><span>Vite React frontend</span></div>
              <div><strong>Launch</strong><span>npm run dev</span></div>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
