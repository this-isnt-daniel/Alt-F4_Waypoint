import re

with open('app/services/loader_service.py', 'r') as f:
    content = f.read()

# Fix EDITABLE_TRIP_STATUSES
content = re.sub(r'EDITABLE_TRIP_STATUSES = .*', 'EDITABLE_TRIP_STATUSES = {"planned"}', content)
content = re.sub(r'READ_ONLY_TRIP_STATUSES = .*', 'READ_ONLY_TRIP_STATUSES = {"loaded", "out_for_delivery", "completed"}', content)

# Remove trip.status = "loading"
content = re.sub(r'\s*if trip\.status == "planned":\s*trip\.status = "loading"', '', content)
content = re.sub(r'\s*trip\.status = "loading"', '', content)

# Remove stop_model.status = "loading_complete"
content = re.sub(r'\s*stop_model\.status = "loading_complete"', '', content)

# Fix LoadCheck status: only create it on submit_load_check, not in progress.
# Wait, loader starts loading, creates LoadCheck... 
# Let's change LoadCheck status default to 'ok'
content = content.replace('status: str = "in_progress"', 'status: str = "ok"')

# Replace "loading" with "planned" in conditions:
content = content.replace('Trip.status.in_(["planned", "loading", "loaded", "out_for_delivery", "vehicle_unavailable"])', 'Trip.status.in_(["planned", "loaded", "out_for_delivery", "completed"])')
content = content.replace('order.status in {"planned", "loading"}', 'order.status == "planned"')

# For mark_vehicle_unavailable
# Change vehicle.status = "unavailable" to "in_workshop"
content = content.replace('vehicle.status = "unavailable"', 'vehicle.status = "in_workshop"')
# Change trip.status = "vehicle_unavailable" to "cancelled" (wait, there's no cancelled in TripStatus! So we keep it "planned" or we don't change trip status. Let's just remove changing trip status, keep it "planned")
content = re.sub(r'\s*trip\.status = "vehicle_unavailable"', '', content)
content = content.replace('if trip.status in {"cancelled", "vehicle_unavailable"}:', 'if trip.status == "completed":') # No cancelled or vehicle_unavailable

# In build_workbench:
# complete=stop.status in {"loaded", "loading_complete"} 
content = content.replace('complete=stop.status in {"loaded", "loading_complete"}', 'complete=stop.status in {"delivered", "skipped"}')

# Wait, the load check status should be 'completed' when submitted? No, canonical is ok or shortfall.
content = content.replace('check.status = "completed"', 'check.status = "shortfall" if discrepancy_count > 0 else "ok"')

with open('app/services/loader_service.py', 'w') as f:
    f.write(content)
