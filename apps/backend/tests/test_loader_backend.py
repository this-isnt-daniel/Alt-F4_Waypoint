from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import (
    DeliveryEvent,
    Depot,
    Discrepancy,
    LoadCheck,
    Order,
    OrderLine,
    Outlet,
    Product,
    Trip,
    TripStop,
    User,
    Vehicle,
)
from app.schemas.loader import LoadCheckItemInput, SaveLoadItemRequest, SubmitLoadCheckRequest
from app.schemas.dispatcher import DeferOrderRequest
from app.schemas.driver import DepartTripRequest
from app.services import delivery_service, loader_service, planning_service


ALLOWED_STATUSES = {
    "trip": {"planned", "loading", "loaded", "out_for_delivery", "cancelled", "vehicle_unavailable"},
    "stop": {"upcoming", "loading_complete", "loaded", "delivered"},
    "order": {"draft", "confirmed", "planned", "loading", "loaded", "out_for_delivery", "deferred", "delivered"},
    "order_line": {"manifested"},
    "vehicle": {"available", "unavailable"},
    "loader": {"active", "wrong_role", "wrong_depot"},
    "depot": {"own_depot", "other_depot"},
    "discrepancy": {"open", "resolved"},
}


class LoaderFixture:
    def __init__(self, db):
        self.db = db
        self.counter = 0

    def seed_reference_data(self):
        self.db.add_all(
            [
                Depot(depot_id="DEP1", name="Depot 1", lat=0, lng=0),
                Depot(depot_id="DEP2", name="Depot 2", lat=0, lng=0),
                Outlet(outlet_id="OUT1", name="Outlet 1", brand="fresh", depot_id="DEP1"),
                Outlet(outlet_id="OUT2", name="Outlet 2", brand="fresh", depot_id="DEP1"),
                Outlet(outlet_id="OUT3", name="Outlet 3", brand="fresh", depot_id="DEP2"),
                Vehicle(
                    vehicle_id="V_AMB",
                    depot_id="DEP1",
                    type="truck",
                    temp="ambient",
                    weight_cap_kg=1000,
                    vol_cap_m3=100,
                    plate="AMB-1",
                    status="available",
                ),
                Vehicle(
                    vehicle_id="V_COLD",
                    depot_id="DEP1",
                    type="truck",
                    temp="reefer",
                    weight_cap_kg=1000,
                    vol_cap_m3=100,
                    plate="COLD-1",
                    status="available",
                ),
                Vehicle(
                    vehicle_id="V_OTHER",
                    depot_id="DEP2",
                    type="truck",
                    temp="ambient",
                    weight_cap_kg=1000,
                    vol_cap_m3=100,
                    plate="OTHER-1",
                    status="available",
                ),
                Product(product_id="P_AMB", name="Ambient item", brand="fresh", temp_req="ambient", unit="EA"),
                Product(product_id="P_DUP", name="Duplicate product", brand="fresh", temp_req="ambient", unit="EA"),
                Product(product_id="P_COLD", name="Cold item", brand="fresh", temp_req="reefer", unit="EA"),
            ]
        )
        self.db.add_all(
            [
                User(
                    user_id="U_MANAGER",
                    username="manager1",
                    name="Manager",
                    role="store_manager",
                    outlet_id="OUT1",
                    hashed_pw=get_password_hash("pass"),
                ),
                User(
                    user_id="U_DISPATCHER",
                    username="dispatcher1",
                    name="Dispatcher",
                    role="dispatcher",
                    depot_id="DEP1",
                    hashed_pw=get_password_hash("pass"),
                ),
                User(
                    user_id="U_LOADER",
                    username="loader1",
                    name="Loader",
                    role="loader",
                    depot_id="DEP1",
                    hashed_pw=get_password_hash("pass"),
                ),
                User(
                    user_id="U_LOADER_OTHER",
                    username="loader2",
                    name="Other Loader",
                    role="loader",
                    depot_id="DEP2",
                    hashed_pw=get_password_hash("pass"),
                ),
                User(
                    user_id="U_DRIVER",
                    username="driver1",
                    name="Driver",
                    role="driver",
                    hashed_pw=get_password_hash("pass"),
                ),
            ]
        )
        self.db.commit()

    def make_trip(
        self,
        *,
        status="planned",
        depot_id="DEP1",
        vehicle_id="V_AMB",
        stop_count=1,
        product_ids=None,
        quantities=None,
        duplicate_product_within_order=False,
        empty_stop=False,
        order_status="planned",
    ):
        self.counter += 1
        product_ids = product_ids or ["P_AMB"]
        quantities = quantities or [5] * len(product_ids)
        trip = Trip(
            trip_id=f"TRIP-{self.counter}",
            depot_id=depot_id,
            vehicle_id=vehicle_id,
            dispatcher_id="U_DISPATCHER",
            trip_date=date.today() + timedelta(days=self.counter),
            trip_no=self.counter,
            status=status,
        )
        self.db.add(trip)

        stops = []
        lines = []
        if stop_count == 0:
            self.db.commit()
            return trip, stops, lines

        for index in range(stop_count):
            outlet_id = "OUT1" if index % 2 == 0 else "OUT2"
            order = Order(
                order_id=f"ORD-{self.counter}-{index}",
                outlet_id=outlet_id,
                created_by="U_MANAGER",
                brand="fresh",
                temp_req="ambient",
                order_date=date.today() + timedelta(days=self.counter + index),
                status=order_status,
                trip_id=trip.trip_id,
                stop_seq=index + 1,
                order_units=0,
            )
            self.db.add(order)
            stop = TripStop(
                stop_id=f"STOP-{self.counter}-{index}",
                trip_id=trip.trip_id,
                outlet_id=outlet_id,
                order_id=order.order_id,
                stop_seq=index + 1,
                temp_req="ambient",
                status="upcoming",
            )
            self.db.add(stop)
            stops.append(stop)

            if empty_stop:
                continue

            line_products = product_ids if duplicate_product_within_order or index == 0 else [product_ids[0]]
            for line_index, product_id in enumerate(line_products):
                quantity = quantities[line_index if line_index < len(quantities) else 0]
                line = OrderLine(
                    line_item_id=f"LINE-{self.counter}-{index}-{line_index}",
                    order_id=order.order_id,
                    product_id=product_id,
                    quantity=quantity,
                )
                self.db.add(line)
                lines.append(line)
                order.order_units = (order.order_units or 0) + quantity

        self.db.commit()
        return trip, stops, lines


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    fixture = LoaderFixture(db)
    fixture.seed_reference_data()
    try:
        yield db, fixture
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def api_client(db_session):
    db, _ = db_session
    previous_get_db = app.dependency_overrides.get(get_db)
    previous_current_user = app.dependency_overrides.get(get_current_user)

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        yield client
    finally:
        if previous_get_db is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_get_db
        if previous_current_user is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous_current_user


def auth_headers(client, username):
    response = client.post("/api/v1/auth/login", json={"username": username, "password": "pass"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def load_payload(lines, *, client_op_id="load-1", status="verified", loaded_qty=None, reason=None):
    items = []
    for line in lines:
        qty = line.quantity if loaded_qty is None else loaded_qty
        item = {"line_item_id": line.line_item_id, "loaded_qty": qty, "status": status}
        if reason:
            item["discrepancy_reason"] = reason
        items.append(item)
    return {"client_op_id": client_op_id, "items": items}


def assert_http(status_code, func, *args, **kwargs):
    with pytest.raises(HTTPException) as exc:
        func(*args, **kwargs)
    assert exc.value.status_code == status_code
    return exc.value.detail


def test_entity_status_map_is_explicit_documentation():
    assert "loaded" in ALLOWED_STATUSES["trip"]
    assert "deferred" in ALLOWED_STATUSES["order"]
    assert "open" in ALLOWED_STATUSES["discrepancy"]


def test_queue_filtering_and_workbench_shape(db_session):
    db, fx = db_session
    planned, _, planned_lines = fx.make_trip(status="planned")
    loaded, _, _ = fx.make_trip(status="loaded")
    fx.make_trip(status="cancelled")
    queue = loader_service.get_loader_queue(db, "DEP1")

    ids = {row.trip_id for row in queue}
    assert planned.trip_id in ids
    assert loaded.trip_id in ids
    assert all(row.status != "cancelled" for row in queue)

    workbench = loader_service.get_workbench(db, planned.trip_id, "DEP1")
    assert workbench.trip_id == planned.trip_id
    assert workbench.stops[0].items[0].line_item_id == planned_lines[0].line_item_id
    assert workbench.total_items == 1


def test_trip_not_found_and_wrong_depot(db_session):
    db, fx = db_session
    trip, _, _ = fx.make_trip()

    assert_http(404, loader_service.get_workbench, db, "NO-TRIP", "DEP1")
    assert_http(403, loader_service.get_workbench, db, trip.trip_id, "DEP2")


@pytest.mark.parametrize("status", ["loaded", "out_for_delivery", "cancelled", "vehicle_unavailable"])
def test_read_only_trip_statuses_reject_loader_edits(db_session, status):
    db, fx = db_session
    trip, _, lines = fx.make_trip(status=status)
    request = SubmitLoadCheckRequest(**load_payload(lines))

    assert_http(400, loader_service.submit_load_check, db, trip.trip_id, request, "DEP1", "U_LOADER")


def test_empty_trip_and_stop_without_items_rejected(db_session):
    db, fx = db_session
    empty_trip, _, _ = fx.make_trip(stop_count=0)
    stop_without_items, _, _ = fx.make_trip(empty_stop=True)

    assert_http(400, loader_service.start_loading, db, empty_trip.trip_id, "DEP1", "U_LOADER")
    assert_http(400, loader_service.start_loading, db, stop_without_items.trip_id, "DEP1", "U_LOADER")


def test_duplicate_product_across_stops_uses_line_item_identity(db_session):
    db, fx = db_session
    trip, _, lines = fx.make_trip(stop_count=2, product_ids=["P_DUP"])
    request = SubmitLoadCheckRequest(**load_payload(lines))

    check = loader_service.submit_load_check(db, trip.trip_id, request, "DEP1", "U_LOADER")

    stored_lines = db.query(LoadCheck).filter(LoadCheck.check_id == check.check_id).one()
    assert stored_lines.status == "completed"
    assert db.query(Discrepancy).count() == 0


def test_duplicate_product_within_same_order_is_safe(db_session):
    db, fx = db_session
    trip, _, lines = fx.make_trip(
        product_ids=["P_DUP", "P_DUP"],
        quantities=[2, 3],
        duplicate_product_within_order=True,
    )

    loader_service.submit_load_check(
        db,
        trip.trip_id,
        SubmitLoadCheckRequest(**load_payload(lines)),
        "DEP1",
        "U_LOADER",
    )

    workbench = loader_service.get_workbench(db, trip.trip_id, "DEP1")
    assert sorted(item.assigned_qty for item in workbench.stops[0].items) == [2, 3]


def test_submitted_item_not_part_of_trip_and_missing_item(db_session):
    db, fx = db_session
    trip, _, lines = fx.make_trip(product_ids=["P_AMB", "P_DUP"], quantities=[2, 3], duplicate_product_within_order=True)

    extra_payload = load_payload(lines)
    extra_payload["items"].append({"line_item_id": "LINE-NOT-IN-TRIP", "loaded_qty": 1, "status": "verified"})
    assert_http(400, loader_service.submit_load_check, db, trip.trip_id, SubmitLoadCheckRequest(**extra_payload), "DEP1", "U_LOADER")

    missing_payload = load_payload(lines[:1])
    assert_http(400, loader_service.submit_load_check, db, trip.trip_id, SubmitLoadCheckRequest(**missing_payload), "DEP1", "U_LOADER")


def test_expected_quantity_from_client_is_rejected_as_stale_manifest_data():
    with pytest.raises(ValidationError):
        LoadCheckItemInput(line_item_id="L1", expected_qty=99, loaded_qty=1, status="verified")


def test_negative_zero_over_short_damaged_and_reason_rules(db_session):
    db, fx = db_session
    trip, _, lines = fx.make_trip()
    line_id = lines[0].line_item_id

    with pytest.raises(ValidationError):
        SaveLoadItemRequest(loaded_qty=-1, status="short", discrepancy_reason="short")

    over = loader_service.save_load_item(
        db,
        trip.trip_id,
        line_id,
        SaveLoadItemRequest(loaded_qty=9, status="over", discrepancy_reason="over count"),
        "DEP1",
        "U_LOADER",
    )
    assert over.status == "over"
    assert_http(
        400,
        loader_service.save_load_item,
        db,
        trip.trip_id,
        line_id,
        SaveLoadItemRequest(loaded_qty=0, status="verified"),
        "DEP1",
        "U_LOADER",
    )
    assert_http(
        400,
        loader_service.save_load_item,
        db,
        trip.trip_id,
        line_id,
        SaveLoadItemRequest(loaded_qty=4, status="short"),
        "DEP1",
        "U_LOADER",
    )
    assert_http(
        400,
        loader_service.save_load_item,
        db,
        trip.trip_id,
        line_id,
        SaveLoadItemRequest(loaded_qty=5, status="verified", discrepancy_reason="should not be here"),
        "DEP1",
        "U_LOADER",
    )

    damaged = loader_service.save_load_item(
        db,
        trip.trip_id,
        line_id,
        SaveLoadItemRequest(loaded_qty=5, status="damaged", discrepancy_reason="box crushed"),
        "DEP1",
        "U_LOADER",
    )
    assert damaged.status == "damaged"
    assert db.query(Discrepancy).filter(Discrepancy.type == "damaged").count() == 1


def test_discrepancy_creation_for_shortage_and_idempotent_final_submit(db_session):
    db, fx = db_session
    trip, _, lines = fx.make_trip()
    payload = load_payload(lines, loaded_qty=3, status="short", reason="inventory shortage")
    request = SubmitLoadCheckRequest(**payload)

    first = loader_service.submit_load_check(db, trip.trip_id, request, "DEP1", "U_LOADER")
    second = loader_service.submit_load_check(db, trip.trip_id, request, "DEP1", "U_LOADER")

    assert first.check_id == second.check_id
    assert db.query(Discrepancy).filter(Discrepancy.status == "open").count() == 1
    assert db.query(DeliveryEvent).filter(DeliveryEvent.event_type == "order_loaded").count() == 1


def test_partial_save_then_final_submit(db_session):
    db, fx = db_session
    trip, _, lines = fx.make_trip(product_ids=["P_AMB", "P_DUP"], quantities=[2, 3], duplicate_product_within_order=True)

    loader_service.save_load_item(
        db,
        trip.trip_id,
        lines[0].line_item_id,
        SaveLoadItemRequest(client_op_id="save-1", loaded_qty=2, status="verified"),
        "DEP1",
        "U_LOADER",
    )
    check = loader_service.submit_load_check(
        db,
        trip.trip_id,
        SubmitLoadCheckRequest(**load_payload(lines, client_op_id="final-1")),
        "DEP1",
        "U_LOADER",
    )

    assert check.status == "completed"
    assert db.query(Trip).filter(Trip.trip_id == trip.trip_id).one().status == "loaded"


def test_final_submit_with_pending_item_is_rejected(db_session):
    db, fx = db_session
    trip, _, lines = fx.make_trip()
    payload = load_payload(lines)
    payload["items"][0]["status"] = "pending"

    assert_http(400, loader_service.submit_load_check, db, trip.trip_id, SubmitLoadCheckRequest(**payload), "DEP1", "U_LOADER")


def test_temperature_sensitive_item_rejected_on_ambient_vehicle(db_session):
    db, fx = db_session
    trip, _, lines = fx.make_trip(product_ids=["P_COLD"], vehicle_id="V_AMB")

    assert_http(
        400,
        loader_service.submit_load_check,
        db,
        trip.trip_id,
        SubmitLoadCheckRequest(**load_payload(lines)),
        "DEP1",
        "U_LOADER",
    )


def test_dispatcher_defers_order_while_loader_screen_is_open(db_session):
    db, fx = db_session
    trip, stops, lines = fx.make_trip()

    planning_service.defer_order(
        db,
        DeferOrderRequest(
            client_op_id="defer-1",
            order_id=stops[0].order_id,
            outlet_id=stops[0].outlet_id,
            original_date=date.today(),
            new_date=date.today() + timedelta(days=1),
            reason="customer closed",
        ),
        "DEP1",
        "U_DISPATCHER",
    )

    assert_http(
        409,
        loader_service.submit_load_check,
        db,
        trip.trip_id,
        SubmitLoadCheckRequest(**load_payload(lines)),
        "DEP1",
        "U_LOADER",
    )


def test_vehicle_unavailable_before_and_after_loading(db_session):
    db, fx = db_session
    trip, _, _ = fx.make_trip(status="loading")

    result = loader_service.mark_vehicle_unavailable(
        db,
        trip.trip_id,
        request=loader_service.VehicleUnavailableRequest(client_op_id="veh-1", reason="breakdown"),
        loader_depot="DEP1",
        user_id="U_LOADER",
    )
    assert result.status == "vehicle_unavailable"
    assert db.query(Vehicle).filter(Vehicle.vehicle_id == "V_AMB").one().status == "unavailable"

    loaded_trip, _, lines = fx.make_trip(status="planned", vehicle_id="V_COLD")
    loader_service.submit_load_check(db, loaded_trip.trip_id, SubmitLoadCheckRequest(**load_payload(lines)), "DEP1", "U_LOADER")
    assert_http(
        400,
        loader_service.mark_vehicle_unavailable,
        db,
        loaded_trip.trip_id,
        loader_service.VehicleUnavailableRequest(client_op_id="veh-2", reason="too late"),
        "DEP1",
        "U_LOADER",
    )


def test_driver_departure_before_and_after_loader_completion(db_session):
    db, fx = db_session
    trip, _, lines = fx.make_trip()

    assert_http(
        400,
        delivery_service.depart_trip,
        db,
        trip.trip_id,
        DepartTripRequest(client_op_id="depart-1", departed_at=datetime.now(timezone.utc)),
        "U_DRIVER",
    )

    loader_service.submit_load_check(
        db,
        trip.trip_id,
        SubmitLoadCheckRequest(**load_payload(lines, loaded_qty=3, status="short", reason="inventory shortage")),
        "DEP1",
        "U_LOADER",
    )
    result = delivery_service.depart_trip(
        db,
        trip.trip_id,
        DepartTripRequest(client_op_id="depart-2", departed_at=datetime.now(timezone.utc)),
        "U_DRIVER",
    )
    assert result.status == "out_for_delivery"


def test_api_role_wrong_depot_and_duplicate_client_op_id(api_client, db_session):
    db, fx = db_session
    trip, _, lines = fx.make_trip()
    loader_headers = auth_headers(api_client, "loader1")
    other_loader_headers = auth_headers(api_client, "loader2")
    dispatcher_headers = auth_headers(api_client, "dispatcher1")

    response = api_client.get("/api/v1/loader/queue", headers=dispatcher_headers)
    assert response.status_code == 403

    response = api_client.get(f"/api/v1/loader/trips/{trip.trip_id}/workbench", headers=other_loader_headers)
    assert response.status_code == 403

    payload = load_payload(lines, client_op_id="api-load-1")
    first = api_client.post(f"/api/v1/loader/trips/{trip.trip_id}/load", headers=loader_headers, json=payload)
    second = api_client.post(f"/api/v1/loader/trips/{trip.trip_id}/load", headers=loader_headers, json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert db.query(LoadCheck).filter(LoadCheck.client_op_id == "api-load-1").count() == 1


def test_full_platform_flow_store_manager_dispatcher_loader_driver(api_client, db_session):
    db, _ = db_session
    sm_headers = auth_headers(api_client, "manager1")
    dispatcher_headers = auth_headers(api_client, "dispatcher1")
    loader_headers = auth_headers(api_client, "loader1")
    driver_headers = auth_headers(api_client, "driver1")

    create = api_client.post(
        "/api/v1/store-manager/orders",
        headers=sm_headers,
        json={
            "outlet_id": "OUT1",
            "brand": "fresh",
            "temp_req": "ambient",
            "order_date": str(date.today() + timedelta(days=90)),
            "items": [{"product_id": "P_AMB", "quantity": 4}],
        },
    )
    assert create.status_code == 200
    order_id = create.json()["order_id"]
    assert api_client.post(f"/api/v1/store-manager/orders/{order_id}/confirm", headers=sm_headers).status_code == 200

    optimize = api_client.post(
        "/api/v1/dispatcher/planning/optimize",
        headers=dispatcher_headers,
        json={"depot_id": "DEP1", "target_date": str(date.today() + timedelta(days=90))},
    )
    assert optimize.status_code == 200
    run_id = optimize.json()["run_id"]
    planning_service._mock_planning_runs[run_id].trips = [
        type(
            "ProposedTripObject",
            (object,),
            {
                "vehicle_id": "V_COLD",
                "brand": "fresh",
                "temp_type": "ambient",
                "stops": [
                    type(
                        "ProposedStopObject",
                        (object,),
                        {"order_id": order_id, "sequence": 1, "expected_arrival": "10:00"},
                    )
                ],
            },
        )
    ]
    confirm = api_client.post(
        f"/api/v1/dispatcher/planning/runs/{run_id}/confirm",
        headers=dispatcher_headers,
        json={"client_op_id": "plan-flow-1"},
    )
    assert confirm.status_code == 200

    order = db.query(Order).filter(Order.order_id == order_id).one()
    trip_id = order.trip_id
    workbench = api_client.get(f"/api/v1/loader/trips/{trip_id}/workbench", headers=loader_headers)
    assert workbench.status_code == 200
    line_id = workbench.json()["stops"][0]["items"][0]["line_item_id"]

    before_depart = api_client.post(
        f"/api/v1/driver-platform/trips/{trip_id}/depart",
        headers=driver_headers,
        json={"client_op_id": "depart-too-early", "departed_at": datetime.now(timezone.utc).isoformat()},
    )
    assert before_depart.status_code == 400

    load = api_client.post(
        f"/api/v1/loader/trips/{trip_id}/load",
        headers=loader_headers,
        json={
            "client_op_id": "flow-load-1",
            "items": [{"line_item_id": line_id, "loaded_qty": 4, "status": "verified"}],
        },
    )
    assert load.status_code == 200

    depart = api_client.post(
        f"/api/v1/driver-platform/trips/{trip_id}/depart",
        headers=driver_headers,
        json={"client_op_id": "depart-flow-1", "departed_at": datetime.now(timezone.utc).isoformat()},
    )
    assert depart.status_code == 200
    assert db.query(DeliveryEvent).filter(DeliveryEvent.event_type == "order_loaded").count() == 1
