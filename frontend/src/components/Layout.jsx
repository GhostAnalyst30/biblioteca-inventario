import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const mainLinks = [
  { to: '/', label: 'Panel', end: true },
  { to: '/libros', label: 'Libros' },
  { to: '/estudiantes', label: 'Estudiantes' },
  { to: '/prestamos', label: 'Préstamos' },
]

const insightLinks = [
  { to: '/alertas', label: 'Alertas' },
  { to: '/analitica', label: 'Analítica' },
]

function Icon({ d }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  )
}

const icons = {
  '/': 'M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1v-9.5Z',
  '/libros': 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z',
  '/estudiantes': 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75',
  '/prestamos': 'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
  '/alertas': 'M10.3 21a1.9 1.9 0 0 0 3.4 0M18 8A6 6 0 1 0 6 8c0 7-3 9-3 9h18s-3-2-3-9',
  '/analitica': 'M18 20V10M12 20V4M6 20v-6',
  '/admin': 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V19a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H5a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H10a1.7 1.7 0 0 0 1-1.5V5a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V10c.5.3 1 .9 1.1 1.5H19a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z',
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState('')

  function handleLogout() {
    logout()
    navigate('/login')
  }

  function onSearch(e) {
    e.preventDefault()
    const term = q.trim()
    if (!term) return
    navigate(`/estudiantes?q=${encodeURIComponent(term)}`)
    setOpen(false)
  }

  const initials = (user?.full_name || 'U')
    .split(' ')
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()

  function renderLinks(items) {
    return items.map((l) => (
      <NavLink
        key={l.to}
        to={l.to}
        end={l.end}
        onClick={() => setOpen(false)}
        className={({ isActive }) => (isActive ? 'nav active' : 'nav')}
      >
        <Icon d={icons[l.to]} />
        {l.label}
      </NavLink>
    ))
  }

  return (
    <div className="shell">
      {open && <div className="sidebar-backdrop" onClick={() => setOpen(false)} />}
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="brand">
          <span className="brand-mark">BI</span>
          <div>
            <strong>Biblioteca</strong>
            <small>Control de inventario</small>
          </div>
        </div>
        <nav className="nav-group">
          <div className="nav-label">Operación</div>
          {renderLinks(mainLinks)}
          <div className="nav-label">Seguimiento</div>
          {renderLinks(insightLinks)}
          {user?.role === 'admin' && (
            <>
              <div className="nav-label">Sistema</div>
              <NavLink to="/admin" onClick={() => setOpen(false)} className={({ isActive }) => (isActive ? 'nav active' : 'nav')}>
                <Icon d={icons['/admin']} />
                Administración
              </NavLink>
            </>
          )}
        </nav>
        <div className="sidebar-foot">
          <div className="user-chip">
            <div className="user-avatar">{initials}</div>
            <div>
              <strong>{user?.full_name}</strong>
              <span>{user?.role}</span>
            </div>
          </div>
          <button className="btn ghost" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main className="content">
        <div className="topbar">
          <button className="menu-toggle" type="button" onClick={() => setOpen((v) => !v)}>
            Menú
          </button>
          <form className="topbar-search" onSubmit={onSearch}>
            <span className="search-ico">⌕</span>
            <input
              placeholder="Buscar estudiante por código o nombre…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </form>
          <button className="btn primary sm" type="button" onClick={() => navigate('/prestamos')}>
            Nuevo préstamo
          </button>
        </div>
        <Outlet />
      </main>
    </div>
  )
}
