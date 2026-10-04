import React, { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { apiFetch } from '../../lib/api';

// Fix for default Leaflet icon paths in Vite/Webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Create custom DivIcons for our points
const createDepotIcon = (name) => L.divIcon({
  className: 'bg-transparent',
  html: `
    <div class="relative flex flex-col items-center">
      <div class="w-4 h-4 rounded-full bg-slate-800 border-2 border-white shadow-md z-10"></div>
      <div class="mt-1 bg-white px-2 py-0.5 rounded shadow-sm border border-slate-200 text-[10px] font-bold text-slate-700 whitespace-nowrap">${name}</div>
    </div>
  `,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const createOutletIcon = (name) => L.divIcon({
  className: 'bg-transparent',
  html: `
    <div class="relative flex flex-col items-center">
      <div class="w-4 h-4 rounded-full bg-[#059669] border-2 border-white shadow-md z-10"></div>
      <div class="mt-1 bg-white px-2 py-0.5 rounded shadow-sm border border-slate-200 text-[10px] font-bold text-slate-700 whitespace-nowrap">${name}</div>
    </div>
  `,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const createVehicleIcon = (id) => L.divIcon({
  className: 'bg-transparent',
  html: `
    <div class="relative flex flex-col items-center">
      <div class="w-7 h-7 rounded-full bg-[#059669] border-2 border-white shadow-md flex items-center justify-center text-[12px] z-20">
        🚚
      </div>
      <div class="mt-1 bg-white px-2 py-0.5 rounded shadow-sm border border-slate-200 text-[10px] font-bold text-[#059669] whitespace-nowrap">${id}</div>
    </div>
  `,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [map, bounds]);
  return null;
}

function RoadRoutePolyline({ points }) {
  const [route, setRoute] = useState([]);

  useEffect(() => {
    if (points.length < 2) return;
    const coordsStr = points.map(p => `${p[1]},${p[0]}`).join(';');
    const url = `https://router.project-osrm.org/route/v1/driving/${coordsStr}?overview=full&geometries=geojson`;
    
    fetch(url)
      .then(res => res.json())
      .then(data => {
        if (data.routes && data.routes[0]) {
          const latLngs = data.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
          setRoute(latLngs);
        }
      })
      .catch(console.error);
  }, [points]);

  if (route.length === 0) {
     return <Polyline positions={points} pathOptions={{ color: '#0ea5e9', weight: 4, opacity: 0.5, dashArray: '5, 10' }} />;
  }

  return <Polyline positions={route} pathOptions={{ color: '#0ea5e9', weight: 4, opacity: 0.8 }} />;
}
import waypointLogo from '../../assets/icons/waypoint_logo.png';
import VerifyDispatchPlanModal from './VerifyDispatchPlanModal';
import RouteAllocationBoard from './RouteAllocationBoard';
import RecoveryPlanModal from './RecoveryPlanModal';
import { 
  Moon, 
  ChevronDown, 
  ChevronUp,
  ChevronRight,
  Bell, 
  Search, 
  ArrowRight,
  ArrowLeft,
  Check,
  Lock,
  Clock,
  AlertTriangle,
  Wrench,
  Info,
  Truck,
  MapPin,
  Package,
  Building2,
  CheckCircle2,
  AlertCircle,
  Navigation,
  ExternalLink,
  RotateCcw,
  Sparkles,
  Plus,
  Minus,
  Filter
} from 'lucide-react';

export default function DispatcherRoster({ onLogout }) {
  // Navigation & Sub-tabs (Reset for Fleet Allocation Demo Video)
  const [activeNav, setActiveNav] = useState('Overview');
  const [activeSubTab, setActiveSubTab] = useState('Fleet Availability');
  const [selectedHub, setSelectedHub] = useState('Peliyagoda');
  const [categoryFilter, setCategoryFilter] = useState('all'); // 'all' | 'reefer' | 'van'
  const [searchQuery, setSearchQuery] = useState('');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [hasUnreadNotifications, setHasUnreadNotifications] = useState(true);
  const [selectedRowId, setSelectedRowId] = useState('VEH004');
  const [showDispatchPlanModal, setShowDispatchPlanModal] = useState(false);
  const [showAllocationBoard, setShowAllocationBoard] = useState(false);

  // Overview Section State (Requested by user: schematic map & live runs table)
  const [overviewDepot, setOverviewDepot] = useState('Peliyagoda Depot');
  const [showOverviewDepotMenu, setShowOverviewDepotMenu] = useState(false);
  const [mapSearch, setMapSearch] = useState('');
  const [selectedMapVehicle, setSelectedMapVehicle] = useState('VEH014');
  const [overviewFilterTab, setOverviewFilterTab] = useState('all'); // 'all' | 'outlet' | 'delayed' | 'offline' | 'completed'

  // Allocation Workbench State
  const [workbenchView, setWorkbenchView] = useState('vehicle'); // 'vehicle' | 'outlet' | 'deferrals'
  const [workbenchFilter, setWorkbenchFilter] = useState('all'); // 'all' | 'reefers' | 'delayed'
  const [deferralCategoryFilter, setDeferralCategoryFilter] = useState('all'); // 'all' | 'damaged' | 'unavailable'
  const [workbenchSearch, setWorkbenchSearch] = useState('');
  const [deferralSearch, setDeferralSearch] = useState('');
  const [expandedVehicleIds, setExpandedVehicleIds] = useState(new Set(['VEH014'])); // Default expanded for instant stop inspection
  const [expandedStopIds, setExpandedStopIds] = useState(new Set(['VEH014-OUT-4089'])); // Default expanded stop for item manifest inspection
  const [expandedOutletIds, setExpandedOutletIds] = useState(new Set(['OUT-4089'])); // Default expanded for outlet vehicle inspection
  const [isAllocationConfirmed, setIsAllocationConfirmed] = useState(false);
  const [showConfirmToast, setShowConfirmToast] = useState(false);
  const [showRecoveryModal, setShowRecoveryModal] = useState(false);
  const [recoveryDeployed, setRecoveryDeployed] = useState(false);
  const [expandedContingencyIds, setExpandedContingencyIds] = useState(new Set());
  const [expandedActiveTripIds, setExpandedActiveTripIds] = useState(new Set(['VEH014']));

  // Contingency Dispatch Disrupted Orders Dataset (Breakdowns & Damaged POD)
  const [contingencyDisruptedOrders, setContingencyDisruptedOrders] = useState([]);

  useEffect(() => {
    apiFetch('/dispatcher/incidents')
      .then(data => {
        const formatted = data.map((inc, i) => ({
          id: inc.incident_id,
          incidentVehicle: inc.vehicle_id,
          type: 'Truck', // Ideally joined from vehicles API
          refrigeration: 'Reefer', 
          tripLabel: inc.trip_id || `Trip ${i+1}`,
          cargoLine: 'Fresh Produce / Dairy',
          reasonPill: inc.type,
          reasonDetail: inc.detail,
          destination: 'Depot / Current Stop',
          reportedTime: new Date(inc.reported_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
          driver: 'N/A', // inc.reported_by is an ID, ideally join User name
          freshWindow: 'Window Alert'
        }));
        setContingencyDisruptedOrders(formatted);
      })
      .catch(err => console.error("Failed to fetch incidents:", err));
  }, []);

  // Active Contingency Recovery Trips (Matching user screenshot)
  const contingencyActiveTrips = [
    {
      vehicleId: 'VEH014',
      type: 'Van',
      refrigeration: 'Reefer',
      tripLabel: 'Trip 1 of 2',
      cargoLine: 'Fresh - Colombo Central',
      stopsCount: 5,
      destination: 'OUT-4089 Nugegoda',
      timeWindow: '07:45 AM - 11:15 AM',
      stopList: [
        { stop: 1, name: 'Colombo South OUT011', time: '08:15 AM', status: 'Completed' },
        { stop: 2, name: 'Kollupitiya OUT015', time: '09:00 AM', status: 'In Transit' },
        { stop: 3, name: 'Liberty Plaza OUT1029', time: '09:45 AM', status: 'Scheduled (Recovered)' },
        { stop: 4, name: 'Maharagama OUT3012', time: '10:30 AM', status: 'Scheduled (Recovered)' },
        { stop: 5, name: 'Nugegoda OUT4089', time: '11:15 AM', status: 'Scheduled' }
      ]
    },
    {
      vehicleId: 'VEH009',
      type: 'Truck',
      refrigeration: 'Reefer',
      tripLabel: 'Trip 2 of 2',
      cargoLine: 'Fresh - Gampaha',
      stopsCount: 5,
      destination: 'OUT-2041 Wattala',
      timeWindow: '07:15 AM - 11:00 AM',
      stopList: [
        { stop: 1, name: 'Peliyagoda OUT001', time: '07:45 AM', status: 'Completed' },
        { stop: 2, name: 'Wattala OUT2041', time: '08:30 AM', status: 'In Transit' },
        { stop: 3, name: 'Ja-Ela Central OUT091', time: '09:15 AM', status: 'Scheduled' },
        { stop: 4, name: 'Kandana OUT064', time: '10:00 AM', status: 'Scheduled' },
        { stop: 5, name: 'Gampaha North OUT102', time: '11:00 AM', status: 'Scheduled' }
      ]
    },
    {
      vehicleId: 'VEH041',
      type: 'Truck',
      refrigeration: 'Ambient',
      tripLabel: 'Trip 1 of 2',
      cargoLine: 'Style - Colombo',
      stopsCount: 4,
      destination: 'OUT-1029 Liberty Plaza',
      timeWindow: '08:00 AM - 11:45 AM',
      stopList: [
        { stop: 1, name: 'Pettah Main OUT004', time: '08:45 AM', status: 'Completed' },
        { stop: 2, name: 'Fort Central OUT008', time: '09:30 AM', status: 'In Transit' },
        { stop: 3, name: 'Wellawatte OUT022', time: '10:45 AM', status: 'Scheduled' },
        { stop: 4, name: 'Liberty Plaza OUT1029', time: '11:45 AM', status: 'Scheduled (Recovered)' }
      ]
    }
  ];

  // Hover state for unavailable vehicle popover tooltip (Fleet Availability)
  const [hoveredUnavailableVehicle, setHoveredUnavailableVehicle] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const [fleetList, setFleetList] = useState([]);

  useEffect(() => {
    apiFetch('/dispatcher/vehicles')
      .then(data => {
        if (!Array.isArray(data)) return;
        const formatted = data.map(v => ({
          id: v.vehicle_id || 'UNKNOWN',
          depot: v.depot_id === 'peliyagoda' ? 'Peliyagoda' : (v.depot_id === 'kandy' ? 'Kandy' : (v.depot_id || 'Peliyagoda')),
          type: v.type ? (v.type.charAt(0).toUpperCase() + v.type.slice(1)) : 'Van',
          refrigeration: v.temp === 'reefer' ? 'Reefer' : 'Ambient',
          payloadKg: Number(v.weight_cap_kg) || 2500,
          volumeM3: Number(v.vol_cap_m3) || 12.5,
          fuelQuota: Number(v.fuel_quota_l) || 85,
          checked: v.status === 'available',
          isLockedUnavailable: v.status !== 'available',
          unavailableSource: v.status !== 'available' ? 'Dispatcher Portal' : '',
          unavailableReason: v.status !== 'available' ? 'Marked Unavailable' : ''
        }));
        setFleetList(formatted);
      })
      .catch(err => console.error("Failed to fetch vehicles:", err));
  }, []);

  // Proposed Vehicle Assignments Dataset with Stops and Shop Items
  const [vehicleAssignments, setVehicleAssignments] = useState([]);

  useEffect(() => {
    apiFetch('/dispatcher/trips/active')
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
  }, []);

  // Proposed Outlet Assignments Dataset
  const initialOutletAssignments = [
    {
      id: 'OUT-4089',
      name: 'Nugegoda Supermarket',
      district: 'Colombo Central',
      deliveryWindow: '08:30 AM - 11:00 AM',
      totalDemand: '48 crates · 1,450 kg',
      status: '1 Completed, 1 En Route',
      assignedVehicles: [
        {
          id: 'VEH014',
          type: 'Van',
          refrigeration: 'Reefer',
          tripLeg: 'Trip 1 of 2',
          eta: '09:55 AM',
          status: 'En Route',
          driver: 'Sunil Bandara (+94 77 123 4567)',
          cargo: '18 crates fresh berries & yogurt'
        },
        {
          id: 'VEH004',
          type: 'Van',
          refrigeration: 'Ambient',
          tripLeg: 'Trip 1 of 1',
          eta: '11:15 AM',
          status: 'Scheduled',
          driver: 'Anura Rathnayake (+94 78 567 8901)',
          cargo: '15 cartons ambient groceries'
        }
      ]
    },
    {
      id: 'OUT-2041',
      name: 'Wattala Mega Store',
      district: 'Gampaha',
      deliveryWindow: '09:00 AM - 12:30 PM',
      totalDemand: '70 crates · 2,800 kg',
      status: '1 Completed, 1 Delayed (+14m)',
      assignedVehicles: [
        {
          id: 'VEH009',
          type: 'Truck',
          refrigeration: 'Reefer',
          tripLeg: 'Trip 2 of 2',
          eta: '10:35 AM (Delivered)',
          status: 'Completed',
          driver: 'Kamal Wickramasinghe (+94 71 987 6543)',
          cargo: '28 crates reefer goods'
        },
        {
          id: 'VEH027',
          type: 'Truck',
          refrigeration: 'Reefer',
          tripLeg: 'Trip 1 of 2',
          eta: '10:14 AM (Delayed +14m)',
          status: 'Delayed',
          driver: 'Nalin Jayasinghe (+94 70 876 5432)',
          cargo: '42 crates chilled dairy & produce'
        }
      ]
    },
    {
      id: 'OUT-1029',
      name: 'Liberty Plaza Express',
      district: 'Colombo Central',
      deliveryWindow: '08:00 AM - 10:00 AM',
      totalDemand: '62 cartons/crates · 2,100 kg',
      status: 'At Dock - Unloading',
      assignedVehicles: [
        {
          id: 'VEH041',
          type: 'Truck',
          refrigeration: 'Ambient',
          tripLeg: 'Trip 1 of 2',
          eta: '09:30 AM (Dock 2)',
          status: 'At Dock - Unloading',
          driver: 'Rohan Silva (+94 76 345 6789)',
          cargo: '50 apparel & household cartons'
        },
        {
          id: 'VEH014',
          type: 'Van',
          refrigeration: 'Reefer',
          tripLeg: 'Trip 1 of 2',
          eta: '08:15 AM (Delivered)',
          status: 'Completed',
          driver: 'Sunil Bandara (+94 77 123 4567)',
          cargo: '12 crates chilled dairy'
        }
      ]
    },
    {
      id: 'OUT-3012',
      name: 'Maharagama Central',
      district: 'Colombo South',
      deliveryWindow: '10:15 AM - 12:45 PM',
      totalDemand: '36 crates/cartons · 1,150 kg',
      status: 'Scheduled',
      assignedVehicles: [
        {
          id: 'VEH014',
          type: 'Van',
          refrigeration: 'Reefer',
          tripLeg: 'Trip 1 of 2',
          eta: '10:45 AM',
          status: 'Scheduled',
          driver: 'Sunil Bandara (+94 77 123 4567)',
          cargo: '16 crates chilled meats'
        },
        {
          id: 'VEH003',
          type: 'Van',
          refrigeration: 'Ambient',
          tripLeg: 'Trip 1 of 1',
          eta: '11:45 AM',
          status: 'Scheduled',
          driver: 'Mahesh Wijesinghe (+94 75 112 2334)',
          cargo: '20 dry grocery cartons'
        }
      ]
    },
    {
      id: 'OUT-5021',
      name: 'Mount Lavinia Hub',
      district: 'Colombo South',
      deliveryWindow: '10:00 AM - 01:00 PM',
      totalDemand: '39 crates/cartons · 1,320 kg',
      status: 'En Route',
      assignedVehicles: [
        {
          id: 'VEH004',
          type: 'Van',
          refrigeration: 'Ambient',
          tripLeg: 'Trip 1 of 1',
          eta: '10:05 AM',
          status: 'En Route',
          driver: 'Anura Rathnayake (+94 78 567 8901)',
          cargo: '25 cartons general dry'
        },
        {
          id: 'VEH006',
          type: 'Truck',
          refrigeration: 'Reefer',
          tripLeg: 'Trip 1 of 2',
          eta: '11:45 AM',
          status: 'Scheduled',
          driver: 'Pradeep Kumara (+94 77 445 5667)',
          cargo: '14 crates dairy'
        }
      ]
    },
    {
      id: 'OUT-3044',
      name: 'Negombo Town Supercenter',
      district: 'Gampaha',
      deliveryWindow: '09:15 AM - 11:30 AM',
      totalDemand: '35 crates · 1,200 kg',
      status: 'En Route',
      assignedVehicles: [
        {
          id: 'VEH001',
          type: 'Truck',
          refrigeration: 'Reefer',
          tripLeg: 'Trip 1 of 2',
          eta: '09:45 AM',
          status: 'En Route',
          driver: 'Duminda Perera (+94 72 456 7890)',
          cargo: '35 crates produce & dairy'
        }
      ]
    }
  ];

  // Deferrals Dataset (Damaged / Unavailable goods reasons)
  const initialDeferrals = [
    {
      id: 'DEF-4102',
      orderId: 'ORD-9821',
      sku: 'Fresh Strawberries 250g (Grade A)',
      outlet: 'OUT-4089 Nugegoda',
      quantity: '40 kg (160 punnets)',
      category: 'Damaged Goods',
      reason: 'Pallet collapsed during pre-loading staging at Bay 3; fruit punnets crushed and unmarketable.',
      reportedBy: 'Loader Lead: S. Perera',
      loggedAt: '08:15 AM',
      resolution: 'Flagged for write-off & supplier replacement scheduled for Wave 2'
    },
    {
      id: 'DEF-4108',
      orderId: 'ORD-9844',
      sku: 'Greek Yogurt Pots 500g (Plain)',
      outlet: 'OUT-2041 Wattala',
      quantity: '120 units (60 kg)',
      category: 'Unavailable Goods',
      reason: 'Warehouse cold-room inventory stockout; inbound supplier shipment delayed at port.',
      reportedBy: 'Inventory Controller: D. Jayawardena',
      loggedAt: '07:45 AM',
      resolution: 'Re-queued for 2:00 PM afternoon dispatch wave'
    },
    {
      id: 'DEF-4115',
      orderId: 'ORD-9852',
      sku: 'Frozen Chicken Breast Fillets 1kg',
      outlet: 'OUT-1029 Liberty Plaza',
      quantity: '85 kg (85 master packs)',
      category: 'Damaged Goods',
      reason: 'Vacuum seal puncture detected on master carton during pallet loading; rejected for food safety.',
      reportedBy: 'QA Inspector: T. Ratnayake',
      loggedAt: '08:30 AM',
      resolution: 'Quarantined in Cold Bay; credit note issued to store'
    },
    {
      id: 'DEF-4123',
      orderId: 'ORD-9870',
      sku: 'Organic Hass Avocados (Export Grade)',
      outlet: 'OUT-3012 Maharagama',
      quantity: '60 kg (30 crates)',
      category: 'Unavailable Goods',
      reason: 'Insufficient harvest yield from central highlands farm; shortage allocated across region.',
      reportedBy: 'Supply Chain Planner: M. Alwis',
      loggedAt: '06:50 AM',
      resolution: 'Partial fulfillment (40% deferred to tomorrow morning)'
    },
    {
      id: 'DEF-4131',
      orderId: 'ORD-9891',
      sku: 'Artisanal Cheddar Blocks 1kg',
      outlet: 'OUT-5021 Mount Lavinia',
      quantity: '35 kg (35 units)',
      category: 'Damaged Goods',
      reason: 'Temperature excursion above +12°C during overnight staging; melted packaging rejected.',
      reportedBy: 'Cold Chain Supervisor: H. Mendis',
      loggedAt: '07:15 AM',
      resolution: 'Disposed under cold chain protocol; emergency batch scheduled'
    }
  ];

  // Accordion Toggle Handlers
  const toggleVehicleExpand = (id) => {
    setExpandedVehicleIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleStopExpand = (vehicleId, stopId) => {
    const key = `${vehicleId}-${stopId}`;
    setExpandedStopIds((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const toggleOutletExpand = (id) => {
    setExpandedOutletIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Confirm Route Allocation in-place (No post-allocation page)
  const handleConfirmRouteAllocation = () => {
    setIsAllocationConfirmed(true);
    setShowConfirmToast(true);
    setTimeout(() => {
      setShowConfirmToast(false);
    }, 4000);
  };

  // Fleet Availability Handlers
  const handleToggleCheck = (id) => {
    setFleetList((prev) =>
      prev.map((v) => {
        if (v.id === id) {
          if (v.isLockedUnavailable) return v;
          return { ...v, checked: !v.checked };
        }
        return v;
      })
    );
  };

  const handleSelectAll = () => {
    setFleetList((prev) =>
      prev.map((v) => (v.isLockedUnavailable ? v : { ...v, checked: true }))
    );
  };

  const handleSelectNone = () => {
    setFleetList((prev) =>
      prev.map((v) => (v.isLockedUnavailable ? v : { ...v, checked: false }))
    );
  };

  const handleResetDefault = () => {
    setFleetList(initialFleet);
    setCategoryFilter('all');
    setSearchQuery('');
  };

  // Filtered vehicles for Fleet Availability
  const filteredVehicles = fleetList.filter((vehicle) => {
    if (selectedHub === 'Kandy' && vehicle.depot !== 'Kandy') return false;
    if (categoryFilter === 'reefer' && vehicle.refrigeration !== 'Reefer') return false;
    if (categoryFilter === 'van' && vehicle.type !== 'Van') return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      return (
        vehicle.id.toLowerCase().includes(q) ||
        vehicle.depot.toLowerCase().includes(q) ||
        vehicle.type.toLowerCase().includes(q) ||
        vehicle.refrigeration.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const dispatchableFiltered = filteredVehicles.filter((v) => !v.isLockedUnavailable);
  const allFilteredChecked =
    dispatchableFiltered.length > 0 && dispatchableFiltered.every((v) => v.checked);
  const someFilteredChecked =
    dispatchableFiltered.some((v) => v.checked) && !allFilteredChecked;

  const handleToggleAllFiltered = () => {
    const dispatchableIds = new Set(dispatchableFiltered.map((v) => v.id));
    if (allFilteredChecked) {
      setFleetList((prev) =>
        prev.map((v) => (dispatchableIds.has(v.id) ? { ...v, checked: false } : v))
      );
    } else {
      setFleetList((prev) =>
        prev.map((v) => (dispatchableIds.has(v.id) ? { ...v, checked: true } : v))
      );
    }
  };

  // Live dynamic metrics for Fleet Availability
  const dispatcherExcluded = fleetList.filter((v) => !v.isLockedUnavailable && !v.checked);
  const dispatcherExcludedReefers = dispatcherExcluded.filter((v) => v.refrigeration === 'Reefer').length;
  const dispatcherExcludedVolume = dispatcherExcluded.reduce((acc, v) => acc + (Number(v.volumeM3) || 0), 0);
  const dispatcherExcludedWeight = dispatcherExcluded.reduce((acc, v) => acc + (Number(v.payloadKg) || 0), 0);

  const isKandy = selectedHub === 'Kandy';
  const totalHubVehicles = isKandy ? 18 : 42;
  const totalHubReefers = isKandy ? 8 : 14;
  const baseActiveVehiclesCount = isKandy ? 17 : 38; // 17 active out of 18
  const baseActiveReefersCount = isKandy ? 8 : 12;   // 8 active reefers out of 8
  const baseVolume = isKandy ? 210.5 : 420.5;
  const baseWeight = isKandy ? 45500 : 98400;

  const activeVehiclesCount = Math.max(0, baseActiveVehiclesCount - dispatcherExcluded.length);
  const activeReefersCount = Math.max(0, baseActiveReefersCount - dispatcherExcludedReefers);
  const availableAssetsDisplay = `${activeVehiclesCount}/${totalHubVehicles}`;
  const reeferReadinessDisplay = `${activeReefersCount}/${totalHubReefers}`;
  const totalVolumeM3 = Math.max(0, baseVolume - dispatcherExcludedVolume).toFixed(1);
  const totalPayloadKg = Math.max(0, baseWeight - dispatcherExcludedWeight).toLocaleString();

  // Recovery Vehicle Assignments (Added upon confirming Recovery Plan)
  const recoveryVehicleAssignments = [
    {
      id: 'VEH014',
      isRecovery: true,
      type: 'Van',
      refrigeration: 'Reefer',
      activeLeg: 'Trip 2 of 2',
      tripLock: 'Fresh - Colombo Central (Recovery)',
      currentDestination: 'OUT-1029 Liberty Plaza',
      startTime: '09:30 AM',
      endTime: '11:45 AM',
      stopsCount: 2,
      tripStatus: 'Scheduled',
      driverName: 'Sunil Bandara',
      driverPhone: '+94 77 123 4567',
      departureTime: '09:30 AM',
      totalCrates: 22,
      payloadKg: 1100,
      stops: [
        {
          id: 'OUT-1029',
          name: 'Liberty Plaza Express',
          eta: '09:45 AM',
          status: 'Scheduled',
          crates: 12,
          weightKg: 680,
          cargo: 'Chilled Dairy & Yogurts',
          items: [
            { sku: 'DAI-204', name: 'Anchor Full Cream Milk 1L', category: 'Dairy', quantity: '4 Crates (48 Units)', weight: '48 kg' },
            { sku: 'DAI-309', name: 'Highland Set Yogurt 80g', category: 'Dairy', quantity: '5 Crates (120 Units)', weight: '24 kg' },
            { sku: 'DAI-112', name: 'Pelwatte Salted Butter 200g', category: 'Dairy', quantity: '3 Crates (60 Units)', weight: '12 kg' }
          ]
        },
        {
          id: 'OUT-4089',
          name: 'Nugegoda Supermarket',
          eta: '10:15 AM',
          status: 'Scheduled',
          crates: 10,
          weightKg: 420,
          cargo: 'Fresh Berries & Cream',
          items: [
            { sku: 'FRU-301', name: 'Imported Strawberries Grade A 250g', category: 'Berries', quantity: '6 Crates (120 Punnets)', weight: '30 kg' },
            { sku: 'DAI-502', name: 'Fresh Whipping Cream 250ml', category: 'Dairy', quantity: '4 Crates (80 Units)', weight: '22 kg' }
          ]
        }
      ]
    },
    {
      id: 'VEH016',
      isRecovery: true,
      type: 'Truck',
      refrigeration: 'Reefer',
      activeLeg: 'Trip 1 of 2',
      tripLock: 'Fresh - Kollupitiya Central (Recovery)',
      currentDestination: 'OUT-1044 Kollupitiya',
      startTime: '09:00 AM',
      endTime: '10:30 AM',
      stopsCount: 1,
      tripStatus: 'Staged at Bay 3',
      driverName: 'Nimal Jayasuriya',
      driverPhone: '+94 71 334 5566',
      departureTime: '09:00 AM',
      totalCrates: 14,
      payloadKg: 840,
      stops: [
        {
          id: 'OUT-1044',
          name: 'Kollupitiya Central',
          eta: '09:15 AM',
          status: 'Scheduled',
          crates: 14,
          weightKg: 840,
          cargo: 'Fresh Poultry & Meat',
          items: [
            { sku: 'MEA-105', name: 'Bairaha Chilled Chicken Breasts 500g', category: 'Poultry', quantity: '8 Crates (80 Packs)', weight: '56 kg' },
            { sku: 'MEA-204', name: 'Farm Fresh Chicken Drumsticks', category: 'Poultry', quantity: '6 Crates (60 Packs)', weight: '42 kg' }
          ]
        }
      ]
    }
  ];

  const currentVehicleAssignments = recoveryDeployed
    ? [...recoveryVehicleAssignments, ...vehicleAssignments]
    : vehicleAssignments;

  // Filtered Vehicle Assignments for Workbench
  const filteredVehicleAssignments = currentVehicleAssignments.filter((va) => {
    if (workbenchFilter === 'reefers' && va.refrigeration !== 'Reefer') return false;
    if (workbenchFilter === 'delayed' && !va.tripStatus.includes('Delayed')) return false;
    if (workbenchSearch.trim()) {
      const q = workbenchSearch.toLowerCase().trim();
      return (
        va.id.toLowerCase().includes(q) ||
        va.tripLock.toLowerCase().includes(q) ||
        va.currentDestination.toLowerCase().includes(q) ||
        va.driverName.toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Filtered Outlets for Workbench
  const filteredOutletAssignments = initialOutletAssignments.filter((oa) => {
    if (workbenchSearch.trim()) {
      const q = workbenchSearch.toLowerCase().trim();
      return (
        oa.id.toLowerCase().includes(q) ||
        oa.name.toLowerCase().includes(q) ||
        oa.district.toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Filtered Deferrals
  const filteredDeferrals = initialDeferrals.filter((def) => {
    if (activeNav !== 'Deferral Log') {
      if (deferralCategoryFilter === 'damaged' && def.category !== 'Damaged Goods') return false;
      if (deferralCategoryFilter === 'unavailable' && def.category !== 'Unavailable Goods') return false;
    }
    const currentSearch = activeNav === 'Deferral Log' ? deferralSearch : workbenchSearch;
    if (currentSearch.trim()) {
      const q = currentSearch.toLowerCase().trim();
      return (
        def.orderId.toLowerCase().includes(q) ||
        def.sku.toLowerCase().includes(q) ||
        def.outlet.toLowerCase().includes(q) ||
        def.reason.toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Overview Dataset (Matching Screenshot)
  const peliyagodaOverviewRuns = [
    {
      id: 'ORD-30301',
      vehicle: 'VEH014',
      destination: 'OUT0043 Nugegoda',
      eta: '8:12 AM',
      status: 'Delayed',
      riskNote: 'ETA drifting past 8:00 AM window',
      riskLevel: 'warning',
      category: 'delayed'
    },
    {
      id: 'ORD-30302',
      vehicle: 'VEH014',
      destination: 'OUT0043 Nugegoda',
      eta: '8:05 AM',
      status: 'In Transit',
      riskNote: '—',
      riskLevel: 'normal',
      category: 'active'
    },
    {
      id: 'ORD-30215',
      vehicle: 'VEH041',
      destination: 'Liberty Plaza Mall',
      eta: '10:40 AM',
      status: 'Delayed',
      riskNote: 'Mall window closes 11:00 AM (18 min out)',
      riskLevel: 'danger',
      category: 'delayed'
    },
    {
      id: 'ORD-30188',
      vehicle: 'VEH027',
      destination: 'OUT0091 Kandy',
      eta: '9:15 AM',
      status: 'Offline',
      riskNote: 'No ping for 14 min (Last seen 9:02 AM)',
      riskLevel: 'offline',
      category: 'offline'
    },
    {
      id: 'ORD-30260',
      vehicle: 'VEH009',
      destination: 'OUT0012 Colombo',
      eta: '7:55 AM',
      status: 'At Outlet',
      badge: 'Unloading',
      riskNote: '',
      riskLevel: 'info',
      category: 'outlet'
    },
    {
      id: 'ORD-30099',
      vehicle: 'VEH009',
      destination: 'OUT0055 Colombo',
      eta: '7:20 AM',
      status: 'Completed',
      badge: 'Signed Off',
      riskNote: '',
      riskLevel: 'success',
      category: 'completed'
    }
  ];

  const kandyOverviewRuns = [
    {
      id: 'ORD-40112',
      vehicle: 'VEH102',
      destination: 'OUT0150 Kandy City Center',
      eta: '9:00 AM',
      status: 'In Transit',
      riskNote: '—',
      riskLevel: 'normal',
      category: 'active'
    },
    {
      id: 'ORD-40115',
      vehicle: 'VEH105',
      destination: 'OUT0155 Peradeniya',
      eta: '9:30 AM',
      status: 'Delayed',
      riskNote: 'Traffic near bridge',
      riskLevel: 'warning',
      category: 'delayed'
    },
    {
       id: 'ORD-40220',
       vehicle: 'VEH108',
       destination: 'OUT0160 Katugastota',
       eta: '8:15 AM',
       status: 'Completed',
       badge: 'Signed Off',
       riskNote: '',
       riskLevel: 'success',
       category: 'completed'
    }
  ];

  const overviewRuns = overviewDepot === 'Peliyagoda Depot' ? peliyagodaOverviewRuns : kandyOverviewRuns;

  const filteredOverviewRuns = overviewRuns.filter((run) => {
    if (overviewFilterTab === 'outlet' && run.category !== 'outlet') return false;
    if (overviewFilterTab === 'delayed' && run.category !== 'delayed') return false;
    if (overviewFilterTab === 'offline' && run.category !== 'offline') return false;
    if (overviewFilterTab === 'completed' && run.category !== 'completed') return false;
    if (mapSearch.trim()) {
      const q = mapSearch.toLowerCase().trim();
      return (
        run.id.toLowerCase().includes(q) ||
        run.vehicle.toLowerCase().includes(q) ||
        run.destination.toLowerCase().includes(q) ||
        run.status.toLowerCase().includes(q)
      );
    }
    return true;
  });

  if (showAllocationBoard) {
    return (
      <RouteAllocationBoard
        onBack={() => setShowAllocationBoard(false)}
        fleetList={fleetList}
        onConfirmAllocations={() => {
          setShowAllocationBoard(false);
          setIsAllocationConfirmed(true);
          setShowConfirmToast(true);
          setTimeout(() => {
            setShowConfirmToast(false);
          }, 4000);
          setActiveNav('Route Allocation & Capacity');
          setActiveSubTab('Allocation Workbench');
        }}
      />
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#FAFBFA] text-gray-900 font-sans antialiased pb-12">
      {/* Top Navigation Bar */}
      <header className="w-full border-b border-gray-100 bg-white sticky top-0 z-30 shadow-2xs">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Left: Brand Logo & Navigation Tabs */}
          <div className="flex items-center gap-6 sm:gap-8">
            {/* Waypoint Dispatcher Brand */}
            <div 
              onClick={() => {
                setActiveNav('Route Allocation & Capacity');
                setActiveSubTab(isAllocationConfirmed ? 'Allocation Workbench' : 'Fleet Availability');
              }}
              className="flex items-center gap-2.5 cursor-pointer"
            >
              <img
                src={waypointLogo}
                alt="Waypoint"
                className="w-7 h-7 object-contain rounded-lg shadow-xs"
              />
              <span
                className="text-lg font-bold tracking-tight text-[#0B2019] whitespace-nowrap"
                style={{ fontFamily: "'Inter', sans-serif" }}
              >
                Waypoint Dispatcher
              </span>
            </div>

            {/* Navigation Tabs */}
            <nav className="hidden md:flex items-center gap-1.5" aria-label="Dispatcher Navigation">
              {[
                { name: 'Overview', id: 'Overview' },
                { name: 'Route Allocation & Capacity', id: 'Route Allocation & Capacity' },
                { name: 'Contingency Dispatch', id: 'Contingency Dispatch' },
                { name: 'Deferral Log', id: 'Deferral Log' }
              ].map((tab) => {
                const isActive = activeNav === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => {
                      setActiveNav(tab.id);
                      if (tab.id === 'Route Allocation & Capacity') {
                        setActiveSubTab(isAllocationConfirmed ? 'Allocation Workbench' : 'Fleet Availability');
                      }
                    }}
                    className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer flex items-center gap-1.5 ${
                      isActive
                        ? 'bg-[#E8F7F0] text-[#059669]'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    <span>{tab.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Right: Theme Toggle, Date Selector, Notifications & Profile */}
          <div className="flex items-center gap-2.5">
            {/* Dark Mode Icon Button */}
            <button
              type="button"
              className="w-8 h-8 rounded-full border border-gray-200 hover:border-gray-300 bg-white flex items-center justify-center text-gray-600 hover:text-gray-900 transition-colors cursor-pointer"
              title="Theme Toggle"
            >
              <Moon size={15} strokeWidth={2} />
            </button>

            {/* Date Picker Selector */}
            <div className="relative">
              <button
                type="button"
                className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold text-gray-700 bg-white border border-gray-200 hover:border-gray-300 rounded-full transition-colors cursor-default pointer-events-none"
              >
                <span>Thu, Oct 1</span>
              </button>
            </div>

            {/* Notification Bell */}
            <button
              type="button"
              onClick={() => setHasUnreadNotifications(!hasUnreadNotifications)}
              title="Notifications"
              className="relative w-8 h-8 rounded-full border border-gray-200 hover:border-gray-300 bg-white flex items-center justify-center text-gray-600 hover:text-gray-900 transition-colors cursor-pointer"
            >
              <Bell size={15} strokeWidth={2} />
              {hasUnreadNotifications && (
                <span className="absolute top-1 right-1 w-2 h-2 bg-[#059669] rounded-full ring-2 ring-white" />
              )}
            </button>

            {/* User Profile Avatar */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowUserMenu(!showUserMenu)}
                title="Dispatcher Profile"
                className="w-8 h-8 rounded-full bg-[#E0F2E9] border border-[#C6E7D5] text-[#059669] text-xs font-bold flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity"
              >
                SA
              </button>

              {/* Profile Dropdown */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-52 bg-white border border-gray-100 rounded-xl shadow-lg py-1 z-50">
                  <div className="px-3 py-2 border-b border-gray-100">
                    <p className="text-xs font-medium text-gray-900">Stephan Anthony - Dispatcher</p>
                    <p className="text-[11px] text-gray-500">hub/Peliyagoda</p>
                  </div>
                  <button
                    onClick={() => {
                      setShowUserMenu(false);
                      if (onLogout) onLogout();
                    }}
                    className="w-full text-left px-3 py-2 text-xs text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Confirmation Toast Notification */}
      {showConfirmToast && (
        <div className="fixed top-20 right-6 z-50 bg-[#059669] text-white px-4 py-3 rounded-xl shadow-xl flex items-center gap-2.5 text-xs font-semibold animate-in slide-in-from-top-2">
          <CheckCircle2 size={16} strokeWidth={2.5} />
          <span>Route allocations confirmed & locked for Wave 1!</span>
        </div>
      )}

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-6 py-5 flex flex-col gap-4">
        {/* Universal Top Depot Header & Metrics Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
          {/* Left: Depot Switcher & Inline KPI Metrics */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Depot Dropdown */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowOverviewDepotMenu(!showOverviewDepotMenu)}
                className="inline-flex items-center gap-1.5 text-lg font-bold text-slate-900 hover:text-slate-700 transition cursor-pointer"
              >
                <span>{overviewDepot}</span>
                <ChevronDown size={18} className="text-slate-600 mt-0.5" />
              </button>

              {showOverviewDepotMenu && (
                <div className="absolute left-0 mt-1.5 w-48 bg-white border border-slate-200 rounded-xl shadow-lg py-1 z-30">
                  {['Peliyagoda Depot', 'Kandy Regional Hub'].map((depot) => (
                    <button
                      key={depot}
                      type="button"
                      onClick={() => {
                        setOverviewDepot(depot);
                        setShowOverviewDepotMenu(false);
                      }}
                      className={`w-full text-left px-3.5 py-2 text-xs font-semibold hover:bg-slate-50 transition cursor-pointer ${
                        overviewDepot === depot ? 'text-[#059669] bg-emerald-50/50' : 'text-slate-700'
                      }`}
                    >
                      {depot}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Metric Chips with separators */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              {/* Fleet Utilization Chip */}
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200/90 bg-white shadow-2xs">
                <span className="text-slate-500 font-medium">Fleet Utilization</span>
                <span className="font-bold text-[#059669]">
                  {overviewDepot === 'Peliyagoda Depot' ? '34 / 60 Active' : '12 / 20 Active'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {activeNav === 'Overview' ? (
          <div className="flex flex-col xl:flex-row gap-4 h-[calc(100vh-170px)]">
            {/* Schematic Map Container */}
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden flex flex-col w-full xl:w-[40%] flex-shrink-0">
              {/* Map Header: Title & Vehicle/Route Search */}
              <div className="px-5 py-3.5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <h2 className="text-sm font-bold text-slate-900 tracking-tight">Depot Hub Schematic</h2>

                <div className="relative w-full sm:w-64">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                  <input
                    type="text"
                    value={mapSearch}
                    onChange={(e) => setMapSearch(e.target.value)}
                    placeholder="Search vehicles or routes..."
                    className="w-full pl-8 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#059669] focus:border-[#059669] transition"
                  />
                </div>
              </div>

              {/* Schematic Visual Canvas */}
              <div className="relative flex-1 w-full bg-[#F4F6F4] select-none min-h-[300px]">
                <MapContainer
                  key={overviewDepot}
                  center={overviewDepot === 'Peliyagoda Depot' ? [6.9250, 79.8800] : [7.2906, 80.6337]}
                  zoom={overviewDepot === 'Peliyagoda Depot' ? 12 : 13}
                  zoomControl={false}
                  dragging={false}
                  scrollWheelZoom={false}
                  doubleClickZoom={false}
                  className="absolute inset-0 z-0 opacity-90"
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {selectedMapVehicle && (() => {
                    const seed = selectedMapVehicle.charCodeAt(0) + selectedMapVehicle.charCodeAt(selectedMapVehicle.length - 1);
                    const latOffset = (seed % 10) * 0.005;
                    const lngOffset = (seed % 5) * 0.008;
                    
                    let coords;
                    if (overviewDepot === 'Peliyagoda Depot') {
                      const d = [6.9610, 79.8821];
                      const v = [6.9110 + latOffset, 79.8720 - lngOffset];
                      const o = [6.8649 - latOffset, 79.8997 + lngOffset];
                      coords = { depot: d, vehicle: v, outlet: o, path: [d, [6.9450, 79.8750 - lngOffset], v, [6.8850 + latOffset, 79.8850], o] };
                    } else {
                      const d = [7.2906, 80.6337];
                      const v = [7.2800 - latOffset, 80.6150 + lngOffset];
                      const o = [7.2700 + latOffset, 80.6000 - lngOffset];
                      coords = { depot: d, vehicle: v, outlet: o, path: [d, [7.2850, 80.6250], v, [7.2750, 80.6050], o] };
                    }
                    
                    const bounds = L.latLngBounds([coords.depot, coords.outlet, coords.vehicle]);
                    
                    return (
                      <>
                        <RoadRoutePolyline points={coords.path} />
                        <Marker position={coords.depot} icon={createDepotIcon(overviewDepot)} />
                        <Marker position={coords.outlet} icon={createOutletIcon('Target Outlet')} />
                        <Marker position={coords.vehicle} icon={createVehicleIcon(selectedMapVehicle)} />
                        <FitBounds bounds={bounds} />
                      </>
                    );
                  })()}
                </MapContainer>
                
                {/* Map Legend (Bottom-Left Overlay) */}
                <div className="absolute bottom-4 left-4 z-10 bg-white/90 backdrop-blur-xs rounded-lg border border-slate-200 shadow-2xs px-3 py-2 text-left">
                  <div className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">MAP LEGEND</div>
                  <div className="flex items-center gap-3 text-[11px] font-medium text-slate-700">
                    <span className="inline-flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      On Time
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-amber-500" />
                      Delayed
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-slate-500" />
                      Offline
                    </span>
                  </div>
                </div>

                {/* Zoom Controls (Bottom-Right Overlay) */}
                <div className="absolute bottom-4 right-4 z-10 bg-white rounded-lg border border-slate-200 shadow-2xs flex flex-col overflow-hidden">
                  <button
                    type="button"
                    title="Zoom In"
                    className="w-7 h-7 flex items-center justify-center text-slate-700 hover:bg-slate-50 transition border-b border-slate-100 cursor-pointer"
                  >
                    <Plus size={14} />
                  </button>
                  <button
                    type="button"
                    title="Zoom Out"
                    className="w-7 h-7 flex items-center justify-center text-slate-700 hover:bg-slate-50 transition cursor-pointer"
                  >
                    <Minus size={14} />
                  </button>
                </div>
              </div>
            </div>

            {/* Live Runs Table Container */}
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col w-full xl:w-[60%] overflow-hidden">
              {/* Filter Tabs & Sort Controls */}
              <div className="px-5 py-3.5 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
                {/* Filter Pills */}
                <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                  {[
                    { id: 'all', label: 'All active (34)' },
                    { id: 'outlet', label: 'At outlet (8)' },
                    { id: 'delayed', label: 'Delayed active (3)' },
                    { id: 'offline', label: 'Offline' },
                    { id: 'completed', label: 'Completed (26)' }
                  ].map((tab) => {
                    const isActive = overviewFilterTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        type="button"
                        onClick={() => setOverviewFilterTab(tab.id)}
                        className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                          isActive
                            ? 'bg-[#E8F7F0] text-[#059669] border border-[#C6E7D5]'
                            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                        }`}
                      >
                        {tab.label}
                      </button>
                    );
                  })}
                </div>

                {/* Right Controls: Sort & Filter */}
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <button
                      type="button"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-700 hover:bg-slate-50 transition cursor-pointer"
                    >
                      <span className="text-slate-500">Sort by:</span>
                      <span className="font-semibold text-slate-800">ETA priority</span>
                      <ChevronDown size={13} className="text-slate-400" />
                    </button>
                  </div>

                  <button
                    type="button"
                    title="Filter Options"
                    className="w-8 h-8 rounded-lg border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-50 transition cursor-pointer"
                  >
                    <Filter size={14} />
                  </button>
                </div>
              </div>

              {/* Table */}
              <div className="flex-1 overflow-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-100 bg-slate-50/50 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      <th className="py-3 px-5">RUN / ID</th>
                      <th className="py-3 px-4">VEHICLE</th>
                      <th className="py-3 px-4">DESTINATION</th>
                      <th className="py-3 px-4">ETA / SCHEDULED STATUS</th>
                      <th className="py-3 px-5">DISPATCH RISK NOTES</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-xs">
                    {filteredOverviewRuns.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-slate-400 italic">
                          No runs match the selected filter.
                        </td>
                      </tr>
                    ) : (
                      filteredOverviewRuns.map((run) => (
                        <tr
                          key={run.id}
                          onClick={() => setSelectedMapVehicle(run.vehicle)}
                          className={`hover:bg-slate-50/70 transition-colors cursor-pointer ${
                            selectedMapVehicle === run.vehicle ? 'bg-emerald-50/30' : ''
                          }`}
                        >
                          {/* RUN / ID */}
                          <td className="py-3 px-5 font-bold font-mono text-slate-900">
                            {run.id}
                          </td>

                          {/* VEHICLE */}
                          <td className="py-3 px-4 text-slate-500 font-medium">
                            {run.vehicle}
                          </td>

                          {/* DESTINATION */}
                          <td className="py-3 px-4 font-bold text-slate-800">
                            {run.destination}
                          </td>

                          {/* ETA / SCHEDULED STATUS */}
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-slate-800">{run.eta}</span>
                              {run.status === 'Delayed' && (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                                  Delayed
                                </span>
                              )}
                              {run.status === 'In Transit' && (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-50 text-sky-700 border border-sky-200">
                                  In Transit
                                </span>
                              )}
                              {run.status === 'Offline' && (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                                  Offline
                                </span>
                              )}
                              {run.status === 'At Outlet' && (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-50 text-sky-700 border border-sky-200">
                                  At Outlet
                                </span>
                              )}
                              {run.status === 'Completed' && (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                  Completed
                                </span>
                              )}
                            </div>
                          </td>

                          {/* DISPATCH RISK NOTES */}
                          <td className="py-3 px-5">
                            {run.badge === 'Unloading' && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
                                Unloading
                              </span>
                            )}
                            {run.badge === 'Signed Off' && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                                Signed Off
                              </span>
                            )}
                            {run.riskLevel === 'warning' && (
                              <span className="inline-flex items-center gap-1.5 text-amber-600 font-medium">
                                <AlertTriangle size={13} className="text-amber-500 flex-shrink-0" />
                                <span>{run.riskNote}</span>
                              </span>
                            )}
                            {run.riskLevel === 'danger' && (
                              <span className="inline-flex items-center gap-1.5 text-rose-600 font-medium">
                                <AlertCircle size={13} className="text-rose-500 flex-shrink-0" />
                                <span>{run.riskNote}</span>
                              </span>
                            )}
                            {run.riskLevel === 'offline' && (
                              <span className="text-slate-500 font-normal">
                                {run.riskNote}
                              </span>
                            )}
                            {run.riskLevel === 'normal' && (
                              <span className="text-slate-300">—</span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : activeNav === 'Contingency Dispatch' ? (
          /* ======================================================= */
          /* CONTINGENCY DISPATCH (MID-SHIFT DISRUPTION & RECOVERY)  */
          /* ======================================================= */
          <div className="flex flex-col gap-4">
            {/* Top Bar: Hub + Summary Strip + Action Button */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pt-1">
              <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">
                {/* Hub Pill */}
                <div className="inline-flex rounded-xl bg-slate-100 p-0.5 border border-slate-200/60 shadow-2xs">
                  <span className="px-3 py-1.5 rounded-lg text-xs font-bold bg-white text-slate-900 shadow-2xs">
                    Peliyagoda Hub
                  </span>
                </div>

                {/* Status Badges */}
                {!recoveryDeployed ? (
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold bg-[#FFF1F2] text-[#BE123C] border border-[#FECDD3]">
                      <AlertTriangle size={12} className="text-[#BE123C]" />
                      <span>2 Vehicle Breakdowns</span>
                    </div>
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold bg-[#FEF6EE] text-[#B45309] border border-[#FBE3CC]">
                      <span>1 Damaged at POD</span>
                    </div>
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold bg-[#EBF5FB] text-[#0284C7] border border-[#CCE5F7]">
                      <span>4 Orders Disrupted (1,730 kg)</span>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold bg-[#EAF7EE] text-[#059669] border border-[#D1F2DD]">
                      <CheckCircle2 size={13} className="text-[#059669]" />
                      <span>Recovery Plan v2 Active</span>
                    </div>
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold bg-[#EBF5FB] text-[#0284C7] border border-[#CCE5F7]">
                      <span>3 Recovery Trips Underway</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Action on Right */}
              <div className="flex items-center gap-2.5">
                {!recoveryDeployed ? (
                  <button
                    type="button"
                    onClick={() => setShowRecoveryModal(true)}
                    className="inline-flex items-center justify-center gap-2 bg-[#059669] hover:bg-[#047857] active:bg-[#065F46] text-white text-xs font-semibold px-4 py-2.5 rounded-lg transition-all shadow-xs cursor-pointer flex-shrink-0"
                  >
                    <span>Start Recovery Plan</span>
                    <ArrowRight size={14} />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setRecoveryDeployed(false);
                      setShowRecoveryModal(false);
                    }}
                    className="inline-flex items-center justify-center gap-1.5 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-xs font-semibold px-3 py-2 rounded-lg transition shadow-2xs cursor-pointer"
                    title="Simulate / Re-evaluate breakdown incident"
                  >
                    <RotateCcw size={13} />
                    <span>Reset Incident Demo</span>
                  </button>
                )}
              </div>
            </div>

            {/* Sub-header Banner */}
            {!recoveryDeployed ? (
              <div className="w-full bg-[#FFF1F2] border border-[#FECDD3] rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-[#881337] shadow-2xs animate-in fade-in">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-rose-100 border border-rose-200 flex items-center justify-center flex-shrink-0 text-[#BE123C]">
                    <AlertTriangle size={16} />
                  </div>
                  <div>
                    <strong className="font-bold text-[#4C0519]">Mid-shift disruption detected: </strong>
                    <span>VEH011 broke down during dock staging (Bay 3) and VEH006 disabled en route. Damaged pallets reported at OUT-2041. Review orders below and launch the recovery plan.</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="w-full bg-[#EAF7EE] border border-[#D1F2DD] rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-[#065F46] shadow-2xs animate-in fade-in">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-emerald-100 border border-emerald-200 flex items-center justify-center flex-shrink-0 text-[#059669]">
                    <CheckCircle2 size={16} />
                  </div>
                  <div>
                    <strong className="font-bold text-[#0B2019]">Recovery Plan v2 is actively executing: </strong>
                    <span>3 recovered orders have been re-slotted onto open vehicle capacity. Updated manifests pushed to mobile apps. Active trips in progress below:</span>
                  </div>
                </div>
              </div>
            )}

            {/* Rows Table */}
            <div className="w-full bg-white border border-gray-200/80 rounded-2xl shadow-xs overflow-hidden">
              {!recoveryDeployed ? (
                /* PRE-RECOVERY: Disrupted / Deferred Orders Rows */
                <div className="divide-y divide-gray-100">
                  {contingencyDisruptedOrders.map((order) => {
                    const isExpanded = expandedContingencyIds.has(order.id);
                    return (
                      <div key={order.id} className="transition">
                        <div 
                          onClick={() => {
                            setExpandedContingencyIds(prev => {
                              const next = new Set(prev);
                              if (next.has(order.id)) next.delete(order.id);
                              else next.add(order.id);
                              return next;
                            });
                          }}
                          className="flex items-center justify-between px-6 py-4 hover:bg-slate-50/70 transition cursor-pointer select-none bg-white"
                        >
                          {/* Col 1: Order ID + Incident Vehicle + Refrigeration */}
                          <div className="flex items-center gap-2.5 w-60 flex-shrink-0">
                            <span className="font-bold text-slate-900 text-xs font-sans tracking-tight">
                              {order.id}
                            </span>
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-700">
                              {order.incidentVehicle} ({order.type})
                            </span>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              order.refrigeration === 'Reefer'
                                ? 'bg-[#E0F2FE] text-[#0284C7] border border-[#BAE6FD]'
                                : 'bg-slate-100 text-slate-600 border border-slate-200'
                            }`}>
                              {order.refrigeration}
                            </span>
                          </div>

                          {/* Col 2: Incident label */}
                          <div className="w-36 flex-shrink-0">
                            <span className="font-bold text-slate-900 text-xs">
                              {order.tripLabel}
                            </span>
                          </div>

                          {/* Col 3: Cargo description */}
                          <div className="w-52 text-slate-500 text-xs truncate flex-shrink-0">
                            {order.cargoLine}
                          </div>

                          {/* Col 4: Reason Pill */}
                          <div className="flex-shrink-0">
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-[#EDF2F7] text-slate-600">
                              {order.reasonPill.includes('Breakdown') ? (
                                <AlertTriangle size={12} className="text-amber-500" />
                              ) : (
                                <Package size={12} className="text-rose-500" />
                              )}
                              <span>{order.reasonPill}</span>
                            </span>
                          </div>

                          {/* Col 5: Destination */}
                          <div className="w-52 flex-shrink-0">
                            <span className="font-bold text-slate-900 text-xs">
                              {order.destination}
                            </span>
                          </div>

                          {/* Col 6: Logged Time */}
                          <div className="flex items-center gap-1.5 text-slate-700 text-xs font-medium flex-shrink-0">
                            <Clock size={13} className="text-slate-400" />
                            <span className="font-mono font-bold">{order.reportedTime}</span>
                          </div>

                          {/* Col 7: Chevron */}
                          <div className="flex-shrink-0 text-slate-400">
                            {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                          </div>
                        </div>

                        {/* Expanded details */}
                        {isExpanded && (
                          <div className="px-6 py-3.5 bg-slate-50/60 border-t border-slate-100 text-xs text-slate-600 flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-in fade-in">
                            <div className="space-y-1">
                              <p><strong className="text-slate-900">Incident Details:</strong> {order.reasonDetail}</p>
                              <p><strong className="text-slate-900">Reported By:</strong> {order.driver} · <span className="text-amber-700 font-semibold">{order.freshWindow}</span></p>
                            </div>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                setShowRecoveryModal(true);
                              }}
                              className="text-xs font-bold text-[#059669] hover:underline whitespace-nowrap self-end sm:self-center cursor-pointer"
                            >
                              Re-allocate in Recovery Plan →
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                /* POST-RECOVERY: Exact Trips Going on Trips (Matching Screenshot!) */
                <div className="divide-y divide-gray-100">
                  {contingencyActiveTrips.map((trip) => {
                    const isExpanded = expandedActiveTripIds.has(trip.vehicleId);
                    return (
                      <div key={trip.vehicleId} className="transition">
                        <div 
                          onClick={() => {
                            setExpandedActiveTripIds(prev => {
                              const next = new Set(prev);
                              if (next.has(trip.vehicleId)) next.delete(trip.vehicleId);
                              else next.add(trip.vehicleId);
                              return next;
                            });
                          }}
                          className="flex items-center justify-between px-6 py-4 hover:bg-slate-50/70 transition cursor-pointer select-none bg-white"
                        >
                          {/* Col 1: Vehicle ID + Van/Truck + Reefer/Ambient */}
                          <div className="flex items-center gap-3 w-56 flex-shrink-0">
                            <span className="font-bold text-slate-900 text-sm font-sans tracking-tight">
                              {trip.vehicleId}
                            </span>
                            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                              {trip.type}
                            </span>
                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                              trip.refrigeration === 'Reefer'
                                ? 'bg-[#E0F2FE] text-[#0284C7] border border-[#BAE6FD]'
                                : 'bg-slate-100 text-slate-600 border border-slate-200'
                            }`}>
                              {trip.refrigeration}
                            </span>
                          </div>

                          {/* Col 2: Trip Label (e.g. Trip 1 of 2) */}
                          <div className="w-32 flex-shrink-0">
                            <span className="font-bold text-slate-900 text-sm">
                              {trip.tripLabel}
                            </span>
                          </div>

                          {/* Col 3: Cargo Line (e.g. Fresh - Colombo Central) */}
                          <div className="w-48 text-slate-500 text-sm truncate flex-shrink-0">
                            {trip.cargoLine}
                          </div>

                          {/* Col 4: Stops count pill (e.g. 5 Stops) */}
                          <div className="flex-shrink-0">
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-[#EDF2F7] text-slate-600">
                              <MapPin size={12} className="text-slate-400" />
                              <span>{trip.stopsCount} Stops</span>
                            </span>
                          </div>

                          {/* Col 5: Destination (e.g. OUT-4089 Nugegoda) */}
                          <div className="w-48 flex-shrink-0">
                            <span className="font-bold text-slate-900 text-sm">
                              {trip.destination}
                            </span>
                          </div>

                          {/* Col 6: Scheduled Time Window (e.g. 07:45 AM - 11:15 AM) */}
                          <div className="flex items-center gap-2 text-slate-700 text-xs font-medium flex-shrink-0">
                            <Clock size={13} className="text-slate-400" />
                            <span className="font-mono font-bold">{trip.timeWindow}</span>
                          </div>

                          {/* Col 7: Chevron Toggle */}
                          <div className="flex-shrink-0 text-slate-400">
                            {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                          </div>
                        </div>

                        {/* Expanded Stop Manifest */}
                        {isExpanded && (
                          <div className="px-6 py-3.5 bg-slate-50/70 border-t border-slate-100 text-xs space-y-2 animate-in fade-in">
                            <span className="font-bold text-slate-800 uppercase tracking-wider text-[11px] block">
                              Active Stop Manifest & Recovered Cargo
                            </span>
                            <div className="space-y-1.5">
                              {trip.stopList.map((stopItem) => (
                                <div key={stopItem.stop} className="flex items-center justify-between text-xs py-1 border-b border-slate-200/50 last:border-0">
                                  <div className="flex items-center gap-2">
                                    <span className="w-5 h-5 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-bold text-[10px]">
                                      {stopItem.stop}
                                    </span>
                                    <span className="font-semibold text-slate-800">{stopItem.name}</span>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <span className="text-slate-500 font-mono">{stopItem.time}</span>
                                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                                      stopItem.status.includes('Recovered')
                                        ? 'bg-amber-50 text-amber-800 border border-amber-200'
                                        : stopItem.status === 'Completed'
                                        ? 'bg-emerald-50 text-emerald-700'
                                        : 'bg-sky-50 text-sky-700'
                                    }`}>
                                      {stopItem.status}
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ) : activeNav === 'Deferral Log' ? (
          /* ======================================================= */
          /* DEDICATED DEFERRAL LOG PAGE (JUST SEARCH BAR + TABLE)   */
          /* ======================================================= */
          <div className="flex flex-col gap-4">
            {/* Search bar for deferrals */}
            <div className="flex items-center justify-between gap-3 pt-1">
              <div className="relative w-full sm:w-80">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  type="text"
                  value={deferralSearch}
                  onChange={(e) => setDeferralSearch(e.target.value)}
                  placeholder="Filter deferrals by SKU or outlet..."
                  className="w-full h-9 pl-9 pr-3 text-xs font-medium text-slate-900 bg-white border border-gray-200 rounded-lg placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#059669] focus:border-transparent transition shadow-2xs"
                />
              </div>
            </div>

            {/* Deferrals Log Table */}
            <div className="w-full bg-white border border-gray-200/80 rounded-2xl shadow-xs overflow-hidden">
              <div className="p-4 border-b border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <span>Unassigned & Deferred Items Log</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                      {filteredDeferrals.length} Items Flagged
                    </span>
                  </h2>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Orders excluded from wave dispatch due to damaged staging or stock shortages.
                  </p>
                </div>

                <div className="text-[11px] text-slate-600">
                  Total Deferred Quantity: <strong className="text-slate-900">280 kg / 340 units</strong>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-[#F8FAFC] text-slate-500 font-semibold border-b border-gray-200/70 select-none">
                      <th className="py-3 px-4">ORDER ID</th>
                      <th className="py-3 px-4">PRODUCT / SKU</th>
                      <th className="py-3 px-4">TARGET OUTLET</th>
                      <th className="py-3 px-4">QUANTITY</th>
                      <th className="py-3 px-4">DEFERRAL CATEGORY</th>
                      <th className="py-3 px-4">SPECIFIC REASON</th>
                      <th className="py-3 px-4">ACTION & RESOLUTION</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredDeferrals.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-slate-400 italic">
                          No deferred items match your search.
                        </td>
                      </tr>
                    ) : (
                      filteredDeferrals.map((def) => (
                        <tr key={def.id} className="hover:bg-slate-50/60 transition">
                          <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                            {def.orderId}
                          </td>
                          <td className="py-3.5 px-4 font-medium text-slate-800">
                            {def.sku}
                          </td>
                          <td className="py-3.5 px-4 text-slate-600">
                            {def.outlet}
                          </td>
                          <td className="py-3.5 px-4 font-mono font-semibold text-slate-800">
                            {def.quantity}
                          </td>
                          <td className="py-3.5 px-4">
                            {def.category === 'Damaged Goods' ? (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                                <AlertTriangle size={11} />
                                <span>Damaged Goods</span>
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                                <AlertCircle size={11} />
                                <span>Unavailable Goods</span>
                              </span>
                            )}
                          </td>
                          <td className="py-3.5 px-4 text-slate-600 max-w-xs">
                            <p className="leading-snug text-[11px]">{def.reason}</p>
                            <span className="text-[10px] text-slate-400 mt-0.5 block">
                              By {def.reportedBy} at {def.loggedAt}
                            </span>
                          </td>
                          <td className="py-3.5 px-4">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                              {def.resolution}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* ======================================================= */}
            {/* SUB-TAB 2: ALLOCATION WORKBENCH (PROPOSED ASSIGNMENTS)    */}
            {/* ======================================================= */}
            {activeSubTab === 'Allocation Workbench' ? (
              <div className="flex flex-col gap-4">
                {/* Workbench Top Bar: Hubs + Segment Bar + Search + Filters */}
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pt-1">
                  {/* Left: Hub Switcher & Segment Bar */}
                  <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">
                    {/* Back to Fleet Availability (Hidden once routes are confirmed) */}
                    {!isAllocationConfirmed && (
                      <button
                        type="button"
                        onClick={() => setActiveSubTab('Fleet Availability')}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
                        title="Back to Fleet Availability"
                      >
                        <ArrowLeft size={13} />
                        <span>Fleet Availability</span>
                      </button>
                    )}

                    {/* Hub Selector */}

                    {/* Workbench Segment Bar: View by Vehicle / View by Outlet / Deferrals */}
                    <div className="inline-flex rounded-xl bg-slate-100 p-0.5 border border-slate-200/60 shadow-2xs">
                      <button
                        type="button"
                        onClick={() => {
                          if (activeNav === 'Deferral Log') setActiveNav('Route Allocation & Capacity');
                          setWorkbenchView('vehicle');
                        }}
                        className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                          workbenchView === 'vehicle'
                            ? 'bg-[#059669] text-white shadow-2xs'
                            : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        View by Vehicle
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          if (activeNav === 'Deferral Log') setActiveNav('Route Allocation & Capacity');
                          setWorkbenchView('outlet');
                        }}
                        className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                          workbenchView === 'outlet'
                            ? 'bg-[#059669] text-white shadow-2xs'
                            : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        View by Outlet
                      </button>
                      <button
                        type="button"
                        onClick={() => setWorkbenchView('deferrals')}
                        className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                          workbenchView === 'deferrals'
                            ? 'bg-[#059669] text-white shadow-2xs'
                            : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        Deferrals ({initialDeferrals.length})
                      </button>
                    </div>
                  </div>

                  {/* Right: Search & View Filters */}
                  <div className="flex flex-wrap items-center gap-2.5">
                    {/* Search Bar */}
                    <div className="relative w-full sm:w-64">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                      <input
                        type="text"
                        value={workbenchSearch}
                        onChange={(e) => setWorkbenchSearch(e.target.value)}
                        placeholder={
                          workbenchView === 'vehicle'
                            ? 'Filter by vehicle ID or district...'
                            : workbenchView === 'outlet'
                            ? 'Filter by outlet code or name...'
                            : 'Filter deferrals by SKU or outlet...'
                        }
                        className="w-full h-8.5 pl-9 pr-3 text-xs font-medium text-slate-900 bg-white border border-gray-200 rounded-lg placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#059669] focus:border-transparent transition shadow-2xs"
                      />
                    </div>

                    {/* Filter Chips for Vehicle View */}
                    {workbenchView === 'vehicle' ? (
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => setWorkbenchFilter('all')}
                          className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                            workbenchFilter === 'all'
                              ? 'bg-slate-900 text-white shadow-2xs'
                              : 'bg-white border border-gray-200 text-slate-600 hover:bg-slate-50'
                          }`}
                        >
                          All
                        </button>
                        <button
                          type="button"
                          onClick={() => setWorkbenchFilter('reefers')}
                          className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                            workbenchFilter === 'reefers'
                              ? 'bg-slate-900 text-white shadow-2xs'
                              : 'bg-white border border-gray-200 text-slate-600 hover:bg-slate-50'
                          }`}
                        >
                          Reefers Only
                        </button>
                        <button
                          type="button"
                          onClick={() => setWorkbenchFilter('delayed')}
                          className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                            workbenchFilter === 'delayed'
                              ? 'bg-slate-900 text-white shadow-2xs'
                              : 'bg-white border border-gray-200 text-slate-600 hover:bg-slate-50'
                          }`}
                        >
                          Delayed Only
                        </button>
                      </div>
                    ) : workbenchView === 'deferrals' ? (
                      /* Filter Chips for Deferrals */
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => setDeferralCategoryFilter('all')}
                          className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                            deferralCategoryFilter === 'all'
                              ? 'bg-slate-900 text-white shadow-2xs'
                              : 'bg-white border border-gray-200 text-slate-600 hover:bg-slate-50'
                          }`}
                        >
                          All ({initialDeferrals.length})
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeferralCategoryFilter('damaged')}
                          className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                            deferralCategoryFilter === 'damaged'
                              ? 'bg-amber-600 text-white shadow-2xs'
                              : 'bg-white border border-amber-200 text-amber-700 hover:bg-amber-50'
                          }`}
                        >
                          Damaged Goods (3)
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeferralCategoryFilter('unavailable')}
                          className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                            deferralCategoryFilter === 'unavailable'
                              ? 'bg-rose-600 text-white shadow-2xs'
                              : 'bg-white border border-rose-200 text-rose-700 hover:bg-rose-50'
                          }`}
                        >
                          Unavailable Goods (2)
                        </button>
                      </div>
                    ) : null}
                  </div>
                </div>

                {/* Metrics Summary Strip with Green Confirm Button */}
                <div className="w-full py-1 flex flex-col md:flex-row md:items-center justify-between gap-3">
                  {/* Summary Metric Badges */}
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-xs">
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold bg-[#EAF6EE] text-[#059669] border border-[#CDEBD8]">
                      <span className="font-normal text-[#059669]/90">Allocated Fleet:</span>
                      <span className="font-bold">14 Vehicles Active</span>
                    </div>

                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold bg-[#EBF5FB] text-[#0284C7] border border-[#CCE5F7]">
                      <span className="font-normal text-[#0284C7]/90">Coverage:</span>
                      <span className="font-bold">24 Outlets Scheduled</span>
                    </div>

                    <span className="text-slate-300 hidden sm:inline">•</span>

                    <div className="flex items-center gap-1.5 text-slate-600">
                      <span className="font-normal">Total Weight:</span>
                      <span className="font-mono font-bold text-slate-900">42,800 kg</span>
                    </div>

                    <span className="text-slate-300 hidden sm:inline">•</span>

                    <div className="flex items-center gap-1.5 text-slate-600">
                      <span className="font-normal">Pending Deferrals:</span>
                      <span className="font-mono font-bold text-rose-600">5 Items</span>
                    </div>
                  </div>

                  {/* Green Confirm Button (In-place Confirmation) - Hidden in Deferral Logs */}
                  {workbenchView !== 'deferrals' && (
                    <button
                      type="button"
                      onClick={handleConfirmRouteAllocation}
                      className={`inline-flex items-center justify-center gap-2 text-white text-xs font-bold px-5 py-2.5 rounded-lg transition-all shadow-xs cursor-pointer flex-shrink-0 ${
                        isAllocationConfirmed
                          ? 'bg-[#047857] hover:bg-[#065F46]'
                          : 'bg-[#059669] hover:bg-[#047857] active:bg-[#065F46]'
                      }`}
                    >
                      <Check size={14} strokeWidth={3} />
                      <span>{isAllocationConfirmed ? 'Route Allocation Confirmed' : 'Confirm Route Allocation'}</span>
                    </button>
                  )}
                </div>

                {/* In-place Confirmation Notice if confirmed - Hidden in Deferral Logs */}
                {isAllocationConfirmed && workbenchView !== 'deferrals' && (
                  <div className="w-full bg-[#EAF7EE] border border-[#CDEED6] rounded-xl px-4 py-2.5 flex items-center justify-between text-xs text-[#065F46] animate-in fade-in">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 size={16} className="text-[#059669]" />
                      <span className="font-semibold">
                        Route allocations confirmed & locked for Wave 1. Dispatches active.
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-[#059669] font-medium">Wave 1 Confirmed</span>
                  </div>
                )}

                {/* =================================================== */}
                {/* 1. VIEW BY VEHICLE (EXACT MATCH TO USER SCREENSHOT) */}
                {/* =================================================== */}
                {workbenchView === 'vehicle' && (
                  <div className="flex flex-col gap-3">
                    {/* Disruption Banner on Confirmed Screen (Matching User's Attached Screenshot) */}
                    {!recoveryDeployed ? (
                      <div className="w-full bg-[#FFF1F2] border border-[#FECDD3] rounded-2xl p-3 sm:px-5 sm:py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs animate-in fade-in">
                        <div className="flex items-center gap-3.5">
                          <div className="w-9 h-9 rounded-xl bg-rose-100/80 border border-rose-200/90 flex items-center justify-center flex-shrink-0 text-[#BE123C]">
                            <AlertTriangle size={18} strokeWidth={2.2} />
                          </div>
                          <div className="text-xs text-[#881337] leading-relaxed">
                            <span>2 vehicles lost since Plan v1 · </span>
                            <strong className="font-mono font-bold text-[#4C0519]">VEH011</strong>
                            <span> (at dock, cargo staged) · </span>
                            <strong className="font-mono font-bold text-[#4C0519]">VEH006</strong>
                            <span> (en route, 4 stops undelivered) · </span>
                            <strong className="font-bold text-[#4C0519]">5 orders · 3,270 kg unassigned</strong>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => setShowRecoveryModal(true)}
                          className="inline-flex items-center justify-center gap-2 bg-[#059669] hover:bg-[#047857] active:bg-[#065F46] text-white text-xs font-bold px-4 py-2 rounded-xl transition-all shadow-xs cursor-pointer flex-shrink-0"
                        >
                          <span>Start Recovery Plan</span>
                          <ArrowRight size={14} />
                        </button>
                      </div>
                    ) : (
                      <div className="w-full bg-[#EAF7EE] border border-[#CDEED6] rounded-2xl p-3 sm:px-5 sm:py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-[#065F46] shadow-2xs animate-in fade-in">
                        <div className="flex items-center gap-2.5">
                          <CheckCircle2 size={18} className="text-[#059669] flex-shrink-0" />
                          <span className="font-semibold">
                            Recovery Plan v2 active · 3 recovered orders placed in open slots (VEH014 & VEH016) · Loader, Driver and Store Managers notified.
                          </span>
                        </div>
                        <span className="text-[11px] font-mono font-bold text-[#059669] bg-white px-2.5 py-1 rounded-lg border border-[#CDEED6]">
                          Recovery Deployed
                        </span>
                      </div>
                    )}

                    <div className="w-full bg-white border border-gray-200/80 rounded-2xl shadow-xs overflow-hidden">
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead>
                            <tr className="bg-[#F8FAFC] text-slate-500 font-semibold border-b border-gray-200/70 select-none">
                              <th className="py-3 px-4">VEHICLE ID</th>
                              <th className="py-3 px-4">ACTIVE LEG</th>
                              <th className="py-3 px-4">TRIP LOCK</th>
                              <th className="py-3 px-4">STOPS</th>
                              <th className="py-3 px-4">CURRENT DESTINATION</th>
                              <th className="py-3 px-4">TRIP TIME</th>
                              <th className="py-3 px-4 text-right">ACTIONS</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {filteredVehicleAssignments.map((va) => {
                              const isExpanded = expandedVehicleIds.has(va.id);

                              return (
                                <React.Fragment key={`${va.id}-${va.activeLeg}`}>
                                  <tr
                                    onClick={() => toggleVehicleExpand(va.id)}
                                    className={`transition-colors cursor-pointer ${
                                      isExpanded ? 'bg-slate-50/80' : 'hover:bg-slate-50/60'
                                    }`}
                                  >
                                    {/* VEHICLE ID + TYPE + REFRIGERATION */}
                                    <td className="py-3.5 px-4">
                                      <div className="flex items-center gap-2">
                                        <span className="font-mono font-bold text-slate-900 text-xs">
                                          {va.id}
                                        </span>
                                        {va.isRecovery && (
                                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                                            Recovery
                                          </span>
                                        )}
                                        <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700">
                                          {va.type}
                                        </span>
                                        {va.refrigeration === 'Reefer' ? (
                                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-sky-50 text-sky-700 border border-sky-200">
                                            Reefer
                                          </span>
                                        ) : (
                                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-50 text-slate-600 border border-slate-200">
                                            Ambient
                                          </span>
                                        )}
                                      </div>
                                    </td>

                                  {/* ACTIVE LEG */}
                                  <td className="py-3.5 px-4 font-bold text-slate-900">
                                    {va.activeLeg}
                                  </td>

                                  {/* TRIP LOCK */}
                                  <td className="py-3.5 px-4 text-slate-700 font-medium">
                                    {va.tripLock}
                                  </td>

                                  {/* STOPS (NUMBER OF STOPS) */}
                                  <td className="py-3.5 px-4 font-semibold text-slate-800">
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 text-slate-800 text-xs font-semibold">
                                      <MapPin size={12} className="text-slate-500" />
                                      <span>{va.stops ? va.stops.length : va.stopsCount} Stops</span>
                                    </span>
                                  </td>

                                  {/* CURRENT DESTINATION */}
                                  <td className="py-3.5 px-4 font-bold text-slate-900">
                                    {va.currentDestination}
                                  </td>

                                  {/* TRIP TIME (START AND END TIME) */}
                                  <td className="py-3.5 px-4">
                                    <div className="flex items-center gap-1.5 font-mono text-xs font-semibold text-slate-800">
                                      <Clock size={13} className="text-slate-400" />
                                      <span>{va.startTime} – {va.endTime}</span>
                                    </div>
                                  </td>

                                  {/* ACTIONS TOGGLE CHEVRON */}
                                  <td className="py-3.5 px-4 text-right">
                                    <button
                                      type="button"
                                      className="p-1 text-slate-400 hover:text-slate-700 rounded-md transition"
                                      title={isExpanded ? 'Collapse stops' : 'View stops'}
                                    >
                                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                    </button>
                                  </td>
                                </tr>

                                {/* Expandable Dropdown Card with Sequential Stops and Shop Items */}
                                {isExpanded && (
                                  <tr className="bg-slate-50/70 border-t border-b border-slate-200/70">
                                    <td colSpan={7} className="px-6 py-4">
                                      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs">
                                        {/* Dropdown Card Header */}
                                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 mb-3 border-b border-slate-100">
                                          <div className="flex items-center gap-2">
                                            <span className="text-xs font-bold text-slate-900">
                                              {va.id} · {va.activeLeg} Route Sequence Manifest
                                            </span>
                                            <span className="text-slate-300">•</span>
                                            <span className="text-xs text-slate-600">
                                              Driver: <strong className="text-slate-800">{va.driverName}</strong> ({va.driverPhone})
                                            </span>
                                          </div>
                                          <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
                                            <span>Trip Time: <strong className="text-slate-800">{va.startTime} – {va.endTime}</strong></span>
                                            <span>•</span>
                                            <span>Total Load: <strong className="text-slate-800">{va.totalCrates} crates ({va.payloadKg} kg)</strong></span>
                                          </div>
                                        </div>

                                        {/* Sequential List of Outlets (One by One) */}
                                        <div className="flex flex-col gap-2.5">
                                          <div className="flex items-center justify-between px-1">
                                            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                                              Assigned Outlet Stops ({va.stops.length} Outlets)
                                            </span>
                                            <span className="text-[11px] text-slate-400">
                                              Click dropdown on any outlet to inspect shop items
                                            </span>
                                          </div>

                                          {va.stops.map((stop, sIdx) => {
                                            const isStopExpanded = expandedStopIds.has(`${va.id}-${stop.id}`);
                                            const isDone = stop.status === 'Completed';
                                            const isCurrent = stop.status === 'En Route' || stop.status === 'At Dock - Unloading' || stop.status === 'Delayed';

                                            return (
                                              <div
                                                key={stop.id}
                                                className={`rounded-xl border transition-all overflow-hidden ${
                                                  isStopExpanded
                                                    ? 'bg-white border-emerald-300 shadow-xs ring-1 ring-emerald-500/20'
                                                    : isCurrent
                                                    ? 'bg-white border-emerald-200 shadow-2xs'
                                                    : isDone
                                                    ? 'bg-slate-50/70 border-slate-200/80'
                                                    : 'bg-white border-slate-200 hover:border-slate-300 shadow-2xs'
                                                }`}
                                              >
                                                {/* Outlet Row Header */}
                                                <div
                                                  onClick={() => toggleStopExpand(va.id, stop.id)}
                                                  className="p-3 sm:px-4 sm:py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer hover:bg-slate-50/70 transition"
                                                >
                                                  {/* Left: Stop Index + Outlet Code + Outlet Name + Status */}
                                                  <div className="flex items-center gap-3">
                                                    <span
                                                      className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs flex-shrink-0 ${
                                                        isDone
                                                          ? 'bg-slate-200 text-slate-600'
                                                          : isCurrent
                                                          ? 'bg-emerald-100 text-emerald-800'
                                                          : 'bg-slate-100 text-slate-700'
                                                      }`}
                                                    >
                                                      {sIdx + 1}
                                                    </span>

                                                    <div>
                                                      <div className="flex flex-wrap items-center gap-2">
                                                        <span className="font-mono font-bold text-xs text-slate-900">{stop.id}</span>
                                                        <span className="text-slate-300">•</span>
                                                        <span className="font-bold text-xs text-slate-900">{stop.name}</span>
                                                        <span
                                                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                                            isDone
                                                              ? 'bg-slate-200/80 text-slate-600'
                                                              : isCurrent
                                                              ? 'bg-emerald-100 text-emerald-800'
                                                              : stop.status === 'Delayed'
                                                              ? 'bg-amber-100 text-amber-800'
                                                              : 'bg-slate-100 text-slate-600'
                                                          }`}
                                                        >
                                                          {stop.status}
                                                        </span>
                                                      </div>
                                                      <p className="text-[11px] text-slate-500 mt-0.5">
                                                        Cargo: <span className="text-slate-700 font-medium">{stop.cargo}</span> · ETA: <strong className="text-slate-800 font-mono">{stop.eta}</strong>
                                                      </p>
                                                    </div>
                                                  </div>

                                                  {/* Right: Crates/Weight + Smaller Dropdown Button */}
                                                  <div className="flex items-center gap-3 self-end sm:self-center">
                                                    <div className="text-right hidden sm:block">
                                                      <span className="text-xs font-bold text-slate-900">{stop.crates} crates</span>
                                                      <span className="text-slate-400 text-[11px] block">{stop.weightKg ? `${stop.weightKg} kg` : 'Payload'}</span>
                                                    </div>

                                                    {/* Smaller Dropdown Toggle Button */}
                                                    <button
                                                      type="button"
                                                      onClick={(e) => {
                                                        e.stopPropagation();
                                                        toggleStopExpand(va.id, stop.id);
                                                      }}
                                                      className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                                                        isStopExpanded
                                                          ? 'bg-[#EAF7EE] text-[#059669] border border-[#CDEED6]'
                                                          : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200/70'
                                                      }`}
                                                      title={isStopExpanded ? 'Collapse shop items' : 'View shop items'}
                                                    >
                                                      <Package size={13} className={isStopExpanded ? 'text-[#059669]' : 'text-slate-500'} />
                                                      <span>{stop.items?.length || 0} Shop Items</span>
                                                      <ChevronDown
                                                        size={13}
                                                        className={`transition-transform duration-200 ${
                                                          isStopExpanded ? 'rotate-180 text-[#059669]' : 'text-slate-400'
                                                        }`}
                                                      />
                                                    </button>
                                                  </div>
                                                </div>

                                                {/* Smaller Dropdown Content: Items Pertaining to That Shop */}
                                                {isStopExpanded && (
                                                  <div className="border-t border-slate-200/80 bg-[#F9FBFA] p-3.5 sm:px-5 sm:py-4">
                                                    <div className="flex items-center justify-between mb-2.5">
                                                      <div className="flex items-center gap-2">
                                                        <span className="text-xs font-bold text-slate-900">
                                                          Items Pertaining to {stop.name}
                                                        </span>
                                                        <span className="text-[11px] text-slate-500 font-mono">
                                                          ({stop.id})
                                                        </span>
                                                      </div>
                                                      <span className="text-[11px] text-slate-500">
                                                        {stop.items?.length || 0} items allocated
                                                      </span>
                                                    </div>

                                                    {stop.items && stop.items.length > 0 ? (
                                                      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-2xs">
                                                        <table className="w-full text-left text-xs">
                                                          <thead>
                                                            <tr className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200 text-[11px]">
                                                              <th className="py-2.5 px-3.5">SKU CODE</th>
                                                              <th className="py-2.5 px-3.5">PRODUCT / ITEM NAME</th>
                                                              <th className="py-2.5 px-3.5">CATEGORY</th>
                                                              <th className="py-2.5 px-3.5">QUANTITY / CRATES</th>
                                                              <th className="py-2.5 px-3.5 text-right">WEIGHT</th>
                                                            </tr>
                                                          </thead>
                                                          <tbody className="divide-y divide-slate-100">
                                                            {stop.items.map((item, itemIdx) => (
                                                              <tr key={itemIdx} className="hover:bg-slate-50/60 transition-colors">
                                                                <td className="py-2.5 px-3.5 font-mono font-bold text-slate-900">
                                                                  {item.sku}
                                                                </td>
                                                                <td className="py-2.5 px-3.5 font-semibold text-slate-800">
                                                                  {item.name}
                                                                </td>
                                                                <td className="py-2.5 px-3.5">
                                                                  <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700">
                                                                    {item.category}
                                                                  </span>
                                                                </td>
                                                                <td className="py-2.5 px-3.5 font-medium text-slate-700">
                                                                  {item.quantity}
                                                                </td>
                                                                <td className="py-2.5 px-3.5 text-right font-mono font-bold text-slate-900">
                                                                  {item.weight}
                                                                </td>
                                                              </tr>
                                                            ))}
                                                          </tbody>
                                                        </table>
                                                      </div>
                                                    ) : (
                                                      <div className="p-3 text-center text-xs text-slate-500 bg-white rounded-lg border border-slate-200">
                                                        No individual items registered for this stop.
                                                      </div>
                                                    )}
                                                  </div>
                                                )}
                                              </div>
                                            );
                                          })}
                                        </div>
                                      </div>
                                    </td>
                                  </tr>
                                )}
                              </React.Fragment>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

                {/* =================================================== */}
                {/* 2. VIEW BY OUTLET (OUTLET CARDS WITH VEHICLES DROPDOWN) */}
                {/* =================================================== */}
                {workbenchView === 'outlet' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                    {filteredOutletAssignments.map((outlet) => {
                      const isExpanded = expandedOutletIds.has(outlet.id);

                      return (
                        <div
                          key={outlet.id}
                          className="bg-white rounded-xl border border-gray-200/80 shadow-xs overflow-hidden transition hover:border-gray-300"
                        >
                          {/* Outlet Card Header */}
                          <div
                            onClick={() => toggleOutletExpand(outlet.id)}
                            className="p-4 flex items-start justify-between gap-3 cursor-pointer hover:bg-slate-50/50 transition"
                          >
                            <div className="flex items-start gap-3">
                              <div className="w-9 h-9 rounded-lg bg-emerald-50 text-[#059669] border border-emerald-200 flex items-center justify-center font-bold text-xs flex-shrink-0">
                                <Building2 size={18} />
                              </div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <h3 className="font-bold text-xs text-slate-900">{outlet.name}</h3>
                                  <span className="font-mono text-[11px] text-slate-500 font-semibold">({outlet.id})</span>
                                </div>
                                <p className="text-[11px] text-slate-500 mt-0.5 flex items-center gap-1.5">
                                  <span>{outlet.district}</span>
                                  <span>•</span>
                                  <span>Window: <strong className="text-slate-700">{outlet.deliveryWindow}</strong></span>
                                </p>
                              </div>
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                                {outlet.assignedVehicles.length} Vehicles Assigned
                              </span>
                              <button
                                type="button"
                                className="p-1 text-slate-400 hover:text-slate-700"
                              >
                                {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                              </button>
                            </div>
                          </div>

                          {/* Expandable Dropdown with Vehicles Assigned to this Outlet */}
                          {isExpanded && (
                            <div className="px-4 pb-4 pt-1 bg-slate-50/70 border-t border-slate-100 flex flex-col gap-2">
                              <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 pb-1">
                                <span className="font-bold uppercase tracking-wider text-[10px] text-slate-400">
                                  Assigned Fleet Deliveries
                                </span>
                                <span>Total Demand: <strong className="text-slate-700">{outlet.totalDemand}</strong></span>
                              </div>

                              {outlet.assignedVehicles.map((av) => (
                                <div
                                  key={av.id}
                                  className="bg-white p-3 rounded-lg border border-slate-200/90 flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-2xs"
                                >
                                  <div className="flex items-center gap-2.5">
                                    <span className="font-mono font-bold text-slate-900 text-xs px-2 py-0.5 rounded bg-slate-100">
                                      {av.id}
                                    </span>
                                    <div>
                                      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
                                        <span>{av.type} ({av.refrigeration})</span>
                                        <span className="text-slate-300">·</span>
                                        <span className="text-slate-600 font-normal">{av.tripLeg}</span>
                                      </div>
                                      <p className="text-[11px] text-slate-500 mt-0.5">
                                        Cargo: <strong className="text-slate-700">{av.cargo}</strong> · {av.driver}
                                      </p>
                                    </div>
                                  </div>

                                  <div className="flex items-center gap-2.5">
                                    <span className="font-mono text-xs font-bold text-slate-800">
                                      ETA: {av.eta}
                                    </span>
                                    <span
                                      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                                        av.status === 'Completed'
                                          ? 'bg-slate-100 text-slate-600'
                                          : av.status === 'Delayed'
                                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                          : av.status === 'At Dock - Unloading'
                                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                          : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                                      }`}
                                    >
                                      {av.status}
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* =================================================== */}
                {/* 3. DEFERRALS SECTION (DAMAGED / UNAVAILABLE GOODS)  */}
                {/* =================================================== */}
                {workbenchView === 'deferrals' && (
                  <div className="w-full bg-white border border-gray-200/80 rounded-2xl shadow-xs overflow-hidden">
                    <div className="p-4 border-b border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div>
                        <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                          <span>Unassigned & Deferred Items Log</span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                            {filteredDeferrals.length} Items Flagged
                          </span>
                        </h2>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Orders excluded from wave dispatch due to damaged staging or stock shortages.
                        </p>
                      </div>

                      <div className="text-[11px] text-slate-600">
                        Total Deferred Quantity: <strong className="text-slate-900">280 kg / 340 units</strong>
                      </div>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="bg-[#F8FAFC] text-slate-500 font-semibold border-b border-gray-200/70 select-none">
                            <th className="py-3 px-4">ORDER ID</th>
                            <th className="py-3 px-4">PRODUCT / SKU</th>
                            <th className="py-3 px-4">TARGET OUTLET</th>
                            <th className="py-3 px-4">QUANTITY</th>
                            <th className="py-3 px-4">DEFERRAL CATEGORY</th>
                            <th className="py-3 px-4">SPECIFIC REASON</th>
                            <th className="py-3 px-4">ACTION & RESOLUTION</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {filteredDeferrals.map((def) => (
                            <tr key={def.id} className="hover:bg-slate-50/60 transition">
                              {/* ORDER ID */}
                              <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                                {def.orderId}
                              </td>

                              {/* PRODUCT / SKU */}
                              <td className="py-3.5 px-4 font-medium text-slate-800">
                                {def.sku}
                              </td>

                              {/* TARGET OUTLET */}
                              <td className="py-3.5 px-4 text-slate-600">
                                {def.outlet}
                              </td>

                              {/* QUANTITY */}
                              <td className="py-3.5 px-4 font-mono font-semibold text-slate-800">
                                {def.quantity}
                              </td>

                              {/* DEFERRAL CATEGORY */}
                              <td className="py-3.5 px-4">
                                {def.category === 'Damaged Goods' ? (
                                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                                    <AlertTriangle size={11} />
                                    <span>Damaged Goods</span>
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                                    <AlertCircle size={11} />
                                    <span>Unavailable Goods</span>
                                  </span>
                                )}
                              </td>

                              {/* SPECIFIC REASON */}
                              <td className="py-3.5 px-4 text-slate-600 max-w-xs">
                                <p className="leading-snug text-[11px]">{def.reason}</p>
                                <span className="text-[10px] text-slate-400 mt-0.5 block">
                                  By {def.reportedBy} at {def.loggedAt}
                                </span>
                              </td>

                              {/* ACTION & RESOLUTION */}
                              <td className="py-3.5 px-4">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                                  {def.resolution}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* ======================================================= */
              /* SUB-TAB 1: FLEET AVAILABILITY (ACTIVE ASSET ROSTER)     */
              /* ======================================================= */
              <div className="flex flex-col gap-4">
                {/* Filter Controls Row */}
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pt-1">
                  {/* Left: Hub Pills, Bulk Helpers, and Category Filters */}
                  <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">

                    {/* Quick Bulk Action Helpers */}
                    <div className="inline-flex items-center gap-1 bg-slate-100/80 px-2 py-1 rounded-lg border border-slate-200/60 text-xs font-medium text-slate-600">
                      <button
                        type="button"
                        onClick={handleSelectAll}
                        className="hover:text-slate-900 px-1.5 py-0.5 rounded hover:bg-white transition cursor-pointer"
                      >
                        All
                      </button>
                      <span className="text-slate-300">|</span>
                      <button
                        type="button"
                        onClick={handleSelectNone}
                        className="hover:text-slate-900 px-1.5 py-0.5 rounded hover:bg-white transition cursor-pointer"
                      >
                        None
                      </button>
                      <span className="text-slate-300">|</span>
                      <button
                        type="button"
                        onClick={handleResetDefault}
                        className="hover:text-slate-900 px-1.5 py-0.5 rounded hover:bg-white transition cursor-pointer"
                      >
                        Reset Default
                      </button>
                    </div>

                    {/* Category Filter Pills */}
                    <div className="inline-flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => setCategoryFilter('all')}
                        className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                          categoryFilter === 'all'
                            ? 'bg-slate-900 text-white shadow-2xs'
                            : 'bg-white border border-gray-200 text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        All
                      </button>
                      <button
                        type="button"
                        onClick={() => setCategoryFilter('reefer')}
                        className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                          categoryFilter === 'reefer'
                            ? 'bg-slate-900 text-white shadow-2xs'
                            : 'bg-white border border-gray-200 text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        Reefer Units (16)
                      </button>
                      <button
                        type="button"
                        onClick={() => setCategoryFilter('van')}
                        className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                          categoryFilter === 'van'
                            ? 'bg-slate-900 text-white shadow-2xs'
                            : 'bg-white border border-gray-200 text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        Vans Only
                      </button>
                    </div>
                  </div>

                  {/* Right: Find vehicle search bar */}
                  <div className="relative w-full sm:w-60">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Find vehicle..."
                      className="w-full h-8.5 pl-9 pr-3 text-xs font-medium text-slate-900 bg-white border border-gray-200 rounded-lg placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#059669] focus:border-transparent transition shadow-2xs"
                    />
                  </div>
                </div>

                {/* Metrics Summary Strip with Proceed Button */}
                <div className="w-full py-1 flex flex-col md:flex-row md:items-center justify-between gap-3">
                  {/* Summary Metric Badges */}
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-xs">
                    {/* Active Assets Pill */}
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold bg-[#EAF6EE] text-[#059669] border border-[#CDEBD8]">
                      <span className="font-normal text-[#059669]/90">Active Assets:</span>
                      <span className="font-bold">{availableAssetsDisplay} Vehicles Available</span>
                    </div>

                    {/* Reefer Readiness Pill */}
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold bg-[#EBF5FB] text-[#0284C7] border border-[#CCE5F7]">
                      <span className="font-normal text-[#0284C7]/90">Reefer Readiness:</span>
                      <span className="font-bold">{reeferReadinessDisplay} Reefers Ready</span>
                    </div>

                    <span className="text-slate-300 hidden sm:inline">•</span>

                    {/* Total Volume */}
                    <div className="flex items-center gap-1.5 text-slate-600">
                      <span className="font-normal">Total Volume:</span>
                      <span className="font-mono font-bold text-slate-900">{totalVolumeM3} m³</span>
                    </div>

                    <span className="text-slate-300 hidden sm:inline">•</span>

                    {/* Total Weight */}
                    <div className="flex items-center gap-1.5 text-slate-600">
                      <span className="font-normal">Total Weight:</span>
                      <span className="font-mono font-bold text-slate-900">{totalPayloadKg} kg</span>
                    </div>
                  </div>

                  {/* Proceed to Route Allocation Button */}
                  <button
                    type="button"
                    onClick={() => setShowDispatchPlanModal(true)}
                    className="inline-flex items-center justify-center gap-2 bg-[#059669] hover:bg-[#047857] active:bg-[#065F46] text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all shadow-xs cursor-pointer flex-shrink-0"
                  >
                    <span>Proceed to Route Allocation</span>
                    <ArrowRight size={14} />
                  </button>
                </div>

                {/* Fleet Roster Table Container with Interactive Checkboxes */}
                <div className="w-full bg-white border border-gray-200/80 rounded-2xl shadow-xs overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="bg-[#F8FAFC] text-slate-500 font-semibold border-b border-gray-200/70 select-none">
                          {/* Master Checkbox Column */}
                          <th className="py-3 pl-4 pr-2 w-10">
                            <button
                              type="button"
                              onClick={handleToggleAllFiltered}
                              className={`w-4 h-4 rounded-[4px] border flex items-center justify-center transition-colors cursor-pointer ${
                                allFilteredChecked
                                  ? 'bg-[#059669] border-[#059669] text-white'
                                  : someFilteredChecked
                                  ? 'bg-[#059669]/20 border-[#059669] text-[#059669]'
                                  : 'bg-white border-slate-300 hover:border-slate-400'
                              }`}
                              title={allFilteredChecked ? 'Deselect all' : 'Select all'}
                            >
                              {allFilteredChecked && <Check size={11} strokeWidth={3} />}
                              {someFilteredChecked && <span className="w-2 h-0.5 bg-[#059669] rounded-full" />}
                            </button>
                          </th>
                          <th className="py-3 px-3">VEHICLE ID</th>
                          <th className="py-3 px-4">DEPOT</th>
                          <th className="py-3 px-4">TYPE</th>
                          <th className="py-3 px-4">REFRIGERATION</th>
                          <th className="py-3 px-4">MAX PAYLOAD (KG)</th>
                          <th className="py-3 px-4">MAX VOLUME (M³)</th>
                          <th className="py-3 px-4">WEEKLY FUEL QUOTA</th>
                          <th className="py-3 px-4">ROSTER STATUS</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {filteredVehicles.length === 0 ? (
                          <tr>
                            <td colSpan="9" className="py-12 text-center text-slate-500 text-xs">
                              No vehicles found matching "{searchQuery}".
                            </td>
                          </tr>
                        ) : (
                          filteredVehicles.map((vehicle) => {
                            const isLocked = vehicle.isLockedUnavailable;
                            const isSelected = selectedRowId === vehicle.id;
                            const isChecked = vehicle.checked;

                            return (
                              <tr
                                key={vehicle.id}
                                onClick={() => {
                                  if (!isLocked) setSelectedRowId(vehicle.id);
                                }}
                                onMouseEnter={(e) => {
                                  if (isLocked) {
                                    setHoveredUnavailableVehicle(vehicle);
                                    setMousePos({ x: e.clientX, y: e.clientY });
                                  }
                                }}
                                onMouseMove={(e) => {
                                  if (isLocked) {
                                    setMousePos({ x: e.clientX, y: e.clientY });
                                  }
                                }}
                                onMouseLeave={() => {
                                  if (isLocked) {
                                    setHoveredUnavailableVehicle(null);
                                  }
                                }}
                                className={`transition-colors relative ${
                                  isLocked
                                    ? 'bg-slate-50/50 opacity-60 hover:opacity-95 cursor-default'
                                    : isSelected
                                    ? 'bg-[#EBF7F1]/70 cursor-pointer'
                                    : !isChecked
                                    ? 'bg-slate-50/40 hover:bg-slate-50 cursor-pointer'
                                    : 'hover:bg-slate-50/70 cursor-pointer'
                                }`}
                              >
                                {/* Row Checkbox Column */}
                                <td className="py-3 pl-4 pr-2 w-10">
                                  {isLocked ? (
                                    <div
                                      title={`Unavailable: Marked via ${vehicle.unavailableSource}`}
                                      className="w-4 h-4 rounded-[4px] border border-slate-300 bg-slate-100 flex items-center justify-center cursor-not-allowed select-none shadow-2xs"
                                    >
                                      <Lock size={9} className="text-slate-400" />
                                    </div>
                                  ) : (
                                    <button
                                      type="button"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleToggleCheck(vehicle.id);
                                      }}
                                      className={`w-4 h-4 rounded-[4px] border flex items-center justify-center transition-colors cursor-pointer ${
                                        isChecked
                                          ? 'bg-[#059669] border-[#059669] text-white shadow-2xs'
                                          : 'bg-white border-slate-300 hover:border-slate-400'
                                      }`}
                                    >
                                      {isChecked && <Check size={11} strokeWidth={3} />}
                                    </button>
                                  )}
                                </td>

                                {/* VEHICLE ID */}
                                <td className="py-3 px-3">
                                  <div className="flex items-center gap-1.5">
                                    <span
                                      className={`font-mono font-bold ${
                                        isLocked || !isChecked ? 'text-slate-400' : 'text-slate-900'
                                      }`}
                                    >
                                      {vehicle.id}
                                    </span>
                                    {isLocked && (
                                      <span 
                                        className="inline-flex items-center text-[10px] px-1.5 py-0.2 rounded font-medium bg-amber-50 text-amber-700 border border-amber-200"
                                        title={`Marked via ${vehicle.unavailableSource}`}
                                      >
                                        {(vehicle.unavailableSource || '').includes('Driver') ? 'Driver' : 'Loader'}
                                      </span>
                                    )}
                                  </div>
                                </td>

                                {/* DEPOT */}
                                <td className={`py-3 px-4 ${isLocked || !isChecked ? 'text-slate-400' : 'text-slate-600'}`}>
                                  {vehicle.depot}
                                </td>

                                {/* TYPE */}
                                <td className="py-3 px-4">
                                  <span
                                    className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                                      isLocked || !isChecked
                                        ? 'bg-slate-100 text-slate-400'
                                        : 'bg-slate-100 text-slate-700'
                                    }`}
                                  >
                                    {vehicle.type}
                                  </span>
                                </td>

                                {/* REFRIGERATION */}
                                <td className="py-3 px-4">
                                  {vehicle.refrigeration === 'Reefer' ? (
                                    <span
                                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                                        isLocked || !isChecked
                                          ? 'bg-slate-100 text-slate-400 border border-slate-200'
                                          : 'bg-sky-50 text-sky-700 border border-sky-200'
                                      }`}
                                    >
                                      Reefer
                                    </span>
                                  ) : (
                                    <span
                                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ${
                                        isLocked || !isChecked
                                          ? 'bg-slate-100 text-slate-400 border border-slate-200'
                                          : 'bg-slate-50 text-slate-600 border border-slate-200'
                                      }`}
                                    >
                                      Ambient
                                    </span>
                                  )}
                                </td>

                                {/* MAX PAYLOAD (KG) */}
                                <td className={`py-3 px-4 font-mono ${isLocked || !isChecked ? 'text-slate-400' : 'text-slate-800'}`}>
                                  {(Number(vehicle.payloadKg) || 0).toLocaleString()}
                                </td>

                                {/* MAX VOLUME (M³) */}
                                <td className={`py-3 px-4 font-mono ${isLocked || !isChecked ? 'text-slate-400' : 'text-slate-800'}`}>
                                  {(Number(vehicle.volumeM3) || 0).toFixed(1)}
                                </td>

                                {/* WEEKLY FUEL QUOTA */}
                                <td className="py-3 px-4">
                                  <div className="flex items-center gap-2.5">
                                    <div className="w-16 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                                      <div
                                        style={{ width: `${vehicle.fuelQuota}%` }}
                                        className={`h-full rounded-full ${
                                          isLocked || !isChecked
                                            ? 'bg-slate-300'
                                            : vehicle.fuelQuota >= 80
                                            ? 'bg-amber-500'
                                            : 'bg-emerald-600'
                                        }`}
                                      />
                                    </div>
                                    <span
                                      className={`font-mono text-xs ${
                                        isLocked || !isChecked
                                          ? 'text-slate-400'
                                          : vehicle.fuelQuota >= 80
                                          ? 'font-bold text-amber-700'
                                          : 'text-slate-700'
                                      }`}
                                    >
                                      {vehicle.fuelQuota}%
                                    </span>
                                  </div>
                                </td>

                                {/* ROSTER STATUS */}
                                <td className="py-3 px-4">
                                  {isLocked ? (
                                    <div 
                                      title={`Unavailable: ${vehicle.unavailableReason} (Hover row for details)`}
                                      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200 select-none cursor-default"
                                    >
                                      <Lock size={10} className="text-rose-500" />
                                      <span>Excluded from Run</span>
                                    </div>
                                  ) : (
                                    <button
                                      type="button"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleToggleCheck(vehicle.id);
                                      }}
                                      title="Click to toggle availability"
                                      className="cursor-pointer focus:outline-none"
                                    >
                                      {isChecked ? (
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition">
                                          Active Pool
                                        </span>
                                      ) : (
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition">
                                          Excluded from Run
                                        </span>
                                      )}
                                    </button>
                                  )}
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Compact Light-Theme Unavailable Popover on Row Hover (Wireframe Design) */}
      {hoveredUnavailableVehicle && (
        <div
          style={{
            left: `${Math.min(
              typeof window !== 'undefined' ? window.innerWidth - 440 : 600,
              Math.max(20, mousePos.x - 200)
            )}px`,
            top: `${
              mousePos.y > (typeof window !== 'undefined' ? window.innerHeight - 170 : 500)
                ? mousePos.y - 150
                : mousePos.y + 16
            }px`,
          }}
          className="fixed z-50 w-[420px] bg-white rounded-xl shadow-xl shadow-slate-900/10 border border-slate-200/90 pointer-events-none transition-all duration-75 text-xs select-none overflow-hidden"
        >
          {/* Row 1: Header with Vehicle Tag & Status Chips */}
          <div className="px-3.5 py-2.5 flex items-center justify-between gap-2 bg-slate-50/50">
            <div className="flex items-center gap-1.5">
              <Lock size={12} className="text-slate-500 flex-shrink-0" />
              <span className="font-mono font-bold text-slate-900">
                {hoveredUnavailableVehicle.id}
              </span>
              <span className="text-slate-400">·</span>
              <span className="font-medium text-slate-600">Unavailable</span>
            </div>

            <div className="flex items-center gap-1.5">
              {/* Source Portal Pill */}
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                  (hoveredUnavailableVehicle?.unavailableSource || '') === 'Driver Portal'
                    ? 'bg-amber-50 text-amber-700 border border-amber-200/60'
                    : 'bg-sky-50 text-sky-700 border border-sky-200/60'
                }`}
              >
                {hoveredUnavailableVehicle?.unavailableSource || 'Dispatcher Portal'}
              </span>

              {/* Excluded Status Pill */}
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200/60">
                Excluded
              </span>
            </div>
          </div>

          <div className="h-px bg-slate-100 w-full" />

          {/* Row 2: Direct Issue Statement */}
          <div className="px-3.5 py-2.5 text-slate-700 text-xs font-normal leading-relaxed">
            {hoveredUnavailableVehicle?.unavailableReason || 'Marked Unavailable'}
          </div>

          <div className="h-px bg-slate-100 w-full" />

          {/* Row 3: Reporter, Est. Return, and Action */}
          <div className="px-3.5 py-2.5 bg-slate-50/30 text-[11px] flex flex-col gap-1.5">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-1">
                <span className="text-slate-500 font-normal">Reporter:</span>
                <span className="text-slate-800 font-medium">{hoveredUnavailableVehicle.reportedBy}</span>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                <span className="text-slate-500 font-normal">Est. Return:</span>
                <span className="text-slate-800 font-medium">{hoveredUnavailableVehicle.expectedReturn}</span>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <span className="text-slate-500 font-normal">Action:</span>
              <span className="text-slate-800 font-medium">{hoveredUnavailableVehicle.maintenanceType}</span>
            </div>
          </div>
        </div>
      )}

      {/* Verify Dispatch Plan Modal */}
      <VerifyDispatchPlanModal
        isOpen={showDispatchPlanModal}
        onClose={() => setShowDispatchPlanModal(false)}
        onAdjustInWorkbench={() => {
          setShowDispatchPlanModal(false);
          setShowAllocationBoard(true);
        }}
        onManualAllocation={() => {
          setShowDispatchPlanModal(false);
          setShowAllocationBoard(true);
        }}
        onConfirmAndLock={async () => {
          try {
            const { safeStorage } = await import('@/lib/security');
            const token = safeStorage.get('token');
            if (token) {
              const { apiFetch } = await import('@/lib/api');
              const targetDate = new Date().toISOString().split('T')[0];
              const draft = await apiFetch('/dispatcher/plans/draft', {
                method: 'POST',
                body: JSON.stringify({ target_date: targetDate })
              });
              if (draft && draft.plan_id) {
                await apiFetch(`/dispatcher/plans/${draft.plan_id}/approve`, {
                  method: 'POST',
                  body: JSON.stringify({ client_op_id: `approve-${Date.now()}` })
                });
              }
            }
          } catch (err) {
            console.warn('Backend plan approval notification:', err);
          }
          setShowDispatchPlanModal(false);
          setIsAllocationConfirmed(true);
          setShowConfirmToast(true);
          setTimeout(() => {
            setShowConfirmToast(false);
          }, 4000);
          setActiveNav('Route Allocation & Capacity');
          setActiveSubTab('Allocation Workbench');
        }}
      />

      {/* Recovery Plan Modal */}
      <RecoveryPlanModal
        isOpen={showRecoveryModal}
        onClose={() => setShowRecoveryModal(false)}
        onAdjustInWorkbench={() => {
          setShowRecoveryModal(false);
          setShowAllocationBoard(true);
        }}
        onConfirmRecovery={() => {
          setShowRecoveryModal(false);
          setRecoveryDeployed(true);
          setShowConfirmToast(true);
          setTimeout(() => {
            setShowConfirmToast(false);
          }, 4000);
          setActiveNav('Contingency Dispatch');
        }}
      />
    </div>
  );
}
