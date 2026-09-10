import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Loans() {
  const [loans, setLoans] = useState([])
  const [students, setStudents] = useState([])
  const [copies, setCopies] = useState([])
  const [estado, setEstado] = useState('activo')
  const [form, setForm] = useState({
    student_id: '',
    copy_id: '',
    fecha_devolucion_esperada: '',
    condicion_entrega: 'bueno',
    comentario_entrega: '',
    forzar: false,
  })
  const [returnForm, setReturnForm] = useState({})
  const [error, setError] = useState('')
  const [warnings, setWarnings] = useState([])
  const [msg, setMsg] = useState('')

  async function load() {
    const qs = estado === 'todos' ? '' : `?estado=${estado}`
    const [l, s, c] = await Promise.all([
      api.get(`/api/loans${qs}`),
      api.get('/api/students'),
      api.get('/api/copies?estado=disponible'),
    ])
    setLoans(l)
    setStudents(s)
    setCopies(c)
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [estado])

  async function createLoan(e) {
    e.preventDefault()
    setError('')
    setWarnings([])
    setMsg('')
    try {
      const payload = {
        ...form,
        fecha_devolucion_esperada: form.fecha_devolucion_esperada || null,
      }
      const result = await api.post('/api/loans', payload)
      if (result.warnings?.length) setWarnings(result.warnings)
      setForm({
        student_id: '',
        copy_id: '',
        fecha_devolucion_esperada: '',
        condicion_entrega: 'bueno',
        comentario_entrega: '',
        forzar: false,
      })
      setMsg('Préstamo registrado')
      await load()
    } catch (err) {
      if (err.detail?.warnings) setWarnings(err.detail.warnings)
      setError(err.message)
    }
  }

  async function returnLoan(loanId) {
    const data = returnForm[loanId] || { condicion_devolucion: 'bueno', comentario_devolucion: '' }
    setError('')
    setMsg('')
    try {
      const result = await api.post(`/api/loans/${loanId}/return`, data)
      if (result.score_antes != null && result.score_despues != null) {
        setMsg(
          `Devolución registrada. Score del estudiante: ${result.score_antes} → ${result.score_despues}`
        )
      } else {
        setMsg('Devolución registrada')
      }
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function renewLoan(loanId) {
    setError('')
    setMsg('')
    try {
      const result = await api.post(`/api/loans/${loanId}/renew?dias=7`)
      setMsg(`Préstamo renovado. Nueva fecha: ${result.fecha_devolucion_esperada}`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Préstamos</h1>
          <p>Asignar libros, fijar fecha de devolución y registrar estado al entregar/devolver.</p>
        </div>
        <select value={estado} onChange={(e) => setEstado(e.target.value)}>
          <option value="activo">Activos</option>
          <option value="vencido">Vencidos</option>
          <option value="devuelto">Devueltos</option>
          <option value="todos">Todos</option>
        </select>
      </header>
      {error && <div className="banner error">{error}</div>}
      {msg && <div className="banner ok">{msg}</div>}
      {warnings.length > 0 && (
        <div className="banner warn">
          {warnings.map((w) => (
            <div key={w}>{w}</div>
          ))}
        </div>
      )}

      <form className="panel form-grid" onSubmit={createLoan}>
        <h2>Registrar préstamo</h2>
        <select required value={form.student_id} onChange={(e) => setForm({ ...form, student_id: e.target.value })}>
          <option value="">Estudiante…</option>
          {students.map((s) => (
            <option key={s.id} value={s.id}>
              {s.codigo} — {s.nombre} (G{s.grado}, score {s.reliability_score})
            </option>
          ))}
        </select>
        <select required value={form.copy_id} onChange={(e) => setForm({ ...form, copy_id: e.target.value })}>
          <option value="">Ejemplar disponible…</option>
          {copies.map((c) => (
            <option key={c.id} value={c.id}>
              {c.etiqueta} — {c.book_titulo}
            </option>
          ))}
        </select>
        <label>
          Fecha devolución esperada
          <input
            type="date"
            value={form.fecha_devolucion_esperada}
            onChange={(e) => setForm({ ...form, fecha_devolucion_esperada: e.target.value })}
          />
        </label>
        <select value={form.condicion_entrega} onChange={(e) => setForm({ ...form, condicion_entrega: e.target.value })}>
          <option value="bueno">Estado entrega: bueno</option>
          <option value="regular">Estado entrega: regular</option>
          <option value="danado">Estado entrega: dañado</option>
        </select>
        <input
          placeholder="Comentario de entrega"
          value={form.comentario_entrega}
          onChange={(e) => setForm({ ...form, comentario_entrega: e.target.value })}
        />
        <label className="check">
          <input type="checkbox" checked={form.forzar} onChange={(e) => setForm({ ...form, forzar: e.target.checked })} />
          Forzar préstamo (ignorar bloqueos)
        </label>
        <button className="btn primary">Prestar</button>
      </form>

      <div className="stack">
        {loans.map((l) => (
          <article key={l.id} className={`panel loan ${l.estado}`}>
            <div className="panel-head">
              <div>
                <h2>{l.book_titulo}</h2>
                <p className="muted">
                  {l.student_nombre} ({l.student_codigo}) · Grado {l.student_grado} · Ejemplar {l.copy_etiqueta}
                </p>
                <p>
                  Prestado: {l.fecha_prestamo} · Devolver: <strong>{l.fecha_devolucion_esperada}</strong>
                  {l.dias_restantes != null && l.estado !== 'devuelto' && (
                    <span className={l.dias_restantes < 0 ? 'danger-text' : l.dias_restantes <= 3 ? 'warn-text' : ''}>
                      {' '}
                      ({l.dias_restantes < 0 ? `${Math.abs(l.dias_restantes)} días de atraso` : `${l.dias_restantes} días restantes`})
                    </span>
                  )}
                </p>
              </div>
              <span className={`badge ${l.estado}`}>{l.estado}</span>
            </div>
            {l.comments?.length > 0 && (
              <ul className="simple-list">
                {l.comments.map((c) => (
                  <li key={c.id}>
                    <strong>{c.tipo}</strong>: {c.condicion} {c.comentario ? `— ${c.comentario}` : ''}
                  </li>
                ))}
              </ul>
            )}
            {l.estado !== 'devuelto' && (
              <div className="row">
                <select
                  value={returnForm[l.id]?.condicion_devolucion || 'bueno'}
                  onChange={(e) =>
                    setReturnForm({
                      ...returnForm,
                      [l.id]: { ...returnForm[l.id], condicion_devolucion: e.target.value },
                    })
                  }
                >
                  <option value="bueno">Devuelve: bueno</option>
                  <option value="regular">Devuelve: regular</option>
                  <option value="danado">Devuelve: dañado</option>
                </select>
                <input
                  placeholder="Comentario de devolución"
                  value={returnForm[l.id]?.comentario_devolucion || ''}
                  onChange={(e) =>
                    setReturnForm({
                      ...returnForm,
                      [l.id]: { ...returnForm[l.id], comentario_devolucion: e.target.value },
                    })
                  }
                />
                <button className="btn primary" onClick={() => returnLoan(l.id)}>
                  Registrar devolución
                </button>
                <button className="btn" onClick={() => renewLoan(l.id)}>
                  Renovar +7 días
                </button>
              </div>
            )}
            {l.estado === 'devuelto' && l.student_score != null && (
              <p className="muted">
                Score actual del estudiante: <strong className="score">{l.student_score}</strong>
              </p>
            )}
          </article>
        ))}
      </div>
    </div>
  )
}
