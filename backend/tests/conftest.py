from sqlmodel import SQLModel, Session, create_engine, StaticPool
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_db
from app.models import User
from app.users import current_user


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture()
def client(session):
    # Override dependency
    def get_session_override():
        yield session

    app.dependency_overrides[get_db] = get_session_override

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def override_auth():
    user = User(
        id="00000000-0000-0000-0000-000000000001",
        email="test@example.com",
        hashed_password="fakehashed",
        is_active=True,
        is_superuser=True,
    )

    app.dependency_overrides[current_user] = lambda: user
    yield
    app.dependency_overrides.pop(current_user, None)
