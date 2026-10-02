"""
Seed data — canonical Day 5 delivery scenario.

Matches frontend's driverContent.ts exactly:
  - Driver: Daniru Dinsara, VEH014, Kandy hub
  - Trip 1: Fresh · Kandy · 8 stops · CHILLED REEFER
  - Trip 2: Style · Kandy · 5 stops · AMBIENT (locked)
  - OUT058 manifest flag (2 frozen damaged)
  - OUT052 outlet-closed scenario
  - OUT058 sync-conflict scenario

Run:  python -m app.seed
"""

import json
import uuid
from app.database import init_db, get_db_connection
from app.middleware.auth_middleware import hash_pin


def _id() -> str:
    return str(uuid.uuid4())


def seed_road_geometries(db):
    try:
        count = db.execute("SELECT COUNT(*) as c FROM road_geometry").fetchone()["c"]
    except Exception:
        count = 0
    if count > 0:
        return
    import os
    data_file = os.path.join(os.path.dirname(__file__), "data", "precomputed_road_geometries.json")
    if os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            geometries = json.load(f)
        for key, entry in geometries.items():
            db.execute(
                """INSERT OR REPLACE INTO road_geometry 
                   (from_id, to_id, coords, coord_version, distance_meters, duration_seconds)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    entry["from_id"],
                    entry["to_id"],
                    json.dumps(entry["coords"]),
                    entry.get("coord_version", 1),
                    entry.get("distance_meters"),
                    entry.get("duration_seconds"),
                ),
            )
        db.commit()
        print(f"  [OK] Seeded {len(geometries)} road geometries.")


def seed():
    init_db()
    db = get_db_connection()

    # Seed road geometry even if base tables already populated
    seed_road_geometries(db)

    # Check if already seeded
    row = db.execute("SELECT COUNT(*) as c FROM drivers").fetchone()
    if row["c"] > 0:
        db.close()
        print("Database already seeded. Drop waypoint_driver.db to re-seed.")
        return

    # ── Driver ───────────────────────────────────────────────────────
    driver_id = "DRV-DANIRU"
    db.execute(
        "INSERT INTO drivers (id, name, pin_hash, home_depot, phone_masked) VALUES (?, ?, ?, ?, ?)",
        (driver_id, "Daniru Dinsara", hash_pin("1234"), "Kandy hub", "+94 7• ••• ••01"),
    )

    # ── Device ───────────────────────────────────────────────────────
    db.execute(
        "INSERT INTO devices (id, label) VALUES (?, ?)",
        ("dev-001", "Driver tablet #1"),
    )

    # ── Trip 1: Fresh · Kandy · 8 stops ─────────────────────────────
    trip1_id = "TRIP-VEH014-2026-09-26-1"
    db.execute(
        """INSERT INTO trips (id, trip_no, driver_id, vehicle_id, brand, district, depot,
           status, stop_count, manifest_units, deliverable_units, return_units,
           weight_kg, volume_m3, depart_time, eta_return, capability, distance_km, drive_time)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (trip1_id, 1, driver_id, "VEH014", "Fresh", "Kandy", "Kandy hub",
         "planned", 8, 1240, 1238, 2,
         890, 4.2, "05:45", "09:30", "CHILLED_REEFER", 126, "3h 40m"),
    )

    # Trip 1 stops
    trip1_stops = [
        ("STOP-001", 1, "OUT042", "Waypoint Fresh Gampola", "Main Street, Gampola",
         7.1666, 80.5666, "05:30", "06:30", None, "street", "van_only", "chilled_ambient",
         120, 120, 0, None, "K. Bandara", "+94 7• ••• ••18", 16, None),
        ("STOP-002", 2, "OUT047", "Waypoint Fresh Kandy Town", "Dalada Veediya · beside Clock Tower, Kandy",
         7.2931, 80.6350, "05:45", "07:01", None, "rear_dock", "van_only", "chilled",
         25, 25, 0, None, "Joseph Vijay", "+94 7• ••• ••42", 15,
         "Use service lane. Ask for manager Joseph Vijay. Keep chilled crates sealed until handover."),
        ("STOP-003", 3, "OUT049", "Waypoint Fresh Kandy Fort", "Fort Road, Kandy",
         7.2936, 80.6360, "06:00", "07:30", None, "street", "normal", "ambient",
         18, 18, 0, None, "P. Jayasuriya", "+94 7• ••• ••21", 14, None),
        ("STOP-004", 4, "OUT052", "Waypoint Fresh Kandy City Centre", "Kandy City Centre, loading bay level",
         7.2941, 80.6380, "05:45", "07:30", "05:30-07:00", "mall_bay", "mall_dock", "chilled_ambient",
         160, 160, 0, None, "M. Fernando", "+94 7• ••• ••63", 18, None),
        ("STOP-005", 5, "OUT055", "Waypoint Fresh Kandy East", "Kandy East, Peradeniya Road",
         7.2880, 80.6200, "06:15", "07:45", None, "rear_dock", "normal", "ambient",
         8, 8, 0, None, "R. Gunawardena", "+94 7• ••• ••09", 12, None),
        ("STOP-006", 6, "OUT058", "Waypoint Fresh Kandy Hills", "Kandy Hills, Baddegama Road",
         7.2850, 80.6250, "06:45", "08:00", None, "rear_dock", "normal", "chilled",
         12, 10, 2, "R-04", "S. Silva", "+94 7• ••• ••77", 15,
         "Two frozen items are sealed in return crate R-04. Do not hand them over."),
        ("STOP-007", 7, "OUT061", "Waypoint Fresh Peradeniya", "Peradeniya, Kandy",
         7.2667, 80.6000, "06:45", "08:00", None, "rear_dock", "normal", "chilled_ambient",
         210, 210, 0, None, "D. Perera", "+94 7• ••• ••34", 17, None),
        ("STOP-008", 8, "OUT064", "Waypoint Fresh Nawalapitiya", "Nawalapitiya, Kandy district",
         7.0500, 80.5333, "07:00", "08:00", None, "street", "normal", "ambient",
         687, 687, 0, None, "T. Rosa", "+94 7• ••• ••55", 20, None),
    ]

    for s in trip1_stops:
        db.execute(
            """INSERT INTO stops (id, trip_id, seq, outlet_id, name, address,
               lat, lng, window_open, window_close, mall_window,
               dock_type, parking_constraint, temp_requirement,
               order_units, deliverable_units, return_units, return_crate,
               manager_name, manager_phone_masked, service_allowance_min, special_instructions)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (s[0], trip1_id, *s[1:]),
        )

    # Trip 1 manifest lines (including the flagged OUT058 line)
    manifest_lines_t1 = [
        (_id(), trip1_id, "STOP-006", "OUT058", "Frozen produce",
         12, 10, 2, "damaged_in_staging", "R-04",
         "S. Fernando", "2 damaged in staging. Sealed in return crate R-04.", 1),
    ]

    for ml in manifest_lines_t1:
        db.execute(
            """INSERT INTO manifest_lines (id, trip_id, stop_id, outlet_id, item_name,
               manifest_qty, deliverable_qty, return_qty, reason, return_crate,
               loader_id, loader_note, pre_flagged)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            ml,
        )

    # Trip 1 route legs
    legs_t1 = [
        (_id(), trip1_id, "DEPOT", "STOP-001", "OUT042", 18.4, 32),
        (_id(), trip1_id, "OUT042", "STOP-002", "OUT047", 22.1, 28),
        (_id(), trip1_id, "OUT047", "STOP-003", "OUT049", 1.2, 4),
        (_id(), trip1_id, "OUT049", "STOP-004", "OUT052", 0.8, 3),
        (_id(), trip1_id, "OUT052", "STOP-005", "OUT055", 3.1, 8),
        (_id(), trip1_id, "OUT055", "STOP-006", "OUT058", 2.4, 7),
        (_id(), trip1_id, "OUT058", "STOP-007", "OUT061", 5.6, 14),
        (_id(), trip1_id, "OUT061", "STOP-008", "OUT064", 28.3, 42),
        (_id(), trip1_id, "OUT064", None, None, 44.1, 55),  # return to depot
    ]

    for leg in legs_t1:
        db.execute(
            """INSERT INTO route_legs (id, trip_id, from_point, to_stop_id, to_outlet_id,
               distance_km, planned_travel_duration_min)
               VALUES (?,?,?,?,?,?,?)""",
            leg,
        )

    # ── Trip 2: Style · Kandy · 5 stops (locked) ────────────────────
    trip2_id = "TRIP-VEH014-2026-09-26-2"
    db.execute(
        """INSERT INTO trips (id, trip_no, driver_id, vehicle_id, brand, district, depot,
           status, stop_count, manifest_units, deliverable_units, return_units,
           weight_kg, volume_m3, depart_time, eta_return, capability, distance_km, drive_time)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (trip2_id, 2, driver_id, "VEH014", "Style", "Kandy", "Kandy hub",
         "locked", 5, 860, 860, 0,
         540, 2.8, "After Trip 1 + depot check", "14:22", "AMBIENT", 54, "1h 55m"),
    )

    trip2_stops = [
        ("STOP-T2-001", 1, "OUT070", "Waypoint Style Kandy City", "Kandy City Centre, Style unit",
         7.2941, 80.6380, "10:00", "12:00", "10:00-12:00", "mall_bay", "mall_dock", "ambient",
         220, 220, 0, None, "A. Silva", "+94 7• ••• ••80", 18, None),
        ("STOP-T2-002", 2, "OUT071", "Waypoint Style Gampola", "Main Street, Gampola",
         7.1666, 80.5666, "10:30", "12:30", None, "street", "normal", "ambient",
         160, 160, 0, None, "J. Fernando", "+94 7• ••• ••81", 15, None),
        ("STOP-T2-003", 3, "OUT072", "Waypoint Style Kandy Fort", "Fort Road, Kandy",
         7.2936, 80.6360, "11:00", "13:00", None, "rear_dock", "normal", "ambient",
         180, 180, 0, None, "K. Silva", "+94 7• ••• ••82", 16, None),
        ("STOP-T2-004", 4, "OUT073", "Waypoint Style Peradeniya", "Peradeniya, Kandy",
         7.2667, 80.6000, "11:30", "13:30", None, "street", "normal", "ambient",
         150, 150, 0, None, "L. Perera", "+94 7• ••• ••83", 14, None),
        ("STOP-T2-005", 5, "OUT074", "Waypoint Style Nawalapitiya", "Nawalapitiya, Kandy district",
         7.0500, 80.5333, "12:00", "14:00", None, "rear_dock", "normal", "ambient",
         150, 150, 0, None, "M. Rosa", "+94 7• ••• ••84", 14, None),
    ]

    for s in trip2_stops:
        db.execute(
            """INSERT INTO stops (id, trip_id, seq, outlet_id, name, address,
               lat, lng, window_open, window_close, mall_window,
               dock_type, parking_constraint, temp_requirement,
               order_units, deliverable_units, return_units, return_crate,
               manager_name, manager_phone_masked, service_allowance_min, special_instructions)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (s[0], trip2_id, *s[1:]),
        )

    # ── Pre-seed a route change for the resequencing scenario ────────
    route_change_payload = json.dumps({
        "headline": "OUT061 is now next",
        "body": "Dispatcher resequenced your remaining route to protect the delivery window. Your loaded goods and saved records are unchanged.",
        "changes": [
            {"type": "moved_next", "stop_id": "STOP-007", "outlet_id": "OUT061"},
            {"type": "moved_later", "stop_id": "STOP-004", "outlet_id": "OUT052"},
        ],
        "new_sequence": [
            "STOP-001", "STOP-002", "STOP-007", "STOP-003",
            "STOP-005", "STOP-004", "STOP-006", "STOP-008"
        ],
        "new_eta": "06:55",
    })

    db.execute(
        """INSERT INTO route_changes (id, trip_id, change_type, issued_at, payload)
           VALUES (?, ?, ?, ?, ?)""",
        ("CHG-001", trip1_id, "route.resequenced", "2026-09-26T06:41:00Z", route_change_payload),
    )

    # ── Pre-seed the sync-conflict scenario for OUT058 ───────────────
    conflict_driver_record = json.dumps({
        "stop_id": "STOP-006",
        "outlet_id": "OUT058",
        "arrived": "07:12",
        "items": "10 items handed over",
        "proof": "Photo · manager PIN",
    })
    conflict_system_record = json.dumps({
        "stop_id": "STOP-006",
        "assignment": "VEH021",
        "store_report": "not_received",
    })

    db.execute(
        """INSERT INTO conflicts (id, stop_id, driver_record_json, system_record_json, status)
           VALUES (?, ?, ?, ?, ?)""",
        ("CONF-001", "STOP-006", conflict_driver_record, conflict_system_record, "in_review"),
    )

    db.commit()
    db.close()
    print("[OK] Database seeded successfully.")
    print(f"  Driver: {driver_id} (PIN: 1234)")
    print(f"  Trip 1: {trip1_id} -- Fresh Kandy, 8 stops")
    print(f"  Trip 2: {trip2_id} -- Style Kandy, 5 stops (locked)")
    print(f"  Conflict: CONF-001 -- OUT058 sync mismatch")
    print(f"  Route change: CHG-001 -- resequencing")


if __name__ == "__main__":
    seed()
