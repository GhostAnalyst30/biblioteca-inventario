import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [error, setError] = useState('')

  async function load() {
    setAlerts(await api.get('/api/alerts'))
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  async function markRead(id) {
    await api.post(`/api/alerts/${id}/read`)
    await load()
  }

  async function markAll() {
    await api.post('/api/alerts/read-all')
    await load()
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Alertas de devolución</h1>
          <p>Avisos próximos, urgentes y vencidos según la fecha definida al prestar.</p>
        </div>
        <button className="btn" onClick={markAll}>
          Marcar todas leídas
        </button>
      </header>
      {error && <div className="banner error">{error}</div>}
      <ul className="alert-list big">
        {alerts.map((a) => (
          <li key={a.id} className={`alert-item ${a.tipo} ${a.leida ? 'read' : ''}`}>
            <div>
              <strong>{a.tipo.replace('_', ' ')}</strong>
              <span>{a.mensaje}</span>
              <small>
                {a.student_nombre} · {a.book_titulo} · vence {a.fecha_devolucion_esperada}
              </small>
            </div>
            {!a.leida && (
              <button className="btn ghost" onClick={() => markRead(a.id)}>
                Marcar leída
              </button>
            )}
          </li>
        ))}
        {alerts.length === 0 && <li className="muted">Sin alertas</li>}
      </ul>
    </div>
  )
}
