from sqlmodel import Session, text


def verificar_conexion(session: Session) -> None:
    session.exec(text("SELECT 1"))
