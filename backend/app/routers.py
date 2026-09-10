from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.auth import (
    AdminUser,
    CurrentUser,
    StaffUser,
    create_access_token,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.database import get_db
from app.models import Alert, AppSettings, AuditLog, Book, Copy, Loan, LoanComment, Student, User
from app.schemas import (
    AlertOut,
    AnalyticsOut,
    BookCreate,
    BookOut,
    BookUpdate,
    CopyCreate,
    CopyOut,
    CopyUpdate,
    DashboardOut,
    LoanCreate,
    LoanOut,
    LoanReturn,
    LoginIn,
    SettingsOut,
    SettingsUpdate,
    StudentCreate,
    StudentOut,
    StudentUpdate,
    TokenOut,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.services import (
    eligibility_check,
    generate_alerts,
    get_or_create_settings,
    recalculate_reliability,
    serialize_alert,
    serialize_book,
    serialize_loan,
)

router = APIRouter(prefix="/api")


def audit(db: Session, user: User | None, accion: str, entidad: str | None = None, entidad_id: str | None = None, detalle: dict | None = None):
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            detalle=detalle,
        )
    )


# -------- Auth --------
@router.post("/auth/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash) or not user.active:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_access_token(str(user.id), user.role)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/auth/token", response_model=TokenOut, include_in_schema=False)
def login_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return login(LoginIn(email=form.username, password=form.password), db)


@router.get("/auth/me", response_model=UserOut)
def me(user: CurrentUser):
    return user


# -------- Users (admin) --------
@router.get("/users", response_model=list[UserOut])
def list_users(_: AdminUser, db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.created_at.desc())).all()


@router.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, admin: AdminUser, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(400, "El email ya está registrado")
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    audit(db, admin, "crear_usuario", "users", detalle={"email": user.email, "role": user.role})
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: UUID, payload: UserUpdate, admin: AdminUser, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        user.password_hash = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(user, k, v)
    audit(db, admin, "actualizar_usuario", "users", str(user.id))
    db.commit()
    db.refresh(user)
    return user


# -------- Students --------
@router.get("/students", response_model=list[StudentOut])
def list_students(
    _: StaffUser,
    q: Optional[str] = None,
    grado: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(Student).where(Student.active.is_(True))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Student.nombre.ilike(like), Student.codigo.ilike(like)))
    if grado:
        stmt = stmt.where(Student.grado == grado)
    return db.scalars(stmt.order_by(Student.nombre)).all()


@router.post("/students", response_model=StudentOut)
def create_student(payload: StudentCreate, user: StaffUser, db: Session = Depends(get_db)):
    if db.scalar(select(Student).where(Student.codigo == payload.codigo)):
        raise HTTPException(400, "Ya existe un estudiante con ese código")
    student = Student(**payload.model_dump())
    db.add(student)
    audit(db, user, "crear_estudiante", "students", detalle={"codigo": student.codigo})
    db.commit()
    db.refresh(student)
    return student


@router.get("/students/{student_id}", response_model=StudentOut)
def get_student(student_id: UUID, _: StaffUser, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(404, "Estudiante no encontrado")
    return student


@router.patch("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: UUID, payload: StudentUpdate, user: StaffUser, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(404, "Estudiante no encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(student, k, v)
    audit(db, user, "actualizar_estudiante", "students", str(student.id))
    db.commit()
    db.refresh(student)
    return student


@router.get("/students/{student_id}/loans", response_model=list[LoanOut])
def student_loans(student_id: UUID, _: StaffUser, db: Session = Depends(get_db)):
    loans = db.scalars(
        select(Loan)
        .options(
            joinedload(Loan.student),
            joinedload(Loan.copy).joinedload(Copy.book),
            joinedload(Loan.comments),
        )
        .where(Loan.student_id == student_id)
        .order_by(Loan.created_at.desc())
    ).unique().all()
    return [serialize_loan(l) for l in loans]


@router.get("/students/{student_id}/eligibility")
def student_eligibility(student_id: UUID, _: StaffUser, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(404, "Estudiante no encontrado")
    ok, warnings = eligibility_check(db, student)
    return {
        "eligible": ok,
        "warnings": warnings,
        "reliability_score": student.reliability_score,
        "prediccion": (
            "Alta probabilidad de devolver a tiempo"
            if student.reliability_score >= 80
            else "Riesgo medio de retraso"
            if student.reliability_score >= 50
            else "Alta probabilidad de NO devolver a tiempo"
        ),
    }


# -------- Books & copies --------
@router.get("/books", response_model=list[BookOut])
def list_books(
    _: StaffUser,
    q: Optional[str] = None,
    categoria: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(Book).options(joinedload(Book.copies)).where(Book.active.is_(True))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Book.titulo.ilike(like), Book.autor.ilike(like), Book.isbn.ilike(like)))
    if categoria:
        stmt = stmt.where(Book.categoria == categoria)
    books = db.scalars(stmt.order_by(Book.titulo)).unique().all()
    return [serialize_book(b) for b in books]


@router.post("/books", response_model=BookOut)
def create_book(payload: BookCreate, user: StaffUser, db: Session = Depends(get_db)):
    book = Book(**payload.model_dump())
    db.add(book)
    audit(db, user, "crear_libro", "books", detalle={"titulo": book.titulo})
    db.commit()
    db.refresh(book)
    book = db.scalar(select(Book).options(joinedload(Book.copies)).where(Book.id == book.id))
    return serialize_book(book)


@router.patch("/books/{book_id}", response_model=BookOut)
def update_book(book_id: UUID, payload: BookUpdate, user: StaffUser, db: Session = Depends(get_db)):
    book = db.scalar(select(Book).options(joinedload(Book.copies)).where(Book.id == book_id))
    if not book:
        raise HTTPException(404, "Libro no encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(book, k, v)
    audit(db, user, "actualizar_libro", "books", str(book.id))
    db.commit()
    db.refresh(book)
    return serialize_book(book)


@router.delete("/books/{book_id}")
def delete_book(book_id: UUID, user: StaffUser, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(404, "Libro no encontrado")
    book.active = False
    for copy in db.scalars(select(Copy).where(Copy.book_id == book_id)).all():
        if copy.estado == "disponible":
            copy.estado = "baja"
    audit(db, user, "eliminar_libro", "books", str(book.id))
    db.commit()
    return {"ok": True}


@router.post("/books/{book_id}/copies", response_model=CopyOut)
def add_copy(book_id: UUID, payload: CopyCreate, user: StaffUser, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(404, "Libro no encontrado")
    if db.scalar(select(Copy).where(Copy.etiqueta == payload.etiqueta)):
        raise HTTPException(400, "Ya existe un ejemplar con esa etiqueta")
    copy = Copy(book_id=book_id, **payload.model_dump())
    db.add(copy)
    audit(db, user, "crear_ejemplar", "copies", detalle={"etiqueta": copy.etiqueta})
    db.commit()
    db.refresh(copy)
    return {
        "id": copy.id,
        "book_id": copy.book_id,
        "etiqueta": copy.etiqueta,
        "estado": copy.estado,
        "ubicacion": copy.ubicacion,
        "notas": copy.notas,
        "book_titulo": book.titulo,
        "book_autor": book.autor,
    }


@router.patch("/copies/{copy_id}", response_model=CopyOut)
def update_copy(copy_id: UUID, payload: CopyUpdate, user: StaffUser, db: Session = Depends(get_db)):
    copy = db.scalar(select(Copy).options(joinedload(Copy.book)).where(Copy.id == copy_id))
    if not copy:
        raise HTTPException(404, "Ejemplar no encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(copy, k, v)
    audit(db, user, "actualizar_ejemplar", "copies", str(copy.id))
    db.commit()
    db.refresh(copy)
    return {
        "id": copy.id,
        "book_id": copy.book_id,
        "etiqueta": copy.etiqueta,
        "estado": copy.estado,
        "ubicacion": copy.ubicacion,
        "notas": copy.notas,
        "book_titulo": copy.book.titulo if copy.book else None,
        "book_autor": copy.book.autor if copy.book else None,
    }


@router.get("/copies", response_model=list[CopyOut])
def list_copies(
    _: StaffUser,
    estado: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(Copy).options(joinedload(Copy.book))
    if estado:
        stmt = stmt.where(Copy.estado == estado)
    if q:
        like = f"%{q}%"
        stmt = stmt.join(Book).where(or_(Copy.etiqueta.ilike(like), Book.titulo.ilike(like)))
    copies = db.scalars(stmt.order_by(Copy.etiqueta)).unique().all()
    return [
        {
            "id": c.id,
            "book_id": c.book_id,
            "etiqueta": c.etiqueta,
            "estado": c.estado,
            "ubicacion": c.ubicacion,
            "notas": c.notas,
            "book_titulo": c.book.titulo if c.book else None,
            "book_autor": c.book.autor if c.book else None,
        }
        for c in copies
    ]


# -------- Loans --------
@router.get("/loans", response_model=list[LoanOut])
def list_loans(
    _: StaffUser,
    estado: Optional[str] = None,
    grado: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = (
        select(Loan)
        .options(
            joinedload(Loan.student),
            joinedload(Loan.copy).joinedload(Copy.book),
            joinedload(Loan.comments),
        )
        .order_by(Loan.fecha_devolucion_esperada)
    )
    if estado:
        stmt = stmt.where(Loan.estado == estado)
    if grado:
        stmt = stmt.join(Student).where(Student.grado == grado)
    if q:
        like = f"%{q}%"
        stmt = stmt.join(Student, isouter=True).join(Copy, isouter=True).join(Book, isouter=True).where(
            or_(Student.nombre.ilike(like), Student.codigo.ilike(like), Book.titulo.ilike(like), Copy.etiqueta.ilike(like))
        )
    loans = db.scalars(stmt).unique().all()
    return [serialize_loan(l) for l in loans]


@router.post("/loans", response_model=LoanOut)
def create_loan(payload: LoanCreate, user: StaffUser, db: Session = Depends(get_db)):
    student = db.get(Student, payload.student_id)
    copy = db.scalar(select(Copy).options(joinedload(Copy.book)).where(Copy.id == payload.copy_id))
    if not student or not student.active:
        raise HTTPException(404, "Estudiante no encontrado")
    if not copy:
        raise HTTPException(404, "Ejemplar no encontrado")
    if copy.estado != "disponible":
        raise HTTPException(400, f"El ejemplar no está disponible (estado: {copy.estado})")

    ok, warnings = eligibility_check(db, student, forzar=payload.forzar)
    if not ok:
        raise HTTPException(400, detail={"message": "Préstamo bloqueado por política", "warnings": warnings})

    settings = get_or_create_settings(db)
    due = payload.fecha_devolucion_esperada
    if not due:
        days = payload.dias_prestamo or settings.dias_prestamo_default
        due = date.today() + timedelta(days=days)

    loan = Loan(
        student_id=student.id,
        copy_id=copy.id,
        prestado_por=user.id,
        fecha_prestamo=date.today(),
        fecha_devolucion_esperada=due,
        estado="activo",
    )
    copy.estado = "prestado"
    db.add(loan)
    db.flush()
    db.add(
        LoanComment(
            loan_id=loan.id,
            tipo="entrega",
            condicion=payload.condicion_entrega,
            comentario=payload.comentario_entrega,
            created_by=user.id,
        )
    )
    audit(db, user, "crear_prestamo", "loans", detalle={"warnings": warnings})
    db.commit()
    loan = db.scalar(
        select(Loan)
        .options(
            joinedload(Loan.student),
            joinedload(Loan.copy).joinedload(Copy.book),
            joinedload(Loan.comments),
        )
        .where(Loan.id == loan.id)
    )
    result = serialize_loan(loan)
    result["warnings"] = warnings  # type: ignore
    return result


@router.post("/loans/{loan_id}/return", response_model=LoanOut)
def return_loan(loan_id: UUID, payload: LoanReturn, user: StaffUser, db: Session = Depends(get_db)):
    loan = db.scalar(
        select(Loan)
        .options(
            joinedload(Loan.student),
            joinedload(Loan.copy).joinedload(Copy.book),
            joinedload(Loan.comments),
        )
        .where(Loan.id == loan_id)
    )
    if not loan:
        raise HTTPException(404, "Préstamo no encontrado")
    if loan.estado == "devuelto":
        raise HTTPException(400, "Este préstamo ya fue devuelto")

    loan.fecha_devolucion_real = payload.fecha_devolucion_real or date.today()
    loan.estado = "devuelto"
    if loan.copy:
        new_estado = "reparacion" if payload.condicion_devolucion == "danado" else "disponible"
        loan.copy.estado = new_estado
    db.add(
        LoanComment(
            loan_id=loan.id,
            tipo="devolucion",
            condicion=payload.condicion_devolucion,
            comentario=payload.comentario_devolucion,
            created_by=user.id,
        )
    )
    if loan.student:
        recalculate_reliability(db, loan.student)
    # mark related alerts read
    for alert in db.scalars(select(Alert).where(Alert.loan_id == loan.id)).all():
        alert.leida = True
    audit(db, user, "devolver_prestamo", "loans", str(loan.id))
    db.commit()
    db.refresh(loan)
    return serialize_loan(loan)


# -------- Alerts --------
@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    _: StaffUser,
    solo_no_leidas: bool = False,
    db: Session = Depends(get_db),
):
    generate_alerts(db)
    stmt = (
        select(Alert)
        .options(
            joinedload(Alert.loan).joinedload(Loan.student),
            joinedload(Alert.loan).joinedload(Loan.copy).joinedload(Copy.book),
        )
        .order_by(Alert.generada_en.desc())
    )
    if solo_no_leidas:
        stmt = stmt.where(Alert.leida.is_(False))
    alerts = db.scalars(stmt).unique().all()
    return [serialize_alert(a) for a in alerts]


@router.post("/alerts/{alert_id}/read")
def mark_alert_read(alert_id: UUID, _: StaffUser, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alerta no encontrada")
    alert.leida = True
    db.commit()
    return {"ok": True}


@router.post("/alerts/read-all")
def mark_all_alerts_read(_: StaffUser, db: Session = Depends(get_db)):
    alerts = db.scalars(select(Alert).where(Alert.leida.is_(False))).all()
    for a in alerts:
        a.leida = True
    db.commit()
    return {"ok": True, "count": len(alerts)}


@router.post("/jobs/generate-alerts")
def job_generate_alerts(secret: str = Query(...), db: Session = Depends(get_db)):
    settings = get_settings()
    if secret != settings.alert_cron_secret:
        raise HTTPException(403, "Secret inválido")
    created = generate_alerts(db)
    return {"ok": True, "created": created}


# -------- Dashboard / Analytics / Settings --------
@router.get("/dashboard", response_model=DashboardOut)
def dashboard(_: StaffUser, db: Session = Depends(get_db)):
    generate_alerts(db)
    return DashboardOut(
        libros=db.scalar(select(func.count()).select_from(Book).where(Book.active.is_(True))) or 0,
        ejemplares_disponibles=db.scalar(select(func.count()).select_from(Copy).where(Copy.estado == "disponible")) or 0,
        prestamos_activos=db.scalar(select(func.count()).select_from(Loan).where(Loan.estado == "activo")) or 0,
        prestamos_vencidos=db.scalar(select(func.count()).select_from(Loan).where(Loan.estado == "vencido")) or 0,
        alertas_sin_leer=db.scalar(select(func.count()).select_from(Alert).where(Alert.leida.is_(False))) or 0,
        estudiantes=db.scalar(select(func.count()).select_from(Student).where(Student.active.is_(True))) or 0,
        score_promedio=float(db.scalar(select(func.avg(Student.reliability_score)).where(Student.active.is_(True))) or 100),
    )


@router.get("/analytics", response_model=AnalyticsOut)
def analytics(
    _: StaffUser,
    grado: Optional[str] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    db: Session = Depends(get_db),
):
    loan_filters = []
    if desde:
        loan_filters.append(Loan.fecha_prestamo >= desde)
    if hasta:
        loan_filters.append(Loan.fecha_prestamo <= hasta)
    if grado:
        loan_filters.append(Student.grado == grado)

    por_grado_rows = db.execute(
        select(Student.grado, func.count(Loan.id))
        .join(Loan, Loan.student_id == Student.id)
        .where(*loan_filters if loan_filters else [True])
        .group_by(Student.grado)
        .order_by(func.count(Loan.id).desc())
    ).all()

    por_categoria_rows = db.execute(
        select(Book.categoria, func.count(Loan.id))
        .select_from(Loan)
        .join(Copy, Copy.id == Loan.copy_id)
        .join(Book, Book.id == Copy.book_id)
        .join(Student, Student.id == Loan.student_id)
        .where(*loan_filters if loan_filters else [True])
        .group_by(Book.categoria)
        .order_by(func.count(Loan.id).desc())
    ).all()

    top_libros_rows = db.execute(
        select(Book.titulo, Book.autor, func.count(Loan.id).label("total"))
        .select_from(Loan)
        .join(Copy, Copy.id == Loan.copy_id)
        .join(Book, Book.id == Copy.book_id)
        .join(Student, Student.id == Loan.student_id)
        .where(*loan_filters if loan_filters else [True])
        .group_by(Book.id)
        .order_by(func.count(Loan.id).desc())
        .limit(10)
    ).all()

    returned = db.scalars(
        select(Loan)
        .join(Student)
        .where(Loan.estado == "devuelto", *(loan_filters if loan_filters else [True]))
    ).all()
    on_time = sum(
        1
        for l in returned
        if l.fecha_devolucion_real and l.fecha_devolucion_real <= l.fecha_devolucion_esperada
    )
    total_ret = len(returned)
    cumplimiento = {
        "devueltos": total_ret,
        "a_tiempo": on_time,
        "tarde": total_ret - on_time,
        "tasa_cumplimiento": round((on_time / total_ret) * 100, 1) if total_ret else 100.0,
        "activos": db.scalar(
            select(func.count()).select_from(Loan).join(Student).where(
                Loan.estado.in_(["activo", "vencido"]), *(loan_filters if loan_filters else [True])
            )
        )
        or 0,
    }

    return AnalyticsOut(
        por_grado=[{"grado": g or "Sin grado", "prestamos": c} for g, c in por_grado_rows],
        por_categoria=[{"categoria": c or "Sin categoría", "prestamos": n} for c, n in por_categoria_rows],
        top_libros=[{"titulo": t, "autor": a, "prestamos": n} for t, a, n in top_libros_rows],
        cumplimiento=cumplimiento,
        filtros={"grado": grado, "desde": str(desde) if desde else None, "hasta": str(hasta) if hasta else None},
    )


@router.get("/analytics/export")
def analytics_export(
    _: StaffUser,
    grado: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = (
        select(Loan, Student, Book, Copy)
        .join(Student, Student.id == Loan.student_id)
        .join(Copy, Copy.id == Loan.copy_id)
        .join(Book, Book.id == Copy.book_id)
        .order_by(Loan.fecha_prestamo.desc())
    )
    if grado:
        stmt = stmt.where(Student.grado == grado)
    rows = db.execute(stmt).all()
    lines = ["codigo_estudiante,nombre,grado,libro,etiqueta,fecha_prestamo,fecha_esperada,fecha_real,estado,score"]
    for loan, student, book, copy in rows:
        lines.append(
            ",".join(
                [
                    student.codigo,
                    f'"{student.nombre}"',
                    student.grado,
                    f'"{book.titulo}"',
                    copy.etiqueta,
                    str(loan.fecha_prestamo),
                    str(loan.fecha_devolucion_esperada),
                    str(loan.fecha_devolucion_real or ""),
                    loan.estado,
                    str(student.reliability_score),
                ]
            )
        )
    csv_data = "\n".join(lines)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=prestamos.csv"},
    )


@router.get("/settings", response_model=SettingsOut)
def get_settings_endpoint(_: StaffUser, db: Session = Depends(get_db)):
    return get_or_create_settings(db)


@router.put("/settings", response_model=SettingsOut)
def update_settings(payload: SettingsUpdate, admin: AdminUser, db: Session = Depends(get_db)):
    settings = get_or_create_settings(db)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(settings, k, v)
    audit(db, admin, "actualizar_settings", "settings", "1")
    db.commit()
    db.refresh(settings)
    return settings
