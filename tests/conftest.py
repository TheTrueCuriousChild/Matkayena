"""Pytest configuration and fixtures for PS-02 microservices using fast in-memory SQLite."""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.services.shared.database import Base, get_db
from backend.services.shared.models import Profile, Role, UserRole, Customer, Product, CustomerProduct, Target
from backend.services.core_server.main import app as core_app
from backend.services.event_intelligence_server.main import app as event_app
from backend.services.action_commission_server.main import app as action_app
from backend.services.audit_blockchain_server.main import app as audit_app

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function", autouse=True)
def init_db_tables():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provides an isolated database session per test with seeded baseline products."""
    session = TestingSessionLocal()

    # Seed baseline products
    if not session.query(Product).first():
        products = [
            Product(id="prod_ins_1", code="TERM_LIFE", name="Term Life Insurance", category="INSURANCE", base_commission_rate=0.05),
            Product(id="prod_mf_1", code="BLUECHIP_MF", name="Bluechip Equity MF", category="MUTUAL_FUND", base_commission_rate=0.015),
            Product(id="prod_eq_1", code="EQUITY_PMS", name="Equity PMS", category="EQUITY", base_commission_rate=0.010),
        ]
        session.add_all(products)
        session.commit()

    yield session
    session.close()


@pytest.fixture
def core_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    core_app.dependency_overrides[get_db] = override_get_db
    with TestClient(core_app) as client:
        yield client
    core_app.dependency_overrides.clear()


@pytest.fixture
def event_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    event_app.dependency_overrides[get_db] = override_get_db
    with TestClient(event_app) as client:
        yield client
    event_app.dependency_overrides.clear()


@pytest.fixture
def action_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    action_app.dependency_overrides[get_db] = override_get_db
    with TestClient(action_app) as client:
        yield client
    action_app.dependency_overrides.clear()


@pytest.fixture
def audit_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    audit_app.dependency_overrides[get_db] = override_get_db
    with TestClient(audit_app) as client:
        yield client
    audit_app.dependency_overrides.clear()
