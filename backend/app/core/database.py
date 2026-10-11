from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from app.core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL, isolation_level="READ COMMITTED", pool_pre_ping=True
)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
