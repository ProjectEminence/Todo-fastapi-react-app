"""
CodeValid pytest conftest — prepends the installable package root to sys.path
(monorepo-safe via CODEVALID_PACKAGE_ROOT), and provides shared test fixtures.
"""
import functools
import os
import sys
from pathlib import Path

codevalid_dir = Path(__file__).resolve().parent
app_root = codevalid_dir.parent
rel = os.environ.get("CODEVALID_PACKAGE_ROOT", "").strip().lstrip("/")
package_root = app_root / rel if rel else app_root
pkg_str = str(package_root.resolve())
if pkg_str not in sys.path:
    sys.path.insert(0, pkg_str)

import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel
from sqlmodel.pool import StaticPool

from app.api.deps.user_deps import get_current_user
from app.core.config import settings
from app.core.security import get_password
from app.database import get_session
from app.main import app
from app.models.user_model import User


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@functools.lru_cache
def get_current_user_override():
    return User(
        username="currentuser",
        email="currentuser@gmail.com",
        firstName="Current",
        lastName="User",
        hashed_password=get_password("verylongpassword"),
    )


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_current_user] = get_current_user_override
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def prefix():
    return settings.API_V1_STR
