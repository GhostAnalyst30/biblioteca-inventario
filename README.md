# Biblioteca Inventario

Sistema de inventario y préstamos de biblioteca.

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

## Desarrollo local

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # configurar DATABASE_URL
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
