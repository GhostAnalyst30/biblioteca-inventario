import { useEffect, useState } from 'react'
import { api } from '../api'

const emptyBook = { titulo: '', autor: '', isbn: '', categoria: '', editorial: '', anio: '', descripcion: '' }

export default function Books() {
  const [books, setBooks] = useState([])
  const [q, setQ] = useState('')
  const [form, setForm] = useState(emptyBook)
  const [copyForms, setCopyForms] = useState({})
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  async function load(search = q) {
    const data = await api.get(`/api/books${search ? `?q=${encodeURIComponent(search)}` : ''}`)
    setBooks(data)
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  async function createBook(e) {
    e.preventDefault()
    setError('')
    try {
      await api.post('/api/books', {
        ...form,
        anio: form.anio ? Number(form.anio) : null,
      })
      setForm(emptyBook)
      setMsg('Libro agregado')
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function removeBook(id) {
    if (!confirm('¿Dar de baja este libro?')) return
    await api.delete(`/api/books/${id}`)
    await load()
  }

  async function addCopy(bookId) {
    const etiqueta = copyForms[bookId]
    if (!etiqueta) return
    try {
      await api.post(`/api/books/${bookId}/copies`, { etiqueta })
      setCopyForms((s) => ({ ...s, [bookId]: '' }))
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function setCopyEstado(copyId, estado) {
    await api.patch(`/api/copies/${copyId}`, { estado })
    await load()
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Libros y ejemplares</h1>
          <p>Inventario, alta/baja y separación por estado.</p>
        </div>
        <div className="row">
          <input placeholder="Buscar título, autor, ISBN…" value={q} onChange={(e) => setQ(e.target.value)} />
          <button className="btn" onClick={() => load()}>
            Buscar
          </button>
        </div>
      </header>
      {error && <div className="banner error">{error}</div>}
      {msg && <div className="banner ok">{msg}</div>}

      <form className="panel form-grid" onSubmit={createBook}>
        <h2>Agregar libro</h2>
        <input required placeholder="Título" value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} />
        <input required placeholder="Autor" value={form.autor} onChange={(e) => setForm({ ...form, autor: e.target.value })} />
        <input placeholder="ISBN" value={form.isbn} onChange={(e) => setForm({ ...form, isbn: e.target.value })} />
        <input placeholder="Categoría" value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value })} />
        <input placeholder="Editorial" value={form.editorial} onChange={(e) => setForm({ ...form, editorial: e.target.value })} />
        <input placeholder="Año" value={form.anio} onChange={(e) => setForm({ ...form, anio: e.target.value })} />
        <button className="btn primary" type="submit">
          Guardar libro
        </button>
      </form>

      <div className="stack">
        {books.map((b) => (
          <article key={b.id} className="panel">
            <div className="panel-head">
              <div>
                <h2>{b.titulo}</h2>
                <p className="muted">
                  {b.autor} · {b.categoria || 'Sin categoría'} · {b.disponibles}/{b.total_copies} disponibles
                </p>
              </div>
              <button className="btn danger ghost" onClick={() => removeBook(b.id)}>
                Eliminar
              </button>
            </div>
            <div className="row wrap">
              {b.copies.map((c) => (
                <div key={c.id} className="chip-card">
                  <strong>{c.etiqueta}</strong>
                  <span className={`badge ${c.estado}`}>{c.estado}</span>
                  <select value={c.estado} onChange={(e) => setCopyEstado(c.id, e.target.value)}>
                    <option value="disponible">disponible</option>
                    <option value="prestado">prestado</option>
                    <option value="reparacion">reparacion</option>
                    <option value="baja">baja</option>
                  </select>
                </div>
              ))}
            </div>
            <div className="row">
              <input
                placeholder="Nueva etiqueta de ejemplar"
                value={copyForms[b.id] || ''}
                onChange={(e) => setCopyForms({ ...copyForms, [b.id]: e.target.value })}
              />
              <button className="btn" type="button" onClick={() => addCopy(b.id)}>
                Agregar ejemplar
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
