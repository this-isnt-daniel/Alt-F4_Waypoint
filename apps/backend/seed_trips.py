import os
from datetime import date
from app.db.session import SessionLocal
from app.models.trip import Trip, TripStop, TripStopItem
from app.models.order import Order, OrderLine

def seed_trips():
    db = SessionLocal()
    try:
        # 1. Ensure we don't duplicate
        if db.query(Trip).filter(Trip.vehicle_id == "VEH014").first():
            print("Trips already seeded.")
            return

        today = date.today()

        # Helper to create orders and trips
        def create_trip(trip_id, vehicle_id, temp_type, trip_no, stops_data):
            trip = Trip(
                trip_id=trip_id,
                depot_id="peliyagoda",
                vehicle_id=vehicle_id,
                dispatcher_id="USR-999",
                trip_date=today,
                trip_no=trip_no,
                status="in_progress"
            )
            db.add(trip)
            db.commit()

            seq = 1
            for stop in stops_data:
                outlet_id = stop['outlet_id']
                order_id = f"ORD-{trip_id}-{seq}"
                
                # Create Order
                order = Order(
                    order_id=order_id,
                    outlet_id=outlet_id,
                    brand="Fresh",
                    temp_req=temp_type,
                    order_date=today,
                    status="planned",
                    created_by="USR-999",
                    defer_count=0
                )
                db.add(order)
                db.commit()

                # Create TripStop
                trip_stop = TripStop(
                    stop_id=f"STP-{trip_id}-{seq}",
                    trip_id=trip_id,
                    outlet_id=outlet_id,
                    order_id=order_id,
                    stop_seq=seq,
                    eta=stop['eta'],
                    temp_req=temp_type,
                    status=stop['status']
                )
                db.add(trip_stop)
                db.commit()

                # Create lines
                for line in stop['lines']:
                    line_item_id = f"LNE-{order_id}-{line['sku']}"
                    order_line = OrderLine(
                        line_item_id=line_item_id,
                        order_id=order_id,
                        product_id=line['sku'],
                        quantity=line['qty']
                    )
                    db.add(order_line)
                    db.commit()

                    trip_stop_item = TripStopItem(
                        stop_item_id=f"TSI-{trip_stop.stop_id}-{line['sku']}",
                        stop_id=trip_stop.stop_id,
                        line_item_id=line_item_id
                    )
                    db.add(trip_stop_item)
                    db.commit()

                seq += 1

        # TRIP 1: VEH014
        create_trip("TRP-VEH014-1", "VEH014", "reefer", 1, [
            {
                "outlet_id": "OUT-011", "eta": "07:30 AM", "status": "Completed",
                "lines": [{"sku": "DAI-102", "qty": 40}, {"sku": "VEG-05", "qty": 20}]
            },
            {
                "outlet_id": "OUT-015", "eta": "08:10 AM", "status": "Completed",
                "lines": [{"sku": "DAI-204", "qty": 48}, {"sku": "DAI-309", "qty": 120}]
            },
            {
                "outlet_id": "OUT-1029", "eta": "08:50 AM", "status": "Completed",
                "lines": [{"sku": "VEG-102", "qty": 36}, {"sku": "VEG-108", "qty": 45}]
            },
            {
                "outlet_id": "OUT-3012", "eta": "09:20 AM", "status": "Completed",
                "lines": [{"sku": "DAI-401", "qty": 72}, {"sku": "MEA-105", "qty": 50}]
            },
            {
                "outlet_id": "OUT-4089", "eta": "09:55 AM (Now)", "status": "in_progress",
                "lines": [{"sku": "FRU-301", "qty": 120}, {"sku": "DAI-502", "qty": 100}]
            }
        ])

        # TRIP 2: VEH009
        create_trip("TRP-VEH009-1", "VEH009", "reefer", 1, [
            {
                "outlet_id": "OUT-2041", "eta": "07:15 AM", "status": "Completed",
                "lines": [{"sku": "VEG-22", "qty": 10}]
            },
            {
                "outlet_id": "OUT-091", "eta": "08:00 AM", "status": "upcoming",
                "lines": [{"sku": "DAI-44", "qty": 15}]
            }
        ])

        print("Successfully seeded trips!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding trips: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_trips()
