from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


Role = Literal["admin", "bibliotecario"]
CopyEstado = Literal["disponible", "prestado", "reparacion", "baja"]
LoanEstado = Literal["activo", "devuelto", "vencido"]
Condicion = Literal["bueno", "regular", "danado"]
AlertTipo = Literal["aviso_proximo", "urgente", "vencido"]


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: Role
    active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=6)
    role: Role = "bibliotecario"


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6)
    active: Optional[bool] = None
    role: Optional[Role] = None


class StudentCreate(BaseModel):
    codigo: str
    nombre: str
    grado: str
    seccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None


class StudentUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    grado: Optional[str] = None
    seccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    active: Optional[bool] = None


class StudentOut(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    grado: str
    seccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    reliability_score: int
    active: bool

    model_config = {"from_attributes": True}


class BookCreate(BaseModel):
    titulo: str
    autor: str
    isbn: Optional[str] = None
    categoria: Optional[str] = None
    editorial: Optional[str] = None
    anio: Optional[int] = None
    descripcion: Optional[str] = None


class BookUpdate(BaseModel):
    titulo: Optional[str] = None
    autor: Optional[str] = None
    isbn: Optional[str] = None
    categoria: Optional[str] = None
    editorial: Optional[str] = None
    anio: Optional[int] = None
    descripcion: Optional[str] = None
    active: Optional[bool] = None


class CopyCreate(BaseModel):
    etiqueta: str
    ubicacion: Optional[str] = None
    notas: Optional[str] = None
    estado: CopyEstado = "disponible"


class CopyUpdate(BaseModel):
    etiqueta: Optional[str] = None
    ubicacion: Optional[str] = None
    notas: Optional[str] = None
    estado: Optional[CopyEstado] = None


class CopyOut(BaseModel):
    id: UUID
    book_id: UUID
    etiqueta: str
    estado: CopyEstado
    ubicacion: Optional[str] = None
    notas: Optional[str] = None
    book_titulo: Optional[str] = None
    book_autor: Optional[str] = None

    model_config = {"from_attributes": True}


class BookOut(BaseModel):
    id: UUID
    titulo: str
    autor: str
    isbn: Optional[str] = None
    categoria: Optional[str] = None
    editorial: Optional[str] = None
    anio: Optional[int] = None
    descripcion: Optional[str] = None
    active: bool
    copies: list[CopyOut] = []
    disponibles: int = 0
    total_copies: int = 0

    model_config = {"from_attributes": True}


class LoanCommentIn(BaseModel):
    condicion: Condicion
    comentario: Optional[str] = None


class LoanCommentOut(BaseModel):
    id: UUID
    tipo: str
    condicion: Condicion
    comentario: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LoanCreate(BaseModel):
    student_id: UUID
    copy_id: UUID
    fecha_devolucion_esperada: Optional[date] = None
    dias_prestamo: Optional[int] = None
    condicion_entrega: Condicion = "bueno"
    comentario_entrega: Optional[str] = None
    forzar: bool = False


class LoanReturn(BaseModel):
    condicion_devolucion: Condicion = "bueno"
    comentario_devolucion: Optional[str] = None
    fecha_devolucion_real: Optional[date] = None


class LoanOut(BaseModel):
    id: UUID
    student_id: UUID
    copy_id: UUID
    fecha_prestamo: date
    fecha_devolucion_esperada: date
    fecha_devolucion_real: Optional[date] = None
    estado: LoanEstado
    student_nombre: Optional[str] = None
    student_codigo: Optional[str] = None
    student_grado: Optional[str] = None
    student_score: Optional[int] = None
    book_titulo: Optional[str] = None
    copy_etiqueta: Optional[str] = None
    dias_restantes: Optional[int] = None
    comments: list[LoanCommentOut] = []
    score_antes: Optional[int] = None
    score_despues: Optional[int] = None
    warnings: list[str] = []

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    id: UUID
    loan_id: UUID
    tipo: AlertTipo
    mensaje: str
    leida: bool
    generada_en: datetime
    student_nombre: Optional[str] = None
    book_titulo: Optional[str] = None
    fecha_devolucion_esperada: Optional[date] = None

    model_config = {"from_attributes": True}


class SettingsOut(BaseModel):
    dias_prestamo_default: int
    umbral_aviso_dias: int
    umbral_urgente_dias: int
    score_minimo_prestamo: int
    bloquear_score_bajo: bool
    bloquear_vencidos: bool

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    dias_prestamo_default: Optional[int] = None
    umbral_aviso_dias: Optional[int] = None
    umbral_urgente_dias: Optional[int] = None
    score_minimo_prestamo: Optional[int] = None
    bloquear_score_bajo: Optional[bool] = None
    bloquear_vencidos: Optional[bool] = None


class DashboardOut(BaseModel):
    libros: int
    ejemplares_disponibles: int
    prestamos_activos: int
    prestamos_vencidos: int
    alertas_sin_leer: int
    estudiantes: int
    score_promedio: float


class AnalyticsOut(BaseModel):
    por_grado: list[dict]
    por_categoria: list[dict]
    top_libros: list[dict]
    cumplimiento: dict
    filtros: dict
