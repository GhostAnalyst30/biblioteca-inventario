-- Biblioteca Inventario schema

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL UNIQUE,
  full_name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('admin', 'bibliotecario')),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS students (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo TEXT NOT NULL UNIQUE,
  nombre TEXT NOT NULL,
  grado TEXT NOT NULL,
  seccion TEXT,
  telefono TEXT,
  email TEXT,
  reliability_score INTEGER NOT NULL DEFAULT 100 CHECK (reliability_score BETWEEN 0 AND 100),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS books (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titulo TEXT NOT NULL,
  autor TEXT NOT NULL,
  isbn TEXT,
  categoria TEXT,
  editorial TEXT,
  anio INTEGER,
  descripcion TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS copies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  etiqueta TEXT NOT NULL UNIQUE,
  estado TEXT NOT NULL DEFAULT 'disponible'
    CHECK (estado IN ('disponible', 'prestado', 'reparacion', 'baja')),
  ubicacion TEXT,
  notas TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS loans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id UUID NOT NULL REFERENCES students(id),
  copy_id UUID NOT NULL REFERENCES copies(id),
  prestado_por UUID REFERENCES users(id),
  fecha_prestamo DATE NOT NULL DEFAULT CURRENT_DATE,
  fecha_devolucion_esperada DATE NOT NULL,
  fecha_devolucion_real DATE,
  estado TEXT NOT NULL DEFAULT 'activo'
    CHECK (estado IN ('activo', 'devuelto', 'vencido')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS loan_comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
  tipo TEXT NOT NULL CHECK (tipo IN ('entrega', 'devolucion')),
  condicion TEXT NOT NULL CHECK (condicion IN ('bueno', 'regular', 'danado')),
  comentario TEXT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
  tipo TEXT NOT NULL CHECK (tipo IN ('aviso_proximo', 'urgente', 'vencido')),
  mensaje TEXT NOT NULL,
  leida BOOLEAN NOT NULL DEFAULT FALSE,
  generada_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (loan_id, tipo)
);

CREATE TABLE IF NOT EXISTS settings (
  id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  dias_prestamo_default INTEGER NOT NULL DEFAULT 14,
  umbral_aviso_dias INTEGER NOT NULL DEFAULT 3,
  umbral_urgente_dias INTEGER NOT NULL DEFAULT 1,
  score_minimo_prestamo INTEGER NOT NULL DEFAULT 50,
  bloquear_score_bajo BOOLEAN NOT NULL DEFAULT FALSE,
  bloquear_vencidos BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  accion TEXT NOT NULL,
  entidad TEXT,
  entidad_id TEXT,
  detalle JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_copies_book ON copies(book_id);
CREATE INDEX IF NOT EXISTS idx_copies_estado ON copies(estado);
CREATE INDEX IF NOT EXISTS idx_loans_student ON loans(student_id);
CREATE INDEX IF NOT EXISTS idx_loans_estado ON loans(estado);
CREATE INDEX IF NOT EXISTS idx_loans_due ON loans(fecha_devolucion_esperada);
CREATE INDEX IF NOT EXISTS idx_alerts_leida ON alerts(leida);
CREATE INDEX IF NOT EXISTS idx_students_grado ON students(grado);
CREATE INDEX IF NOT EXISTS idx_books_titulo ON books(titulo);

INSERT INTO settings (id) VALUES (1) ON CONFLICT (id) DO NOTHING;

-- Backend uses direct Postgres connection; revoke public Data API access
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE books ENABLE ROW LEVEL SECURITY;
ALTER TABLE copies ENABLE ROW LEVEL SECURITY;
ALTER TABLE loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE loan_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
