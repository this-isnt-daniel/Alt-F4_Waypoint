import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.models.depot import Depot
from app.models.outlet import Outlet
from app.models.product import Product
from app.models.order import Order, OrderLine

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    # Setup
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    # Teardown
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_insert_and_relationships(db):
    # 1. Insert Depot
    depot = Depot(depot_id="D1", name="Central Depot")
    db.add(depot)
    
    # 2. Insert Outlet
    outlet = Outlet(outlet_id="OUT1", name="Store 1", brand="fresh", depot_id="D1")
    db.add(outlet)
    
    # 3. Insert Product
    product = Product(product_id="P1", name="Apples", brand="fresh", temp_req="ambient", unit="box")
    db.add(product)
    
    db.commit()
    
    # 4. Create Order
    order = Order(
        order_id="ORD1",
        outlet_id="OUT1",
        created_by="U1",
        brand="fresh",
        temp_req="ambient",
        order_date=date(2026, 10, 2)
    )
    db.add(order)
    
    # 5. Create OrderLine
    line = OrderLine(
        line_item_id="LI1",
        order_id="ORD1",
        product_id="P1",
        quantity=10
    )
    db.add(line)
    db.commit()
    
    # Verify relations
    assert len(order.lines) == 1
    assert order.lines[0].product_id == "P1"
    
def test_unique_order_constraint(db):
    # Insert required foreign keys
    db.add(Outlet(outlet_id="OUT1", name="Store", brand="fresh"))
    db.commit()
    
    order1 = Order(
        order_id="ORD1",
        outlet_id="OUT1",
        created_by="U1",
        brand="fresh",
        temp_req="ambient",
        order_date=date(2026, 10, 2)
    )
    db.add(order1)
    db.commit()
    
    # Attempt duplicate for same outlet, date, and temp_req
    order2 = Order(
        order_id="ORD2",
        outlet_id="OUT1",
        created_by="U1",
        brand="fresh",
        temp_req="ambient",
        order_date=date(2026, 10, 2)
    )
    db.add(order2)
    
    with pytest.raises(IntegrityError):
        db.commit()
