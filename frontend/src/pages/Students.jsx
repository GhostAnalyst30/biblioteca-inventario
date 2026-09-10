import { useEffect, useState } from 'react'
import { api } from '../api'

const empty = { codigo: '', nombre: '', grado: '', seccion: '', telefono: '', email: '' }

export default function Students() {
  const [students, setStudents] = useState([])
  const [q, setQ] = useState('')
  const [form, setForm] = useState(empty)
  const [selected, setSelected] = useState(null)
  const [eligibility, setEligibility] = useState(null)
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')

  async function load(search = q) {
    setStudents(await api.get(`/api/students${search ? `?q=${encodeURIComponent(search)}` : ''}`))
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  async function createStudent(e) {
    e.preventDefault()
    try {
      await api.post('/api/students', form)
      setForm(empty)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function openStudent(s) {
    setSelected(s)
    const [elig, loans] = await Promise.all([
      api.get(`/api/students/${s.id}/eligibility`),
      api.get(`/api/students/${s.id}/loans`),
    ])
    setEligibility(elig)
    setHistory(loans)
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Estudiantes</h1>
          <p>Registro por código/ID, nombre, grado y score de cumplimiento.</p>
        </div>
        <div className="row">
          <input placeholder="Buscar código o nombre…" value={q} onChange={(e) => setQ(e.target.value)} />
          <button className="btn" onClick={() => load()}>
            Buscar
          </button>
        </div>
      </header>
      {error && <div className="banner error">{error}</div>}

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
                    <span className={`score ${s.reliability_score < 50 ? 'bad' : s.reliability_score < 80 ? 'mid' : 'good'}`}>
                      {s.reliability_score}
                    </span>
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
              <h2>{selected.nombre}</h2>
              <p className="muted">
                {selected.codigo} · Grado {selected.grado}
              </p>
              {eligibility && (
                <div className={`banner ${eligibility.eligible ? 'ok' : 'error'}`}>
                  <strong>{eligibility.prediccion}</strong>
                  <div>Score: {eligibility.reliability_score}</div>
                  {eligibility.warnings?.map((w) => (
                    <div key={w}>{w}</div>
                  ))}
                </div>
              )}
              <h3>Historial de préstamos</h3>
              <ul className="simple-list">
                {history.map((l) => (
                  <li key={l.id}>
                    <strong>{l.book_titulo}</strong> — {l.estado} · vencía {l.fecha_devolucion_esperada}
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
