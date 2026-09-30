"""
SQLite database setup — all tables, WAL mode, get_db() helper.

Every table defined here matches the spec in docs/driver-backend-design.md.
"""

import sqlite3
from contextlib import contextmanager
from app.config import DATABASE_PATH

# ── Connection factory ───────────────────────────────────────────────────

def _make_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


_conn: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    """Return a module-level connection (re-used across requests)."""
    global _conn
    if _conn is None:
        _conn = _make_connection()
    return _conn


@contextmanager
def get_db_tx():
    """Context manager that yields a connection and commits on success."""
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


# ── Schema creation ──────────────────────────────────────────────────────

def init_db():
    """Create all tables if they don't exist."""
    db = get_db()

    db.executescript("""

    -- ═══════════════════════════════════════════════════════════════════
    -- Module A: Driver auth + device session
    -- ═══════════════════════════════════════════════════════════════════

    CREATE TABLE IF NOT EXISTS drivers (
        id              TEXT PRIMARY KEY,
        name            TEXT NOT NULL,
        pin_hash        TEXT NOT NULL,
        home_depot      TEXT NOT NULL,
        phone_masked    TEXT,
        active          INTEGER NOT NULL DEFAULT 1,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS devices (
        id              TEXT PRIMARY KEY,
        label           TEXT,
        registered_at   TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS driver_sessions (
        id                  TEXT PRIMARY KEY,
        driver_id           TEXT NOT NULL REFERENCES drivers(id),
        device_id           TEXT NOT NULL,
        access_token_hash   TEXT NOT NULL,
        refresh_token_hash  TEXT NOT NULL,
        expires_at          TEXT NOT NULL,
        created_at          TEXT NOT NULL DEFAULT (datetime('now')),
        revoked             INTEGER NOT NULL DEFAULT 0
    );

    -- ═══════════════════════════════════════════════════════════════════
    -- Module B: Trips / route snapshot
    -- ═══════════════════════════════════════════════════════════════════

    CREATE TABLE IF NOT EXISTS trips (
        id              TEXT PRIMARY KEY,
        trip_no         INTEGER NOT NULL,
        driver_id       TEXT NOT NULL REFERENCES drivers(id),
        vehicle_id      TEXT NOT NULL,
        brand           TEXT NOT NULL,
        district        TEXT NOT NULL,
        depot           TEXT NOT NULL,
        status          TEXT NOT NULL DEFAULT 'planned',
        stop_count      INTEGER NOT NULL DEFAULT 0,
        manifest_units  INTEGER NOT NULL DEFAULT 0,
        deliverable_units INTEGER NOT NULL DEFAULT 0,
        return_units    INTEGER NOT NULL DEFAULT 0,
        weight_kg       REAL,
        volume_m3       REAL,
        depart_time     TEXT,
        eta_return      TEXT,
        capability      TEXT,
        distance_km     REAL,
        drive_time      TEXT,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS stops (
        id                  TEXT PRIMARY KEY,
        trip_id             TEXT NOT NULL REFERENCES trips(id),
        seq                 INTEGER NOT NULL,
        outlet_id           TEXT NOT NULL,
        name                TEXT NOT NULL,
        address             TEXT,
        lat                 REAL,
        lng                 REAL,
        window_open         TEXT,
        window_close        TEXT,
        mall_window         TEXT,
        dock_type           TEXT,
        parking_constraint  TEXT,
        temp_requirement    TEXT,
        order_units         INTEGER NOT NULL DEFAULT 0,
        deliverable_units   INTEGER NOT NULL DEFAULT 0,
        return_units        INTEGER NOT NULL DEFAULT 0,
        return_crate        TEXT,
        manager_name        TEXT,
        manager_phone_masked TEXT,
        service_allowance_min INTEGER,
        special_instructions TEXT,
        status              TEXT NOT NULL DEFAULT 'upcoming',
        row_version         INTEGER NOT NULL DEFAULT 1,
        created_at          TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS manifest_lines (
        id              TEXT PRIMARY KEY,
        trip_id         TEXT NOT NULL REFERENCES trips(id),
        stop_id         TEXT NOT NULL REFERENCES stops(id),
        outlet_id       TEXT NOT NULL,
        item_name       TEXT NOT NULL,
        manifest_qty    INTEGER NOT NULL DEFAULT 0,
        deliverable_qty INTEGER NOT NULL DEFAULT 0,
        return_qty      INTEGER NOT NULL DEFAULT 0,
        reason          TEXT,
        return_crate    TEXT,
        loader_id       TEXT,
        loader_note     TEXT,
        pre_flagged     INTEGER NOT NULL DEFAULT 0,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS route_legs (
        id                      TEXT PRIMARY KEY,
        trip_id                 TEXT NOT NULL REFERENCES trips(id),
        from_point              TEXT NOT NULL,
        to_stop_id              TEXT,
        to_outlet_id            TEXT,
        distance_km             REAL,
        planned_travel_duration_min INTEGER,
        created_at              TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- ═══════════════════════════════════════════════════════════════════
    -- Core: Append-only event ledger
    -- ═══════════════════════════════════════════════════════════════════

    CREATE TABLE IF NOT EXISTS driver_events (
        id                  TEXT PRIMARY KEY,
        driver_id           TEXT NOT NULL REFERENCES drivers(id),
        device_id           TEXT,
        client_event_id     TEXT NOT NULL UNIQUE,
        kind                TEXT NOT NULL,
        stop_id             TEXT,
        trip_id             TEXT,
        payload             TEXT,
        occurred_at         TEXT,
        received_at         TEXT NOT NULL DEFAULT (datetime('now')),
        applied_at          TEXT,
        status              TEXT NOT NULL DEFAULT 'pending',
        row_version_before  INTEGER,
        row_version_after   INTEGER,
        error               TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_driver_events_client_id
        ON driver_events(client_event_id);

    CREATE INDEX IF NOT EXISTS idx_driver_events_driver
        ON driver_events(driver_id, received_at);

    CREATE INDEX IF NOT EXISTS idx_driver_events_kind
        ON driver_events(kind);

    -- ═══════════════════════════════════════════════════════════════════
    -- Module D: Stop lifecycle evidence
    -- ═══════════════════════════════════════════════════════════════════

    CREATE TABLE IF NOT EXISTS evidence_objects (
        id              TEXT PRIMARY KEY,
        stop_id         TEXT NOT NULL REFERENCES stops(id),
        kind            TEXT NOT NULL,
        object_key      TEXT,
        mime_type       TEXT,
        size_bytes      INTEGER,
        captured_at     TEXT,
        uploaded_at     TEXT,
        checksum        TEXT,
        status          TEXT NOT NULL DEFAULT 'pending_upload',
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS checklist_results (
        id              TEXT PRIMARY KEY,
        stop_id         TEXT NOT NULL REFERENCES stops(id),
        event_id        TEXT REFERENCES driver_events(id),
        line_id         TEXT NOT NULL,
        state           TEXT NOT NULL,
        reason          TEXT,
        quantity_flagged INTEGER,
        return_crate    TEXT,
        version         INTEGER NOT NULL DEFAULT 1,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS pod_records (
        id                  TEXT PRIMARY KEY,
        stop_id             TEXT NOT NULL REFERENCES stops(id),
        photo_evidence_id   TEXT REFERENCES evidence_objects(id),
        pin_state           TEXT NOT NULL DEFAULT 'not_started',
        pin_verified        INTEGER NOT NULL DEFAULT 0,
        pin_submitted_at    TEXT,
        pin_verified_at     TEXT,
        attempt_count       INTEGER NOT NULL DEFAULT 0,
        created_at          TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS return_custody (
        id                  TEXT PRIMARY KEY,
        stop_id             TEXT NOT NULL REFERENCES stops(id),
        trip_id             TEXT NOT NULL REFERENCES trips(id),
        items               TEXT,
        return_crate        TEXT,
        destination_depot   TEXT,
        handover_location   TEXT,
        status              TEXT NOT NULL DEFAULT 'pending',
        confirmed_at        TEXT,
        officer_name        TEXT,
        officer_pin_state   TEXT,
        condition           TEXT,
        created_at          TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- ═══════════════════════════════════════════════════════════════════
    -- Module E: Conflicts
    -- ═══════════════════════════════════════════════════════════════════

    CREATE TABLE IF NOT EXISTS conflicts (
        id                  TEXT PRIMARY KEY,
        stop_id             TEXT REFERENCES stops(id),
        driver_event_id     TEXT REFERENCES driver_events(id),
        driver_record_json  TEXT,
        system_record_json  TEXT,
        status              TEXT NOT NULL DEFAULT 'in_review',
        created_at          TEXT NOT NULL DEFAULT (datetime('now')),
        forwarded_at        TEXT,
        resolved_at         TEXT,
        resolved_by_role    TEXT,
        resolution_note     TEXT
    );

    -- ═══════════════════════════════════════════════════════════════════
    -- Module F: Route changes (dispatcher → driver)
    -- ═══════════════════════════════════════════════════════════════════

    CREATE TABLE IF NOT EXISTS route_changes (
        id              TEXT PRIMARY KEY,
        trip_id         TEXT NOT NULL REFERENCES trips(id),
        change_type     TEXT NOT NULL,
        issued_at       TEXT NOT NULL DEFAULT (datetime('now')),
        payload         TEXT NOT NULL,
        acknowledged    INTEGER NOT NULL DEFAULT 0,
        ack_at          TEXT,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- ═══════════════════════════════════════════════════════════════════
    -- Module G: Chat / Call
    -- ═══════════════════════════════════════════════════════════════════

    CREATE TABLE IF NOT EXISTS messages (
        id              TEXT PRIMARY KEY,
        stop_id         TEXT REFERENCES stops(id),
        sender_role     TEXT NOT NULL,
        sender_id       TEXT NOT NULL,
        body            TEXT NOT NULL,
        quick_reply     INTEGER NOT NULL DEFAULT 0,
        client_event_id TEXT UNIQUE,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS call_sessions (
        id              TEXT PRIMARY KEY,
        stop_id         TEXT REFERENCES stops(id),
        requested_by    TEXT NOT NULL,
        masked_dial_number TEXT,
        expires_at      TEXT,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- ═══════════════════════════════════════════════════════════════════
    -- Audit log
    -- ═══════════════════════════════════════════════════════════════════

    CREATE TABLE IF NOT EXISTS audit_log (
        id              TEXT PRIMARY KEY,
        actor_role      TEXT,
        actor_id        TEXT,
        action          TEXT NOT NULL,
        entity_type     TEXT,
        entity_id       TEXT,
        detail          TEXT,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- ═══════════════════════════════════════════════════════════════════
    -- Module C: Load confirmation (stored in driver_events, but also
    -- a convenience table for quick lookup)
    -- ═══════════════════════════════════════════════════════════════════

    CREATE TABLE IF NOT EXISTS load_confirmations (
        id              TEXT PRIMARY KEY,
        trip_id         TEXT NOT NULL REFERENCES trips(id),
        driver_id       TEXT NOT NULL REFERENCES drivers(id),
        event_id        TEXT REFERENCES driver_events(id),
        departed_at     TEXT,
        groups_json     TEXT,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    """)

    db.commit()
