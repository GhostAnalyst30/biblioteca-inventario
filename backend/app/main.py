from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.auth import hash_password
from app.config import get_settings
from app.database import SessionLocal
from app.models import AppSettings, User
from app.routers import router


def seed_data() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        if not db.get(AppSettings, 1):
            db.add(AppSettings(id=1))

        admin = db.scalar(select(User).where(User.email == settings.admin_seed_email.lower()))
        if not admin:
            db.add(
                User(
                    email=settings.admin_seed_email.lower(),
                    full_name=settings.admin_seed_name,
                    password_hash=hash_password(settings.admin_seed_password),
                    role="admin",
                )
            )

        librarian = db.scalar(select(User).where(User.email == settings.librarian_seed_email.lower()))
        if not librarian:
            db.add(
                User(
                    email=settings.librarian_seed_email.lower(),
                    full_name=settings.librarian_seed_name,
                    password_hash=hash_password(settings.librarian_seed_password),
                    role="bibliotecario",
                )
            )
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_data()
    yield


app = FastAPI(title="Biblioteca Inventario API", version="1.0.0", lifespan=lifespan)
settings = get_settings()

origins = settings.cors_origin_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
