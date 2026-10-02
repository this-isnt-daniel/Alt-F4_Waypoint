import pytest
from pydantic import ValidationError
from datetime import date
from fastapi.testclient import TestClient

from app.schemas.order import OrderLineRequest, CreateOrderRequest
from app.schemas.enums import Brand, TempReq
from app.main import app

# Database Override for Endpoint test
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.session import get_db
from app.models.outlet import Outlet
from app.models.product import Product

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    Base.metadata.create_all(bind=engine)
    try:
        db = TestingSessionLocal()
        # Setup fake FKs needed for sqlite test so insertion doesn't fail on foreign keys
        if not db.query(Outlet).filter_by(outlet_id="OUT001").first():
            db.add(Outlet(outlet_id="OUT001", name="Test", brand="fresh"))
            db.add(Product(product_id="P001", name="Test", brand="fresh", temp_req="ambient", unit="box"))
            db.commit()
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_schema_db():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

client = TestClient(app)

def test_valid_create_order_request():
    req = CreateOrderRequest(
        outlet_id="OUT001",
        brand=Brand.fresh,
        temp_req=TempReq.ambient,
        order_date=date(2026, 10, 2),
        items=[OrderLineRequest(product_id="P001", quantity=10)]
    )
    assert req.outlet_id == "OUT001"
    assert req.items[0].quantity == 10

def test_quantity_zero_rejected():
    with pytest.raises(ValidationError):
        OrderLineRequest(product_id="P001", quantity=0)

def test_empty_items_list_rejected():
    with pytest.raises(ValidationError):
        CreateOrderRequest(
            outlet_id="OUT001",
            brand=Brand.fresh,
            temp_req=TempReq.ambient,
            order_date=date(2026, 10, 2),
            items=[]
        )

def test_demo_endpoint_valid_request():
    response = client.post("/api/v1/demo/orders", json={
      "outlet_id": "OUT001",
      "brand": "fresh",
      "temp_req": "ambient",
      "order_date": "2026-10-02",
      "items": [
        {
          "product_id": "P001",
          "quantity": 10
        }
      ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["outlet_id"] == "OUT001"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 10

def test_demo_endpoint_invalid_quantity():
    response = client.post("/api/v1/demo/orders", json={
      "outlet_id": "OUT001",
      "brand": "fresh",
      "temp_req": "ambient",
      "order_date": "2026-10-02",
      "items": [
        {
          "product_id": "P001",
          "quantity": 0
        }
      ]
    })
    assert response.status_code == 422
