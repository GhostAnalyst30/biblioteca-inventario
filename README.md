# Biblioteca Inventario

Sistema de inventario y préstamos de biblioteca.

## Probar en producción

- **App:** https://biblioteca-inventario.vercel.app
- **API:** https://biblioteca-inventario-api.onrender.com/health
- **GitHub:** https://github.com/GhostAnalyst30/biblioteca-inventario
- **Supabase:** proyecto `biblioteca-inventario` (`doyemhftlardsgztfxzh`)

## Stack

- **Frontend:** React + JavaScript (Vite) → Vercel
- **Backend:** Python FastAPI → Render
- **Base de datos:** PostgreSQL (Supabase)

## Roles

- `admin` — usuarios, configuración, todo lo operativo
- `bibliotecario` — libros, estudiantes, préstamos, alertas, analítica

## Credenciales demo

| Rol | Email | Contraseña |
|-----|-------|------------|
| Admin | `admin@biblioteca.app` | `Admin123!` |
| Bibliotecario | `biblio@biblioteca.app` | `Biblio123!` |

## Funcionalidades

- Inventario de libros y ejemplares (alta/baja/estados)
- Estudiantes por código/ID, nombre y grado
- Préstamos con fecha de devolución definida por el staff
- Comentarios de estado del libro al entregar y devolver
- Alertas próximas / urgentes / vencidas
- Score de cumplimiento y predicción al prestar
- Analítica por grado/categoría + export CSV
- Administración de usuarios y umbrales de alerta

## Desarrollo local

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # configurar DATABASE_URL (pooler de Supabase)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

## API útil

- `POST /api/auth/login`
- CRUD libros / ejemplares / estudiantes / préstamos
- `GET /api/alerts` — genera avisos de devolución
- `GET /api/analytics` — filtros por grado y fechas
- `POST /api/jobs/generate-alerts?secret=...` — job diario
