from enum import Enum

class Brand(str, Enum):
    FRESH = "fresh"
    STYLE = "style"
    TECH = "tech"

class TempRequirement(str, Enum):
    AMBIENT = "ambient"
    CHILLED = "chilled"

class VehicleType(str, Enum):
    TRUCK = "truck"
    VAN = "van"

class VehicleTemp(str, Enum):
    REEFER = "reefer"
    AMBIENT = "ambient"

class DockType(str, Enum):
    REAR_DOCK = "rear_dock"
    STREET = "street"
    MALL_BAY = "mall_bay"

class ParkingConstraint(str, Enum):
    NORMAL = "normal"
    VAN_ONLY = "van_only"
    MALL_DOCK = "mall_dock"

class UserRole(str, Enum):
    STORE_MANAGER = "store_manager"
    DISPATCHER = "dispatcher"
    LOADER = "loader"
    DRIVER = "driver"

class OrderStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PLANNED = "planned"
    LOADED = "loaded"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    DEFERRED = "deferred"

class DeliveryEventType(str, Enum):
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_PLANNED = "order_planned"
    ORDER_LOADED = "order_loaded"
    ORDER_OUT_FOR_DELIVERY = "order_out_for_delivery"
    ORDER_DELIVERED = "order_delivered"
    ORDER_DEFERRED = "order_deferred"

class DiscrepancyType(str, Enum):
    MISSING = "missing"
    DAMAGED = "damaged"
    WRONG_ITEM = "wrong_item"
    SHORT_QUANTITY = "short_quantity"
    OTHER = "other"

class TripStatus(str, Enum):
    PLANNED = "planned"
    LOADED = "loaded"
    OUT_FOR_DELIVERY = "out_for_delivery"
    COMPLETED = "completed"

class LoadCheckStatus(str, Enum):
    OK = "ok"
    SHORTFALL = "shortfall"

class UrgentNeedStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
