from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Student(Base):
    __tablename__ = "students"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    codigo: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    grado: Mapped[str] = mapped_column(Text, nullable=False)
    seccion: Mapped[str | None] = mapped_column(Text)
    telefono: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    reliability_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    loans: Mapped[list["Loan"]] = relationship(back_populates="student")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    autor: Mapped[str] = mapped_column(Text, nullable=False)
    isbn: Mapped[str | None] = mapped_column(Text)
    categoria: Mapped[str | None] = mapped_column(Text)
    editorial: Mapped[str | None] = mapped_column(Text)
    anio: Mapped[int | None] = mapped_column(Integer)
    descripcion: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    copies: Mapped[list["Copy"]] = relationship(back_populates="book", cascade="all, delete-orphan")


class Copy(Base):
    __tablename__ = "copies"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    book_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    etiqueta: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    estado: Mapped[str] = mapped_column(Text, default="disponible", nullable=False)
    ubicacion: Mapped[str | None] = mapped_column(Text)
    notas: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    book: Mapped[Book] = relationship(back_populates="copies")
    loans: Mapped[list["Loan"]] = relationship(back_populates="copy")


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    copy_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("copies.id"), nullable=False)
    prestado_por: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    fecha_prestamo: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    fecha_devolucion_esperada: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_devolucion_real: Mapped[date | None] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(Text, default="activo", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student: Mapped[Student] = relationship(back_populates="loans")
    copy: Mapped[Copy] = relationship(back_populates="loans")
    comments: Mapped[list["LoanComment"]] = relationship(back_populates="loan", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="loan", cascade="all, delete-orphan")


class LoanComment(Base):
    __tablename__ = "loan_comments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    loan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    condicion: Mapped[str] = mapped_column(Text, nullable=False)
    comentario: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    loan: Mapped[Loan] = relationship(back_populates="comments")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("loan_id", "tipo", name="alerts_loan_id_tipo_key"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    loan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    leida: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    generada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    loan: Mapped[Loan] = relationship(back_populates="alerts")


class AppSettings(Base):
    __tablename__ = "settings"
    __table_args__ = (CheckConstraint("id = 1", name="settings_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    dias_prestamo_default: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    umbral_aviso_dias: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    umbral_urgente_dias: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    score_minimo_prestamo: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    bloquear_score_bajo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bloquear_vencidos: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    accion: Mapped[str] = mapped_column(Text, nullable=False)
    entidad: Mapped[str | None] = mapped_column(Text)
    entidad_id: Mapped[str | None] = mapped_column(Text)
    detalle: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
