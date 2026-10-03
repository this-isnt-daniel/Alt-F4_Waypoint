import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timezone
from app.main import app

# We use the test client and mock authentication
from app.models.user import User
from app.db.session import get_db

@pytest.fixture
def override_db():
    from sqlalchemy import create_engine, StaticPool
    from sqlalchemy.orm import sessionmaker
    from app.db.base import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    from app.core.security import get_password_hash
    from app.models.depot import Depot
    from app.models.vehicle import Vehicle
    from app.models.trip import Trip
    
    depots = [
        Depot(depot_id="DEP1", name="Test Depot 1", lat=0.0, lng=0.0),
        Depot(depot_id="DEP2", name="Test Depot 2", lat=0.0, lng=0.0)
    ]
    db.add_all(depots)
    
    vehicles = [
        Vehicle(vehicle_id="V1", depot_id="DEP1", type="truck", temp="ambient", vol_cap_m3=10.0, weight_cap_kg=1000.0, plate="TEST", status="available"),
        Vehicle(vehicle_id="V2", depot_id="DEP2", type="truck", temp="ambient", vol_cap_m3=10.0, weight_cap_kg=1000.0, plate="TEST2", status="available")
    ]
    db.add_all(vehicles)
    
    users = [
        User(user_id="U2", name="Dispatcher One", username="disp1", hashed_pw=get_password_hash("pass"), role="dispatcher", depot_id="DEP1"),
        User(user_id="U4", name="Driver One", username="driver1", hashed_pw=get_password_hash("pass"), role="driver")
    ]
    db.add_all(users)
    
    trips = [
        Trip(trip_id="TRIP1", depot_id="DEP1", vehicle_id="V1", dispatcher_id="U2", trip_date=date.today(), trip_no=1, status="planned"),
        Trip(trip_id="TRIP2", depot_id="DEP2", vehicle_id="V2", dispatcher_id="U2", trip_date=date.today(), trip_no=1, status="planned")
    ]
    db.add_all(trips)
    
    db.commit()
    
    def override_get_db():
        try:
            yield db
        finally:
            pass # Keep alive for tests
            
    app.dependency_overrides[get_db] = override_get_db
    yield db
    
    app.dependency_overrides.clear()
    db.close()

@pytest.fixture
def client(override_db):
    return TestClient(app)

@pytest.fixture
def disp_headers(client):
    res = client.post("/api/v1/auth/login", json={"username": "disp1", "password": "pass"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

@pytest.fixture
def driver_headers(client):
    res = client.post("/api/v1/auth/login", json={"username": "driver1", "password": "pass"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

def test_dispatcher_can_create_incident(client, disp_headers):
    res = client.post("/api/v1/dispatcher/incidents", headers=disp_headers, json={
        "vehicle_id": "V1",
        "type": "breakdown",
        "detail": "Engine failed"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["vehicle_id"] == "V1"
    assert data["type"] == "breakdown"
    assert data["detail"] == "Engine failed"
    assert data["reported_by"] == "U2"
    assert "reported_at" in data

def test_non_dispatcher_cannot_create_incident(client, driver_headers):
    res = client.post("/api/v1/dispatcher/incidents", headers=driver_headers, json={
        "vehicle_id": "V1",
        "type": "breakdown",
        "detail": "Engine failed"
    })
    assert res.status_code == 403

def test_unknown_vehicle_returns_404(client, disp_headers):
    res = client.post("/api/v1/dispatcher/incidents", headers=disp_headers, json={
        "vehicle_id": "UNKNOWN",
        "type": "breakdown",
        "detail": "Engine failed"
    })
    assert res.status_code == 404

def test_vehicle_outside_depot_forbidden(client, disp_headers):
    res = client.post("/api/v1/dispatcher/incidents", headers=disp_headers, json={
        "vehicle_id": "V2", # DEP2
        "type": "breakdown",
        "detail": "Engine failed"
    })
    assert res.status_code == 403

def test_incident_lists_and_detail(client, disp_headers):
    # Create incident
    res = client.post("/api/v1/dispatcher/incidents", headers=disp_headers, json={
        "vehicle_id": "V1",
        "type": "breakdown",
        "detail": "Flat tire"
    })
    inc_id = res.json()["incident_id"]
    
    # List incidents
    res = client.get("/api/v1/dispatcher/incidents", headers=disp_headers)
    assert res.status_code == 200
    incidents = res.json()
    assert len(incidents) > 0
    assert any(i["incident_id"] == inc_id for i in incidents)
    
    # Detail
    res = client.get(f"/api/v1/dispatcher/incidents/{inc_id}", headers=disp_headers)
    assert res.status_code == 200
    assert res.json()["incident_id"] == inc_id

def test_incident_filters(client, disp_headers):
    # Create incident
    client.post("/api/v1/dispatcher/incidents", headers=disp_headers, json={
        "vehicle_id": "V1",
        "type": "other",
        "detail": "Testing filters"
    })
    
    # Filter by vehicle
    res = client.get("/api/v1/dispatcher/incidents?vehicle_id=V1", headers=disp_headers)
    assert res.status_code == 200
    assert len(res.json()) > 0
    
    # Filter by type
    res = client.get("/api/v1/dispatcher/incidents?type=other", headers=disp_headers)
    assert len([i for i in res.json() if i["type"] == "other"]) > 0

def test_incident_resolution(client, disp_headers):
    res = client.post("/api/v1/dispatcher/incidents", headers=disp_headers, json={
        "vehicle_id": "V1",
        "type": "breakdown",
        "detail": "Needs resolving"
    })
    inc_id = res.json()["incident_id"]
    
    # Unresolved check
    res = client.get("/api/v1/dispatcher/incidents?unresolved_only=true", headers=disp_headers)
    assert any(i["incident_id"] == inc_id for i in res.json())
    
    # Resolve
    res = client.post(f"/api/v1/dispatcher/incidents/{inc_id}/resolve", headers=disp_headers, json={
        "resolution_note": "Fixed tire"
    })
    assert res.status_code == 200
    assert res.json()["resolved_at"] is not None
    assert "Fixed tire" in res.json()["detail"]
    
    # Already resolved
    res = client.post(f"/api/v1/dispatcher/incidents/{inc_id}/resolve", headers=disp_headers, json={})
    assert res.status_code == 409

# ROUTE CHANGES
def test_dispatcher_issue_route_change(client, disp_headers):
    res = client.post("/api/v1/dispatcher/trips/TRIP1/route-changes", headers=disp_headers, json={
        "change_type": "route.resequenced",
        "payload": {"new_sequence": ["S1", "S2"]}
    })
    assert res.status_code == 200
    data = res.json()
    assert data["change_type"] == "route.resequenced"
    assert data["acknowledged"] is False
    assert data["issued_by"] == "U2"
    assert "issued_at" in data

def test_unknown_trip_returns_404(client, disp_headers):
    res = client.post("/api/v1/dispatcher/trips/TRIP999/route-changes", headers=disp_headers, json={
        "change_type": "route.resequenced",
        "payload": {}
    })
    assert res.status_code == 404

def test_trip_outside_depot_forbidden(client, disp_headers):
    res = client.post("/api/v1/dispatcher/trips/TRIP2/route-changes", headers=disp_headers, json={
        "change_type": "route.resequenced",
        "payload": {}
    })
    assert res.status_code == 403

def test_non_dispatcher_cannot_issue_route_change(client, driver_headers):
    res = client.post("/api/v1/dispatcher/trips/TRIP1/route-changes", headers=driver_headers, json={
        "change_type": "route.resequenced",
        "payload": {}
    })
    assert res.status_code == 403

def test_route_change_retrieval_and_idempotency(client, disp_headers):
    # Same client_id should not duplicate
    res1 = client.post("/api/v1/dispatcher/trips/TRIP1/route-changes", headers=disp_headers, json={
        "change_id": "SAME_ID_123",
        "change_type": "route.resequenced",
        "payload": {}
    })
    res2 = client.post("/api/v1/dispatcher/trips/TRIP1/route-changes", headers=disp_headers, json={
        "change_id": "SAME_ID_123",
        "change_type": "route.resequenced",
        "payload": {}
    })
    assert res1.json()["change_id"] == res2.json()["change_id"]
    
    # Retrieve
    res = client.get("/api/v1/dispatcher/trips/TRIP1/route-changes", headers=disp_headers)
    assert res.status_code == 200
    changes = res.json()
    assert any(c["change_id"] == "SAME_ID_123" for c in changes)
