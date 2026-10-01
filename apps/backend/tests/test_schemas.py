import pytest
from pydantic import ValidationError
from datetime import date

from app.schemas.order import OrderItemRequest, CreateOrderRequest
from app.schemas.common import Brand, TempRequirement
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_valid_create_order_request():
    req = CreateOrderRequest(
        outlet_id="OUT001",
        brand=Brand.FRESH,
        order_type=TempRequirement.AMBIENT,
        order_date=date(2026, 10, 2),
        items=[OrderItemRequest(product_id="P001", quantity=10)]
    )
    assert req.outlet_id == "OUT001"
    assert req.items[0].quantity == 10

def test_quantity_zero_rejected():
    with pytest.raises(ValidationError):
        OrderItemRequest(product_id="P001", quantity=0)

def test_empty_items_list_rejected():
    with pytest.raises(ValidationError):
        CreateOrderRequest(
            outlet_id="OUT001",
            brand=Brand.FRESH,
            order_type=TempRequirement.AMBIENT,
            order_date=date(2026, 10, 2),
            items=[]
        )

def test_invalid_brand_rejected():
    with pytest.raises(ValidationError):
        CreateOrderRequest(
            outlet_id="OUT001",
            brand="invalid_brand",
            order_type=TempRequirement.AMBIENT,
            order_date=date(2026, 10, 2),
            items=[OrderItemRequest(product_id="P001", quantity=10)]
        )

def test_invalid_order_type_rejected():
    with pytest.raises(ValidationError):
        CreateOrderRequest(
            outlet_id="OUT001",
            brand=Brand.FRESH,
            order_type="invalid_type",
            order_date=date(2026, 10, 2),
            items=[OrderItemRequest(product_id="P001", quantity=10)]
        )

def test_missing_required_fields_rejected():
    with pytest.raises(ValidationError):
        CreateOrderRequest(
            brand=Brand.FRESH,
            order_type=TempRequirement.AMBIENT,
            order_date=date(2026, 10, 2),
            items=[OrderItemRequest(product_id="P001", quantity=10)]
        )

def test_demo_endpoint_valid_request():
    response = client.post("/api/v1/demo/orders", json={
      "outlet_id": "OUT001",
      "brand": "fresh",
      "order_type": "ambient",
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
      "order_type": "ambient",
      "order_date": "2026-10-02",
      "items": [
        {
          "product_id": "P001",
          "quantity": 0
        }
      ]
    })
    assert response.status_code == 422
