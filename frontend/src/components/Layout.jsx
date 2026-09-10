import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const links = [
  { to: '/', label: 'Panel', end: true },
  { to: '/libros', label: 'Libros' },
  { to: '/estudiantes', label: 'Estudiantes' },
  { to: '/prestamos', label: 'Préstamos' },
  { to: '/alertas', label: 'Alertas' },
  { to: '/analitica', label: 'Analítica' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">BI</span>
          <div>
            <strong>Biblioteca</strong>
            <small>Inventario</small>
          </div>
        </div>
        <nav>
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={({ isActive }) => (isActive ? 'nav active' : 'nav')}>
              {l.label}
            </NavLink>
          ))}
          {user?.role === 'admin' && (
            <NavLink to="/admin" className={({ isActive }) => (isActive ? 'nav active' : 'nav')}>
              Administración
            </NavLink>
          )}
        </nav>
        <div className="sidebar-foot">
          <div className="user-chip">
            <strong>{user?.full_name}</strong>
            <span>{user?.role}</span>
          </div>
          <button className="btn ghost" onClick={handleLogout}>
            Salir
          </button>
        </div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
