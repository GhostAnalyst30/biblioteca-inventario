import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Admin() {
  const [users, setUsers] = useState([])
  const [settings, setSettings] = useState(null)
  const [form, setForm] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'bibliotecario',
  })
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  async function load() {
    const [u, s] = await Promise.all([api.get('/api/users'), api.get('/api/settings')])
    setUsers(u)
    setSettings(s)
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  async function createUser(e) {
    e.preventDefault()
    try {
      await api.post('/api/users', form)
      setForm({ email: '', full_name: '', password: '', role: 'bibliotecario' })
      setMsg('Usuario creado')
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function saveSettings(e) {
    e.preventDefault()
    try {
      const updated = await api.put('/api/settings', settings)
      setSettings(updated)
      setMsg('Configuración guardada')
    } catch (err) {
      setError(err.message)
    }
  }

  if (!settings) return <div className="center">Cargando…</div>

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Administración</h1>
          <p>Usuarios del sistema y reglas de préstamo / alertas.</p>
        </div>
      </header>
      {error && <div className="banner error">{error}</div>}
      {msg && <div className="banner ok">{msg}</div>}

      <div className="split">
        <form className="panel form-grid" onSubmit={createUser}>
          <h2>Crear usuario</h2>
          <input required placeholder="Nombre" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input required type="password" placeholder="Contraseña" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            <option value="bibliotecario">Bibliotecario</option>
            <option value="admin">Admin</option>
          </select>
          <button className="btn primary">Crear</button>
          <h3>Usuarios</h3>
          <ul className="simple-list">
            {users.map((u) => (
              <li key={u.id}>
                <strong>{u.full_name}</strong> — {u.email} ({u.role}) {u.active ? '' : '[inactivo]'}
              </li>
            ))}
          </ul>
        </form>

        <form className="panel form-grid" onSubmit={saveSettings}>
          <h2>Configuración</h2>
          <label>
            Días de préstamo por defecto
            <input
              type="number"
              value={settings.dias_prestamo_default}
              onChange={(e) => setSettings({ ...settings, dias_prestamo_default: Number(e.target.value) })}
            />
          </label>
          <label>
            Aviso con N días de anticipación
            <input
              type="number"
              value={settings.umbral_aviso_dias}
              onChange={(e) => setSettings({ ...settings, umbral_aviso_dias: Number(e.target.value) })}
            />
          </label>
          <label>
            Urgente con N días
            <input
              type="number"
              value={settings.umbral_urgente_dias}
              onChange={(e) => setSettings({ ...settings, umbral_urgente_dias: Number(e.target.value) })}
            />
          </label>
          <label>
            Score mínimo para prestar
            <input
              type="number"
              value={settings.score_minimo_prestamo}
              onChange={(e) => setSettings({ ...settings, score_minimo_prestamo: Number(e.target.value) })}
            />
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={settings.bloquear_score_bajo}
              onChange={(e) => setSettings({ ...settings, bloquear_score_bajo: e.target.checked })}
            />
            Bloquear si score bajo
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={settings.bloquear_vencidos}
              onChange={(e) => setSettings({ ...settings, bloquear_vencidos: e.target.checked })}
            />
            Bloquear si tiene vencidos
          </label>
          <button className="btn primary">Guardar configuración</button>
        </form>
      </div>
    </div>
  )
}
