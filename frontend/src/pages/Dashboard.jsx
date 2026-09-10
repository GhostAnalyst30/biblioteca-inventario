import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [loans, setLoans] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api.get('/api/dashboard'),
      api.get('/api/alerts?solo_no_leidas=true'),
      api.get('/api/loans?estado=activo'),
    ])
      .then(([dash, al, ln]) => {
        setData(dash)
        setAlerts(al.slice(0, 5))
        setLoans(ln.slice(0, 5))
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
          <p>Resumen del inventario, alertas y préstamos en curso.</p>
        </div>
        <div className="row">
          <Link className="btn" to="/estudiantes">
            Estudiantes
          </Link>
          <Link className="btn primary" to="/prestamos">
            Nuevo préstamo
          </Link>
        </div>
      </header>
      <div className="kpi-grid">
        {cards.map((c) => (
          <div key={c.label} className={`kpi ${c.danger ? 'danger' : ''} ${c.warn ? 'warn' : ''}`}>
            <span>{c.label}</span>
            <strong>{c.value}</strong>
          </div>
        ))}
      </div>
      <div className="split">
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
                  <div>
                    <strong>{a.tipo.replace('_', ' ')}</strong>
                    <span>{a.mensaje}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section className="panel">
          <div className="panel-head">
            <h2>Próximas devoluciones</h2>
            <Link to="/prestamos">Ver préstamos</Link>
          </div>
          {loans.length === 0 ? (
            <p className="muted">Sin préstamos activos.</p>
          ) : (
            <ul className="simple-list">
              {loans.map((l) => (
                <li key={l.id}>
                  <strong>{l.book_titulo}</strong>
                  <div className="muted">
                    {l.student_nombre} · {l.fecha_devolucion_esperada}
                    {l.dias_restantes != null && (
                      <span className={l.dias_restantes < 0 ? ' danger-text' : l.dias_restantes <= 3 ? ' warn-text' : ''}>
                        {' '}
                        ({l.dias_restantes < 0 ? `${Math.abs(l.dias_restantes)}d atraso` : `${l.dias_restantes}d`})
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
