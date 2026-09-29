const fs = require('fs');

const originalMock = [
  { 
    id: 'VEH011', depot: 'peliyagoda', type: 'Truck · Reefer', route: 'Gampaha Fresh', stops: 3, status: 'En Route', color: 'blue', desc: 'Expected Depot Return: 08:22 AM',
    location: { lat: 7.0873, lng: 79.9995 },
    routeCoords: [{ lat: 6.9654, lng: 79.8821 }, { lat: 7.0873, lng: 79.9995 }]
  },
  { 
    id: 'VEH009', depot: 'peliyagoda', type: 'Truck · Reefer', route: 'Gampaha Fresh', stops: 3, status: 'Returning', color: 'orange', eta: 'ETA: 08:45 AM (In 15 mins)', action: 'Pre-stage next trip cargo',
    location: { lat: 7.0100, lng: 79.9300 },
    routeCoords: [{ lat: 7.0873, lng: 79.9995 }, { lat: 6.9654, lng: 79.8821 }]
  },
  { 
    id: 'VEH019', depot: 'peliyagoda', type: 'Van · Ambient', route: 'Colombo Central Style', stops: 4, status: 'Delayed', color: 'red', desc: 'Adjusted return: 10:42 AM (+22m late)', isRedDesc: true,
    location: { lat: 6.9271, lng: 79.8612 },
    routeCoords: [{ lat: 6.9654, lng: 79.8821 }, { lat: 6.9271, lng: 79.8612 }]
  },
  { 
    id: 'VEH041', depot: 'peliyagoda', type: 'Truck · Ambient', route: 'Liberty Plaza Style', stops: null, status: 'Dispatched', color: 'brand', desc: 'Released 03:28 AM · Driver: S. Perera',
    location: { lat: 6.9099, lng: 79.8519 },
    routeCoords: [{ lat: 6.9654, lng: 79.8821 }, { lat: 6.9099, lng: 79.8519 }]
  },
  { 
    id: 'VEH014', depot: 'peliyagoda', type: 'Truck · Reefer', route: 'Gampaha Fresh North', stops: 5, status: 'En Route', color: 'blue', desc: 'Expected Depot Return: 09:15 AM',
    location: { lat: 7.2008, lng: 79.8737 },
    routeCoords: [{ lat: 6.9654, lng: 79.8821 }, { lat: 7.2008, lng: 79.8737 }]
  },

  { 
    id: 'VEH-K01', depot: 'kandy', type: 'Truck · Ambient', route: 'Peradeniya Route', stops: 4, status: 'En Route', color: 'blue', desc: 'Expected Depot Return: 07:15 AM',
    location: { lat: 7.2687, lng: 80.5975 },
    routeCoords: [{ lat: 7.2906, lng: 80.6337 }, { lat: 7.2687, lng: 80.5975 }]
  },
  { 
    id: 'VEH-K02', depot: 'kandy', type: 'Van · Reefer', route: 'Katugastota Fresh', stops: 6, status: 'Returning', color: 'orange', eta: 'ETA: 08:10 AM (In 20 mins)', action: 'Pre-stage next trip cargo',
    location: { lat: 7.3000, lng: 80.6300 },
    routeCoords: [{ lat: 7.3235, lng: 80.6212 }, { lat: 7.2906, lng: 80.6337 }]
  },
  { 
    id: 'VEH-K05', depot: 'kandy', type: 'Van · Ambient', route: 'Kandy Town Style', stops: null, status: 'Dispatched', color: 'brand', desc: 'Released 04:15 AM · Driver: K. Bandara',
    location: { lat: 7.2950, lng: 80.6350 },
    routeCoords: [{ lat: 7.2906, lng: 80.6337 }, { lat: 7.2950, lng: 80.6350 }]
  }
];

const additionalVehicles = [];
for (let i = 1; i <= 25; i++) {
  // Peliyagoda: strictly inland/north/south, avoid west ocean (lng < 79.85)
  // Base: 6.9654, 79.8821
  const pLat1 = 6.9654 + (Math.random() * 0.15 - 0.05);
  const pLng1 = 79.8821 + (Math.random() * 0.15); // only eastwards
  
  const pLat2 = 6.9654 + (Math.random() * 0.15 - 0.05);
  const pLng2 = 79.8821 + (Math.random() * 0.15);

  additionalVehicles.push({
    id: `VEH-P${100 + i}`, depot: 'peliyagoda', type: 'Truck · Ambient', route: `Route P${i}`, stops: 2, status: 'En Route', color: 'blue',
    location: { lat: pLat1, lng: pLng1 },
    routeCoords: [{ lat: 6.9654, lng: 79.8821 }, { lat: pLat1, lng: pLng1 }]
  });
  additionalVehicles.push({
    id: `VEH-P${200 + i}`, depot: 'peliyagoda', type: 'Van · Reefer', route: `Route P${i} (Return)`, stops: 3, status: 'Returning', color: 'orange',
    location: { lat: pLat2, lng: pLng2 },
    routeCoords: [{ lat: pLat2, lng: pLng2 }, { lat: 6.9654, lng: 79.8821 }]
  });

  // Kandy: Central, so small variations are fine
  const kLat1 = 7.2906 + (Math.random() - 0.5) * 0.1;
  const kLng1 = 80.6337 + (Math.random() - 0.5) * 0.1;
  const kLat2 = 7.2906 + (Math.random() - 0.5) * 0.1;
  const kLng2 = 80.6337 + (Math.random() - 0.5) * 0.1;

  additionalVehicles.push({
    id: `VEH-K${100 + i}`, depot: 'kandy', type: 'Truck · Ambient', route: `Route K${i}`, stops: 2, status: 'En Route', color: 'blue',
    location: { lat: kLat1, lng: kLng1 },
    routeCoords: [{ lat: 7.2906, lng: 80.6337 }, { lat: kLat1, lng: kLng1 }]
  });
  additionalVehicles.push({
    id: `VEH-K${200 + i}`, depot: 'kandy', type: 'Van · Reefer', route: `Route K${i} (Return)`, stops: 3, status: 'Returning', color: 'orange',
    location: { lat: kLat2, lng: kLng2 },
    routeCoords: [{ lat: kLat2, lng: kLng2 }, { lat: 7.2906, lng: 80.6337 }]
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

const allVehicles = [...originalMock, ...additionalVehicles];

let code = fs.readFileSync('src/pages/loader/LoaderHome.jsx', 'utf8');
const targetStr = 'const MOCK_VEHICLES = ';
const endTargetStr = '];';
const startIndex = code.indexOf(targetStr);
const exportIndex = code.indexOf('export default function LoaderHome');
const oldArrayText = code.substring(startIndex, exportIndex);

code = code.replace(oldArrayText, `const MOCK_VEHICLES = ${JSON.stringify(allVehicles, null, 2)};\n\n`);

fs.writeFileSync('src/pages/loader/LoaderHome.jsx', code);
console.log('MOCK_VEHICLES rewritten with safe coordinates');
