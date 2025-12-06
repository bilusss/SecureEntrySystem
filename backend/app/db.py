from collections.abc import Generator
from typing import Annotated
from app.models import Employee
from sqlmodel import SQLModel, create_engine, Session
from fastapi import Depends
from app import settings

engine = create_engine(settings.DATABASE_URL)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_db)]