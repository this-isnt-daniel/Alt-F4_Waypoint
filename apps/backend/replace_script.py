import re

file_path = r"c:\Daniel\Projects\Alt-F4_Waypoint\apps\frontend\src\pages\dispatcher\DispatcherRoster.jsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

replacement = """  const [vehicleAssignments, setVehicleAssignments] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/dispatcher/trips/active')
      .then(res => res.json())
      .then(data => {
        // Group trips by vehicle (or just list them as assignments)
        const mapped = data.map(trip => {
          let totalCrates = 0;
          const stops = trip.stops.map((stop, index) => {
            let stopCrates = 0;
            const items = stop.items.map(i => {
              stopCrates += i.quantity;
              return { sku: i.product_id, name: i.product_id, category: 'General', quantity: `${i.quantity} Units`, weight: 'N/A' };
            });
            totalCrates += stopCrates;
            
            return {
              id: stop.outlet_id,
              name: `Outlet ${stop.outlet_id}`,
              eta: stop.expected_arrival || 'N/A',
              status: stop.status === 'in_progress' ? 'En Route' : (stop.status === 'upcoming' ? 'Scheduled' : 'Completed'),
              crates: stopCrates,
              weightKg: 0,
              cargo: 'Mixed Goods',
              items: items
            };
          });

          return {
            id: trip.vehicle_id || 'Unassigned',
            type: 'Vehicle',
            refrigeration: trip.temp_type === 'reefer' ? 'Reefer' : 'Ambient',
            activeLeg: `Trip ${trip.trip_id}`,
            tripLock: 'Fresh / Style',
            currentDestination: stops.length > 0 ? stops[stops.length-1].id : 'Depot',
            startTime: '06:00 AM',
            endTime: '12:00 PM',
            stopsCount: stops.length,
            tripStatus: trip.status === 'in_progress' ? 'Active' : 'Planned',
            driverName: 'Driver',
            driverPhone: 'N/A',
            departureTime: '06:00 AM',
            totalCrates: totalCrates,
            weightKg: 0,
            temperature: trip.temp_type === 'reefer' ? '+4.2°C' : 'N/A',
            stops: stops
          };
        });
        setVehicleAssignments(mapped);
      })
      .catch(err => console.error("Failed to fetch trips:", err));
  }, []);"""

# regex to find const initialVehicleAssignments = [ ... ];
pattern = r"  const initialVehicleAssignments = \[\n(?:.|\n)*?  \];"

new_content = re.sub(pattern, replacement, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Replaced initialVehicleAssignments with API fetch.")
