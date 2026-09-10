import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api'

const empty = { codigo: '', nombre: '', grado: '', seccion: '', telefono: '', email: '' }

function scoreClass(n) {
  if (n < 50) return 'bad'
  if (n < 80) return 'mid'
  return 'good'
}

export default function Students() {
  const [params] = useSearchParams()
  const [students, setStudents] = useState([])
  const [q, setQ] = useState(params.get('q') || '')
  const [form, setForm] = useState(empty)
  const [selected, setSelected] = useState(null)
  const [eligibility, setEligibility] = useState(null)
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  async function load(search = q) {
    setStudents(await api.get(`/api/students${search ? `?q=${encodeURIComponent(search)}` : ''}`))
  }

  useEffect(() => {
    const initial = params.get('q') || ''
    setQ(initial)
    load(initial).catch((e) => setError(e.message))
  }, [params])

  async function createStudent(e) {
    e.preventDefault()
    try {
      await api.post('/api/students', form)
      setForm(empty)
      setMsg('Estudiante registrado')
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function openStudent(s) {
    setSelected(s)
    setMsg('')
    const [elig, loans] = await Promise.all([
      api.get(`/api/students/${s.id}/eligibility`),
      api.get(`/api/students/${s.id}/loans`),
    ])
    setEligibility(elig)
    setHistory(loans)
  }

  async function recalc() {
    if (!selected) return
    const data = await api.post(`/api/students/${selected.id}/recalculate-score`)
    setMsg(`Score recalculado: ${data.reliability_score}`)
    setEligibility((prev) => ({
      ...prev,
      reliability_score: data.reliability_score,
      breakdown: data.breakdown,
    }))
    await load()
    const updated = (await api.get(`/api/students`)).find((s) => s.id === selected.id)
    if (updated) setSelected(updated)
  }

  const b = eligibility?.breakdown

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Estudiantes</h1>
          <p>Registro, historial y score de cumplimiento de devoluciones.</p>
        </div>
        <div className="row">
          <input placeholder="Buscar código o nombre…" value={q} onChange={(e) => setQ(e.target.value)} />
          <button className="btn" onClick={() => load()}>
            Buscar
          </button>
        </div>
      </header>
      {error && <div className="banner error">{error}</div>}
      {msg && <div className="banner ok">{msg}</div>}

      <form className="panel form-grid" onSubmit={createStudent}>
        <h2>Registrar estudiante</h2>
        <input required placeholder="Código / ID" value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} />
        <input required placeholder="Nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
        <input required placeholder="Grado" value={form.grado} onChange={(e) => setForm({ ...form, grado: e.target.value })} />
        <input placeholder="Sección" value={form.seccion} onChange={(e) => setForm({ ...form, seccion: e.target.value })} />
        <input placeholder="Teléfono" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} />
        <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <button className="btn primary">Guardar</button>
      </form>

      <div className="split">
        <div className="panel">
          <table>
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th>Grado</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id} onClick={() => openStudent(s)} className={selected?.id === s.id ? 'selected' : ''}>
                  <td>{s.codigo}</td>
                  <td>{s.nombre}</td>
                  <td>{s.grado}</td>
                  <td>
                    <span className={`score ${scoreClass(s.reliability_score)}`}>{s.reliability_score}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel">
          {!selected ? (
            <p className="muted">Selecciona un estudiante para ver predicción e historial.</p>
          ) : (
            <>
              <div className="panel-head">
                <div>
                  <h2>{selected.nombre}</h2>
                  <p className="muted">
                    {selected.codigo} · Grado {selected.grado}
                  </p>
                </div>
                <div className={`score-ring ${scoreClass(eligibility?.reliability_score ?? selected.reliability_score)}`}>
                  {eligibility?.reliability_score ?? selected.reliability_score}
                </div>
              </div>
              {eligibility && (
                <div className={`banner ${eligibility.eligible ? 'ok' : 'error'}`}>
                  <strong>{eligibility.prediccion}</strong>
                  {eligibility.warnings?.map((w) => (
                    <div key={w}>{w}</div>
                  ))}
                </div>
              )}
              {b && (
                <div className="stat-pills" style={{ marginTop: '0.75rem' }}>
                  <span className="stat-pill">
                    Devueltos <strong>{b.devueltos}</strong>
                  </span>
                  <span className="stat-pill">
                    A tiempo <strong>{b.a_tiempo}</strong>
                  </span>
                  <span className="stat-pill">
                    Tarde <strong>{b.tarde}</strong>
                  </span>
                  <span className="stat-pill">
                    Vencidos <strong>{b.vencidos_abiertos}</strong>
                  </span>
                  {b.tasa_puntualidad != null && (
                    <span className="stat-pill">
                      Puntualidad <strong>{b.tasa_puntualidad}%</strong>
                    </span>
                  )}
                </div>
              )}
              <div className="row" style={{ marginTop: '0.85rem' }}>
                <button className="btn sm" type="button" onClick={recalc}>
                  Recalcular score
                </button>
              </div>
              <h3 style={{ marginTop: '1rem' }}>Historial de préstamos</h3>
              <ul className="simple-list">
                {history.map((l) => (
                  <li key={l.id}>
                    <strong>{l.book_titulo}</strong> — <span className={`badge ${l.estado}`}>{l.estado}</span> · vencía{' '}
                    {l.fecha_devolucion_esperada}
                    {l.fecha_devolucion_real ? ` · entregó ${l.fecha_devolucion_real}` : ''}
                  </li>
                ))}
                {history.length === 0 && <li className="muted">Sin préstamos</li>}
              </ul>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
