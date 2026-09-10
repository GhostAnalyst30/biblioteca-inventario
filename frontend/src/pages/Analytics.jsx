import { useEffect, useState } from 'react'
import { api, getToken } from '../api'

export default function Analytics() {
  const [data, setData] = useState(null)
  const [grado, setGrado] = useState('')
  const [error, setError] = useState('')

  async function load(g = grado) {
    const qs = g ? `?grado=${encodeURIComponent(g)}` : ''
    setData(await api.get(`/api/analytics${qs}`))
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  async function exportCsv() {
    const qs = grado ? `?grado=${encodeURIComponent(grado)}` : ''
    const res = await fetch(api.exportUrl(`/api/analytics/export${qs}`), {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'prestamos.csv'
    a.click()
  }

  if (error) return <div className="banner error">{error}</div>
  if (!data) return <div className="center">Cargando analítica…</div>

  const maxGrado = Math.max(...data.por_grado.map((x) => x.prestamos), 1)

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Analítica</h1>
          <p>Estudio por grado, categorías, cumplimiento y predicción de devolución.</p>
        </div>
        <div className="row">
          <input placeholder="Filtrar grado" value={grado} onChange={(e) => setGrado(e.target.value)} />
          <button className="btn" onClick={() => load()}>
            Aplicar
          </button>
          <button className="btn primary" onClick={exportCsv}>
            Exportar CSV
          </button>
        </div>
      </header>

      <div className="kpi-grid">
        <div className="kpi">
          <span>Tasa de cumplimiento</span>
          <strong>{data.cumplimiento.tasa_cumplimiento}%</strong>
        </div>
        <div className="kpi">
          <span>A tiempo</span>
          <strong>{data.cumplimiento.a_tiempo}</strong>
        </div>
        <div className="kpi warn">
          <span>Tarde</span>
          <strong>{data.cumplimiento.tarde}</strong>
        </div>
        <div className="kpi">
          <span>Activos</span>
          <strong>{data.cumplimiento.activos}</strong>
        </div>
      </div>

      <div className="split">
        <section className="panel">
          <h2>Préstamos por grado</h2>
          <div className="bars">
            {data.por_grado.map((row) => (
              <div key={row.grado} className="bar-row">
                <span>{row.grado}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${(row.prestamos / maxGrado) * 100}%` }} />
                </div>
                <strong>{row.prestamos}</strong>
              </div>
            ))}
            {data.por_grado.length === 0 && <p className="muted">Sin datos</p>}
          </div>
        </section>
        <section className="panel">
          <h2>Por categoría</h2>
          <ul className="simple-list">
            {data.por_categoria.map((row) => (
              <li key={row.categoria}>
                <strong>{row.categoria}</strong>: {row.prestamos}
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="panel">
        <h2>Top libros prestados</h2>
        <table>
          <thead>
            <tr>
              <th>Título</th>
              <th>Autor</th>
              <th>Préstamos</th>
            </tr>
          </thead>
          <tbody>
            {data.top_libros.map((b) => (
              <tr key={b.titulo + b.autor}>
                <td>{b.titulo}</td>
                <td>{b.autor}</td>
                <td>{b.prestamos}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
