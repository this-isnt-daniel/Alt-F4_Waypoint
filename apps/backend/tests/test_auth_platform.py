import pytest
from fastapi.testclient import TestClient
from fastapi import APIRouter

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.core.security import get_password_hash
from app.api.deps import require_role

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.outlet import Outlet
from app.models.product import Product

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Seed fake user
    if not db.query(User).filter_by(username="manager1").first():
        db.add(User(
            user_id="U1", username="manager1", role="store_manager",
            outlet_id="OUT001", name="Manager One", hashed_pw=get_password_hash("password123")
        ))
        db.add(User(
            user_id="U2", username="disp1", role="dispatcher",
            depot_id="D1", name="Disp One", hashed_pw=get_password_hash("password123")
        ))
        
        # Need dummy outlet and product for duplicate order test
        db.add(Outlet(outlet_id="OUT001", name="Test", brand="fresh"))
        db.add(Product(product_id="P001", name="Test", brand="fresh", temp_req="ambient", unit="box"))
        
        db.commit()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_auth_db():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

test_router = APIRouter()
@test_router.get("/api/v1/test/store-manager-only", dependencies=[require_role("store_manager")])
def sm_only():
    return {"msg": "success"}

@test_router.get("/api/v1/test/raise-integrity")
def raise_integrity():
    from sqlalchemy.exc import IntegrityError
    raise IntegrityError("mock error", params=None, orig=None)

app.include_router(test_router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def use_auth_test_db():
    previous_get_db = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield
    finally:
        if previous_get_db is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_get_db

def test_login_success():
    res = client.post("/api/v1/auth/login", json={"username": "manager1", "password": "password123"})
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_login_wrong_password():
    res = client.post("/api/v1/auth/login", json={"username": "manager1", "password": "wrong"})
    assert res.status_code == 401

def test_login_unknown_user():
    res = client.post("/api/v1/auth/login", json={"username": "nobody", "password": "password123"})
    assert res.status_code == 401

def test_access_me_valid_jwt():
    res = client.post("/api/v1/auth/login", json={"username": "manager1", "password": "password123"})
    token = res.json()["access_token"]
    
    res2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    assert res2.json()["username"] == "manager1"

def test_access_invalid_jwt():
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer BAD_TOKEN"})
    assert res.status_code == 401

def test_access_missing_token():
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

def test_role_allowed():
    res = client.post("/api/v1/auth/login", json={"username": "manager1", "password": "password123"})
    token = res.json()["access_token"]
    
    res2 = client.get("/api/v1/test/store-manager-only", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200

def test_role_forbidden():
    res = client.post("/api/v1/auth/login", json={"username": "disp1", "password": "password123"})
    token = res.json()["access_token"]
    
    res2 = client.get("/api/v1/test/store-manager-only", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 403

def test_global_409_handler():
    # Hit the test endpoint that raises an IntegrityError
    res = client.get("/api/v1/test/raise-integrity")
    assert res.status_code == 409
