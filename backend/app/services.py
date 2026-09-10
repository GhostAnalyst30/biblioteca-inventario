from datetime import date, timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Alert, AppSettings, Book, Copy, Loan, LoanComment, Student


def get_or_create_settings(db: Session) -> AppSettings:
    settings = db.get(AppSettings, 1)
    if not settings:
        settings = AppSettings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def recalculate_reliability(db: Session, student: Student) -> int:
    loans = db.scalars(
        select(Loan).where(Loan.student_id == student.id, Loan.estado == "devuelto")
    ).all()
    if not loans:
        student.reliability_score = 100
        return 100
    on_time = sum(
        1
        for loan in loans
        if loan.fecha_devolucion_real and loan.fecha_devolucion_real <= loan.fecha_devolucion_esperada
    )
    score = round((on_time / len(loans)) * 100)
    student.reliability_score = score
    return score


def loan_dias_restantes(loan: Loan, today: date | None = None) -> int:
    today = today or date.today()
    if loan.estado == "devuelto" and loan.fecha_devolucion_real:
        return (loan.fecha_devolucion_esperada - loan.fecha_devolucion_real).days
    return (loan.fecha_devolucion_esperada - today).days


def serialize_loan(loan: Loan) -> dict:
    dias = loan_dias_restantes(loan)
    return {
        "id": loan.id,
        "student_id": loan.student_id,
        "copy_id": loan.copy_id,
        "fecha_prestamo": loan.fecha_prestamo,
        "fecha_devolucion_esperada": loan.fecha_devolucion_esperada,
        "fecha_devolucion_real": loan.fecha_devolucion_real,
        "estado": loan.estado,
        "student_nombre": loan.student.nombre if loan.student else None,
        "student_codigo": loan.student.codigo if loan.student else None,
        "student_grado": loan.student.grado if loan.student else None,
        "student_score": loan.student.reliability_score if loan.student else None,
        "book_titulo": loan.copy.book.titulo if loan.copy and loan.copy.book else None,
        "copy_etiqueta": loan.copy.etiqueta if loan.copy else None,
        "dias_restantes": dias,
        "comments": loan.comments or [],
    }


def serialize_book(book: Book) -> dict:
    copies = book.copies or []
    disponibles = sum(1 for c in copies if c.estado == "disponible")
    return {
        "id": book.id,
        "titulo": book.titulo,
        "autor": book.autor,
        "isbn": book.isbn,
        "categoria": book.categoria,
        "editorial": book.editorial,
        "anio": book.anio,
        "descripcion": book.descripcion,
        "active": book.active,
        "copies": [
            {
                "id": c.id,
                "book_id": c.book_id,
                "etiqueta": c.etiqueta,
                "estado": c.estado,
                "ubicacion": c.ubicacion,
                "notas": c.notas,
                "book_titulo": book.titulo,
                "book_autor": book.autor,
            }
            for c in copies
        ],
        "disponibles": disponibles,
        "total_copies": len(copies),
    }


def serialize_alert(alert: Alert) -> dict:
    loan = alert.loan
    return {
        "id": alert.id,
        "loan_id": alert.loan_id,
        "tipo": alert.tipo,
        "mensaje": alert.mensaje,
        "leida": alert.leida,
        "generada_en": alert.generada_en,
        "student_nombre": loan.student.nombre if loan and loan.student else None,
        "book_titulo": loan.copy.book.titulo if loan and loan.copy and loan.copy.book else None,
        "fecha_devolucion_esperada": loan.fecha_devolucion_esperada if loan else None,
    }


def mark_overdue_loans(db: Session) -> int:
    today = date.today()
    loans = db.scalars(
        select(Loan).where(Loan.estado == "activo", Loan.fecha_devolucion_esperada < today)
    ).all()
    for loan in loans:
        loan.estado = "vencido"
    db.commit()
    return len(loans)


def generate_alerts(db: Session) -> dict:
    settings = get_or_create_settings(db)
    mark_overdue_loans(db)
    today = date.today()
    created = {"aviso_proximo": 0, "urgente": 0, "vencido": 0}

    loans = db.scalars(
        select(Loan)
        .options(
            joinedload(Loan.student),
            joinedload(Loan.copy).joinedload(Copy.book),
        )
        .where(Loan.estado.in_(["activo", "vencido"]))
    ).unique().all()

    for loan in loans:
        days_left = (loan.fecha_devolucion_esperada - today).days
        book_title = loan.copy.book.titulo if loan.copy and loan.copy.book else "Libro"
        student_name = loan.student.nombre if loan.student else "Estudiante"

        def upsert(tipo: str, mensaje: str):
            existing = db.scalar(
                select(Alert).where(Alert.loan_id == loan.id, Alert.tipo == tipo)
            )
            if existing:
                existing.mensaje = mensaje
                if loan.estado != "devuelto":
                    existing.leida = False
            else:
                db.add(Alert(loan_id=loan.id, tipo=tipo, mensaje=mensaje))
                created[tipo] += 1

        if days_left < 0 or loan.estado == "vencido":
            upsert(
                "vencido",
                f"VENCIDO: {student_name} no ha devuelto «{book_title}» (vencía {loan.fecha_devolucion_esperada}).",
            )
        elif days_left <= settings.umbral_urgente_dias:
            upsert(
                "urgente",
                f"URGENTE: «{book_title}» de {student_name} vence en {days_left} día(s) ({loan.fecha_devolucion_esperada}).",
            )
        elif days_left <= settings.umbral_aviso_dias:
            upsert(
                "aviso_proximo",
                f"Aviso: «{book_title}» de {student_name} debe devolverse el {loan.fecha_devolucion_esperada} ({days_left} días).",
            )

    db.commit()
    return created


def eligibility_check(db: Session, student: Student, forzar: bool = False) -> tuple[bool, list[str]]:
    settings = get_or_create_settings(db)
    warnings: list[str] = []
    blocked = False

    overdue = db.scalar(
        select(func.count()).select_from(Loan).where(
            Loan.student_id == student.id, Loan.estado == "vencido"
        )
    ) or 0
    if overdue:
        msg = f"El estudiante tiene {overdue} préstamo(s) vencido(s)."
        warnings.append(msg)
        if settings.bloquear_vencidos and not forzar:
            blocked = True

    if student.reliability_score < settings.score_minimo_prestamo:
        msg = (
            f"Score de cumplimiento bajo ({student.reliability_score} < {settings.score_minimo_prestamo}). "
            "Históricamente no suele devolver a tiempo."
        )
        warnings.append(msg)
        if settings.bloquear_score_bajo and not forzar:
            blocked = True

    active = db.scalar(
        select(func.count()).select_from(Loan).where(
            Loan.student_id == student.id, Loan.estado.in_(["activo", "vencido"])
        )
    ) or 0
    if active >= 5:
        warnings.append("El estudiante ya tiene 5 o más préstamos activos.")
        if not forzar:
            blocked = True

    return (not blocked), warnings
