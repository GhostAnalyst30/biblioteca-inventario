import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.get('/api/dashboard'), api.get('/api/alerts?solo_no_leidas=true')])
      .then(([dash, al]) => {
        setData(dash)
        setAlerts(al.slice(0, 6))
      })
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="banner error">{error}</div>
  if (!data) return <div className="center">Cargando panel…</div>

  const cards = [
    { label: 'Libros', value: data.libros },
    { label: 'Disponibles', value: data.ejemplares_disponibles },
    { label: 'Préstamos activos', value: data.prestamos_activos },
    { label: 'Vencidos', value: data.prestamos_vencidos, danger: true },
    { label: 'Alertas', value: data.alertas_sin_leer, warn: true },
    { label: 'Score promedio', value: Math.round(data.score_promedio) },
  ]

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Panel operativo</h1>
          <p>Resumen del inventario y préstamos de la biblioteca.</p>
        </div>
        <Link className="btn primary" to="/prestamos">
          Nuevo préstamo
        </Link>
      </header>
      <div className="kpi-grid">
        {cards.map((c) => (
          <div key={c.label} className={`kpi ${c.danger ? 'danger' : ''} ${c.warn ? 'warn' : ''}`}>
            <span>{c.label}</span>
            <strong>{c.value}</strong>
          </div>
        ))}
      </div>
      <section className="panel">
        <div className="panel-head">
          <h2>Alertas recientes</h2>
          <Link to="/alertas">Ver todas</Link>
        </div>
        {alerts.length === 0 ? (
          <p className="muted">No hay alertas pendientes.</p>
        ) : (
          <ul className="alert-list">
            {alerts.map((a) => (
              <li key={a.id} className={`alert-item ${a.tipo}`}>
                <strong>{a.tipo.replace('_', ' ')}</strong>
                <span>{a.mensaje}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
