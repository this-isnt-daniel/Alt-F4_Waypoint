const fs = require('fs');
let content = fs.readFileSync('src/pages/loader/LoaderHome.jsx', 'utf8');

const additionalVehicles = [];
for (let i = 1; i <= 25; i++) {
  additionalVehicles.push({
    id: `VEH-P${100 + i}`, depot: 'peliyagoda', type: 'Truck · Ambient', route: `Route P${i}`, stops: 2, status: 'En Route', color: 'blue',
    location: { lat: 6.9654 + (Math.random() - 0.5) * 0.5, lng: 79.8821 + (Math.random() - 0.5) * 0.5 },
    routeCoords: [{ lat: 6.9654, lng: 79.8821 }, { lat: 6.9654 + (Math.random() - 0.5) * 0.5, lng: 79.8821 + (Math.random() - 0.5) * 0.5 }]
  });
  additionalVehicles.push({
    id: `VEH-P${200 + i}`, depot: 'peliyagoda', type: 'Van · Reefer', route: `Route P${i} (Return)`, stops: 3, status: 'Returning', color: 'orange',
    location: { lat: 6.9654 + (Math.random() - 0.5) * 0.5, lng: 79.8821 + (Math.random() - 0.5) * 0.5 },
    routeCoords: [{ lat: 6.9654 + (Math.random() - 0.5) * 0.5, lng: 79.8821 + (Math.random() - 0.5) * 0.5 }, { lat: 6.9654, lng: 79.8821 }]
  });
  additionalVehicles.push({
    id: `VEH-K${100 + i}`, depot: 'kandy', type: 'Truck · Ambient', route: `Route K${i}`, stops: 2, status: 'En Route', color: 'blue',
    location: { lat: 7.2906 + (Math.random() - 0.5) * 0.5, lng: 80.6337 + (Math.random() - 0.5) * 0.5 },
    routeCoords: [{ lat: 7.2906, lng: 80.6337 }, { lat: 7.2906 + (Math.random() - 0.5) * 0.5, lng: 80.6337 + (Math.random() - 0.5) * 0.5 }]
  });
  additionalVehicles.push({
    id: `VEH-K${200 + i}`, depot: 'kandy', type: 'Van · Reefer', route: `Route K${i} (Return)`, stops: 3, status: 'Returning', color: 'orange',
    location: { lat: 7.2906 + (Math.random() - 0.5) * 0.5, lng: 80.6337 + (Math.random() - 0.5) * 0.5 },
    routeCoords: [{ lat: 7.2906 + (Math.random() - 0.5) * 0.5, lng: 80.6337 + (Math.random() - 0.5) * 0.5 }, { lat: 7.2906, lng: 80.6337 }]
  });
}
for (let i = 1; i <= 5; i++) {
  additionalVehicles.push({
    id: `VEH-P${300 + i}`, depot: 'peliyagoda', type: 'Truck · Reefer', route: 'Hub Staging', stops: 0, status: 'Dispatched', color: 'brand',
    location: { lat: 6.9654, lng: 79.8821 },
    routeCoords: null
  });
  additionalVehicles.push({
    id: `VEH-K${300 + i}`, depot: 'kandy', type: 'Truck · Reefer', route: 'Hub Staging', stops: 0, status: 'Dispatched', color: 'brand',
    location: { lat: 7.2906, lng: 80.6337 },
    routeCoords: null
  });
}

content = content.replace('];', '  ...JSON.parse(`' + JSON.stringify(additionalVehicles) + '`)\n];');
fs.writeFileSync('src/pages/loader/LoaderHome.jsx', content);
console.log('MOCK_VEHICLES updated');
