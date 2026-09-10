const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function getToken() {
  return localStorage.getItem('bib_token')
}

export function setToken(token) {
  if (token) localStorage.setItem('bib_token', token)
  else localStorage.removeItem('bib_token')
}

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (res.status === 401) {
    setToken(null)
    if (!path.includes('/login')) window.location.href = '/login'
  }
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = text
  }
  if (!res.ok) {
    const detail = data?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : detail?.message || detail?.warnings?.join?.(' ') || res.statusText
    const err = new Error(message || 'Error de solicitud')
    err.detail = detail
    err.status = res.status
    throw err
  }
  return data
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
  put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: 'DELETE' }),
  exportUrl: (path) => `${API_URL}${path}`,
  apiUrl: API_URL,
}
