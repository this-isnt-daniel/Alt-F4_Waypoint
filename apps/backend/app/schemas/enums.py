from enum import Enum

class Brand(str, Enum):
    fresh = "fresh"
    style = "style"
    tech = "tech"

class TempReq(str, Enum):
    ambient = "ambient"
    chilled = "chilled"

class VehicleType(str, Enum):
    truck = "truck"
    van = "van"

class VehicleTemp(str, Enum):
    reefer = "reefer"
    ambient = "ambient"

class DockType(str, Enum):
    rear_dock = "rear_dock"
    street = "street"
    mall_bay = "mall_bay"

class ParkConstraint(str, Enum):
    normal = "normal"
    van_only = "van_only"
    mall_dock = "mall_dock"

class UserRole(str, Enum):
    store_manager = "store_manager"
    dispatcher = "dispatcher"
    loader = "loader"
    driver = "driver"

class OrderStatus(str, Enum):
    draft = "draft"
    confirmed = "confirmed"
    planned = "planned"
    loaded = "loaded"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    deferred = "deferred"

class TripStatus(str, Enum):
    planned = "planned"
    loaded = "loaded"
    out_for_delivery = "out_for_delivery"
    completed = "completed"

class StopStatus(str, Enum):
    upcoming = "upcoming"
    arrived = "arrived"
    delivered = "delivered"
    skipped = "skipped"

class LoadCheckStatus(str, Enum):
    ok = "ok"
    shortfall = "shortfall"

class LoadCheckItemStatus(str, Enum):
    ok = "ok"
    shortfall = "shortfall"
    damaged = "damaged"

class DiscrepancyType(str, Enum):
    missing = "missing"
    damaged = "damaged"
    wrong_item = "wrong_item"
    short_qty = "short_qty"
    other = "other"

class DiscrepancyStatus(str, Enum):
    open = "open"
    resolved = "resolved"

class DeliveryEventType(str, Enum):
    order_confirmed = "order_confirmed"
    order_planned = "order_planned"
    order_loaded = "order_loaded"
    order_out_for_delivery = "order_out_for_delivery"
    order_delivered = "order_delivered"
    order_deferred = "order_deferred"

class EventSyncStatus(str, Enum):
    pending = "pending"
    applied = "applied"
    conflict = "conflict"
    failed = "failed"
    already_applied = "already_applied"
