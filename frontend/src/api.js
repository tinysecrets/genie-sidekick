const API = import.meta.env.VITE_BACKEND_URL || ''
const TOKEN_KEY = 'genie_token'

const token = () => localStorage.getItem(TOKEN_KEY) || ''
const headers = () => ({
  'Content-Type': 'application/json',
  ...(token() ? { Authorization: `Bearer ${token()}` } : {}),
})

async function jsonOrThrow(r) {
  const text = await r.text()
  let body = {}
  try { body = text ? JSON.parse(text) : {} } catch { body = { detail: text } }
  if (!r.ok) throw new Error(body.detail || `${r.status} ${r.statusText}`)
  return body
}

export async function login(email, password) {
  const r = await fetch(`${API}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  const data = await jsonOrThrow(r)
  localStorage.setItem(TOKEN_KEY, data.access_token)
  return data
}

export const logout = () => localStorage.removeItem(TOKEN_KEY)
export const isLoggedIn = () => !!token()

export async function listProviders() {
  return jsonOrThrow(await fetch(`${API}/api/genie/providers`, { headers: headers() }))
}

export async function chat(message, sessionId, provider) {
  return jsonOrThrow(await fetch(`${API}/api/genie/chat`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ message, session_id: sessionId, provider }),
  }))
}

export async function listSessions() {
  return jsonOrThrow(await fetch(`${API}/api/genie/sessions`, { headers: headers() }))
}

export async function loadHistory(sessionId) {
  return jsonOrThrow(await fetch(`${API}/api/genie/history/${sessionId}`, { headers: headers() }))
}

export async function newSession() {
  return jsonOrThrow(await fetch(`${API}/api/genie/new-session`, { method: 'POST', headers: headers() }))
}
