import React, { useState, useMemo } from 'react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';
import InspectDeliveryModal from './InspectDeliveryModal';
import OrderConfirmationModal from './OrderConfirmationModal';
import {
  OUTLETS,
  CATALOGS,
  ACTIVE_INBOUND_BY_OUTLET,
  ORDER_HISTORY_BY_OUTLET,
} from './storeManagerData';
import {
  Truck,
  Bell,
  ChevronDown,
  ChevronUp,
  Package,
  Phone,
  Check,
  Clock,
  AlertCircle,
  AlertTriangle,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Snowflake,
  X,
  ShieldCheck,
  Layers,
  FileCheck,
  CheckCircle2,
  Calendar,
  Building2,
  MapPin,
  Sparkles,
  Info,
} from 'lucide-react';

export default function StoreManagerOverview({ onLogout }) {
  // Navigation & Outlet Selection State
  const [activeTab, setActiveTab] = useState('Overview');
  const [selectedOutletId, setSelectedOutletId] = useState('OUT047'); // Default: Waypoint Fresh Kandy Town
  const [showOutletDropdown, setShowOutletDropdown] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [hasUnreadNotifications, setHasUnreadNotifications] = useState(true);

  // Active Outlet Data
  const currentOutlet = useMemo(() => {
    return OUTLETS.find((o) => o.id === selectedOutletId) || OUTLETS[0];
  }, [selectedOutletId]);

  // Modals State
  const [inspectModalOpen, setInspectModalOpen] = useState(false);
  const [selectedInspectVehicle, setSelectedInspectVehicle] = useState(null);
  const [confirmOrderModalOpen, setConfirmOrderModalOpen] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // Overview Tab State
  const [ordersSegmentTab, setOrdersSegmentTab] = useState('progress'); // 'progress' | 'deferred'
  const [expandedVehicles, setExpandedVehicles] = useState({ 'VH-014': true, 'VH-025': true });
  const [verifiedShipments, setVerifiedShipments] = useState({}); // Shipments confirmed by manager

  // Place Order Tab State
  const [catalogSearch, setCatalogSearch] = useState('');
  const [catalogSortField, setCatalogSortField] = useState('id'); // 'id' | 'name'
  const [catalogSortDirection, setCatalogSortDirection] = useState('asc'); // 'asc' | 'desc'
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState('All');
  const [isSimulatedPastCutoff, setIsSimulatedPastCutoff] = useState(false);
  const [orderPlacedSuccess, setOrderPlacedSuccess] = useState(false);

  // Quantities for current catalog, keyed by product ID
  const [orderQuantities, setOrderQuantities] = useState({
    'PRD-F101': 10,
    'PRD-F102': 15,
    'PRD-F201': 8,
    'PRD-F203': 6,
    'PRD-S101': 12,
    'PRD-S201': 6,
    'PRD-T101': 2,
    'PRD-T102': 3,
  });

  // Receipts & Deferrals Tab State
  const [historyFilter, setHistoryFilter] = useState('All'); // 'All' | 'Delivered' | 'Deferred'
  const [historySearch, setHistorySearch] = useState('');
  const [expandedHistoryRows, setExpandedHistoryRows] = useState({ 'ORD-30082': true, 'ORD-30114': true });

  // Inbound Shipments for selected outlet
  const activeInboundVehicles = useMemo(() => {
    return ACTIVE_INBOUND_BY_OUTLET[currentOutlet.id] || ACTIVE_INBOUND_BY_OUTLET['OUT047'];
  }, [currentOutlet.id]);

  // Order History for selected outlet
  const orderHistoryList = useMemo(() => {
    return ORDER_HISTORY_BY_OUTLET[currentOutlet.id] || ORDER_HISTORY_BY_OUTLET['OUT047'];
  }, [currentOutlet.id]);

  // Catalog items for the active brand
  const currentCatalog = useMemo(() => {
    return CATALOGS[currentOutlet.brand] || CATALOGS['Waypoint Fresh'];
  }, [currentOutlet.brand]);

  // Categories present in active catalog
  const catalogCategories = useMemo(() => {
    const set = new Set(['All']);
    currentCatalog.forEach((p) => set.add(p.category));
    return Array.from(set);
  }, [currentCatalog]);

  const toggleVehicle = (id) => {
    setExpandedVehicles((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleHistoryRow = (orderNo) => {
    setExpandedHistoryRows((prev) => ({ ...prev, [orderNo]: !prev[orderNo] }));
  };

  const handleQtyChange = (id, val) => {
    const num = parseInt(val, 10);
    setOrderQuantities((prev) => ({
      ...prev,
      [id]: isNaN(num) ? 0 : Math.max(0, num),
    }));
  };

  const handleSortToggle = (field) => {
    if (catalogSortField === field) {
      setCatalogSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setCatalogSortField(field);
      setCatalogSortDirection('asc');
    }
  };

  // Filtered and sorted products
  const filteredCatalog = useMemo(() => {
    return currentCatalog.filter((item) => {
      const matchCat =
        selectedCategoryFilter === 'All' || item.category === selectedCategoryFilter;
      const q = catalogSearch.toLowerCase().trim();
      const matchSearch =
        !q ||
        item.id.toLowerCase().includes(q) ||
        item.name.toLowerCase().includes(q) ||
        item.format.toLowerCase().includes(q) ||
        (item.subType && item.subType.toLowerCase().includes(q));
      return matchCat && matchSearch;
    });
  }, [currentCatalog, selectedCategoryFilter, catalogSearch]);

  const sortedCatalog = useMemo(() => {
    return [...filteredCatalog].sort((a, b) => {
      let comp = 0;
      if (catalogSortField === 'id') {
        comp = a.id.localeCompare(b.id, undefined, { numeric: true });
      } else {
        comp = a.name.localeCompare(b.name);
      }
      return catalogSortDirection === 'asc' ? comp : -comp;
    });
  }, [filteredCatalog, catalogSortField, catalogSortDirection]);

  // Order Metrics Calculations
  const activeLineItems = useMemo(() => {
    return currentCatalog
      .filter((p) => (orderQuantities[p.id] || 0) > 0)
      .map((p) => ({ ...p, qty: orderQuantities[p.id] }));
  }, [currentCatalog, orderQuantities]);

  const totalOrderedUnits = useMemo(() => {
    return activeLineItems.reduce((acc, item) => acc + item.qty, 0);
  }, [activeLineItems]);

  const estTotalWeightKg = useMemo(() => {
    return Math.round(
      activeLineItems.reduce((sum, item) => sum + item.qty * item.unitWeightKg, 0)
    );
  }, [activeLineItems]);

  const estTotalVolumeM3 = useMemo(() => {
    return activeLineItems
      .reduce((sum, item) => sum + item.qty * item.unitVolumeM3, 0)
      .toFixed(2);
  }, [activeLineItems]);

  const dryItems = useMemo(() => {
    return activeLineItems.filter((p) => p.category === 'Dry');
  }, [activeLineItems]);

  const chilledItems = useMemo(() => {
    return activeLineItems.filter((p) => p.category === 'Chilled');
  }, [activeLineItems]);

  // Dual dispatch logic for Fresh
  const dispatchesCount = useMemo(() => {
    if (currentOutlet.brand !== 'Waypoint Fresh') return 1;
    return (dryItems.length > 0 ? 1 : 0) + (chilledItems.length > 0 ? 1 : 0);
  }, [currentOutlet.brand, dryItems, chilledItems]);

  // Order summary metrics package
  const orderTotals = {
    totalUnits: totalOrderedUnits,
    estWeightKg: estTotalWeightKg,
    estVolumeM3: estTotalVolumeM3,
    dryItems,
    chilledItems,
    dispatchesCount,
  };

  const handleOpenInspect = (vehicle) => {
    setSelectedInspectVehicle(vehicle);
    setInspectModalOpen(true);
  };

  const handleConfirmInspectionReceipt = (details) => {
    setVerifiedShipments((prev) => ({
      ...prev,
      [details.vehicleId]: details,
    }));
    setToastMessage(`Receipt signed with driver ${details.driverName} (Ref: ${details.receiptId})`);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 4000);
  };

  const handleFinalOrderSubmit = () => {
    setOrderPlacedSuccess(true);
    setToastMessage(`Order placed successfully! Scheduled for ${isSimulatedPastCutoff ? 'Day +2 run' : 'Tomorrow morning'}.`);
    setShowToast(true);
    setTimeout(() => {
      setShowToast(false);
      setOrderPlacedSuccess(false);
    }, 4500);
  };

  // Node renderer for progress milestone stepper
  const renderNode = (stepIndex, activeStageIndex) => {
    if (stepIndex < activeStageIndex) {
      return (
        <div className="w-3.5 h-3.5 rounded-full bg-emerald-600 flex items-center justify-center text-white shadow-2xs">
          <Check size={9} strokeWidth={3} />
        </div>
      );
    }
    if (stepIndex === activeStageIndex) {
      return (
        <span className="relative flex h-3.5 w-3.5 items-center justify-center">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60 duration-1000" />
          <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-600 ring-2 ring-white shadow-2xs" />
        </span>
      );
    }
    return <span className="w-3 h-3 rounded-full border-2 border-slate-300 bg-white" />;
  };

  return (
    <div className={`min-h-screen w-full bg-[#FAFBFA] text-gray-900 font-sans antialiased ${activeTab === 'Place order' ? 'pb-4' : 'pb-16'}`}>
      {/* Toast Notification */}
      {showToast && (
        <div className="fixed top-4 right-4 z-50 bg-slate-900 text-white px-4 py-2.5 rounded-2xl shadow-xl flex items-center gap-2.5 text-xs border border-slate-700 animate-in fade-in slide-in-from-top-2 duration-150">
          <CheckCircle2 size={16} className="text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Top Navigation Bar */}
      <header className="w-full border-b border-gray-100 bg-white sticky top-0 z-30 shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          {/* Left: Brand Logo & Navigation Tabs */}
          <div className="flex items-center gap-4 sm:gap-8 min-w-0">
            {/* Waypoint Brand */}
            <div className="flex items-center gap-2.5 cursor-pointer shrink-0">
              <img
                src={waypointLogo}
                alt="Waypoint"
                className="w-7 h-7 object-contain rounded-lg shadow-xs"
              />
              <span
                className="text-lg font-bold tracking-tight text-[#0B2019] hidden sm:inline"
                style={{ fontFamily: "'Inter', sans-serif" }}
              >
                Waypoint
              </span>
            </div>

            {/* Navigation Pills */}
            <nav className="flex items-center gap-1 sm:gap-1.5" aria-label="Store Manager Navigation">
              {['Overview', 'Place order', 'Receipts & Deferrals'].map((tab) => {
                const isActive = activeTab === tab;
                return (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setActiveTab(tab)}
                    className={`px-3 py-1.5 rounded-full text-xs sm:text-sm font-semibold transition-colors cursor-pointer ${
                      isActive
                        ? 'bg-[#E8F7F0] text-[#059669]'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    {tab}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Right: Interactive Outlet Selector Dropdown, Receiving PIN badge & Account */}
          <div className="flex items-center gap-2.5 shrink-0">
            {/* Interactive Outlet & Brand Selector */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowOutletDropdown(!showOutletDropdown)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-800 bg-white border border-slate-200 hover:border-slate-300 rounded-full transition-colors cursor-pointer shadow-2xs"
                title="Switch Outlet / Brand"
              >
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="max-w-[130px] sm:max-w-[170px] truncate">{currentOutlet.name}</span>
                <ChevronDown size={13} className="text-slate-500" />
              </button>

              {/* Outlet Dropdown Menu */}
              {showOutletDropdown && (
                <div className="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-2xl shadow-xl py-2 z-50 text-xs">
                  <div className="px-3.5 py-1.5 border-b border-slate-100 flex items-center justify-between text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
                    <span>Select Outlet & Retail Brand</span>
                    <span>3 Brands</span>
                  </div>

                  <div className="max-h-72 overflow-y-auto divide-y divide-slate-100">
                    {OUTLETS.map((outlet) => {
                      const isSelected = outlet.id === currentOutlet.id;
                      return (
                        <button
                          key={outlet.id}
                          type="button"
                          onClick={() => {
                            setSelectedOutletId(outlet.id);
                            setShowOutletDropdown(false);
                          }}
                          className={`w-full text-left p-3 hover:bg-slate-50 transition cursor-pointer flex flex-col gap-1 ${
                            isSelected ? 'bg-emerald-50/60' : ''
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-900">{outlet.name}</span>
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                outlet.brand === 'Waypoint Fresh'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : outlet.brand === 'Waypoint Style'
                                  ? 'bg-purple-100 text-purple-800'
                                  : 'bg-blue-100 text-blue-800'
                              }`}
                            >
                              {outlet.brand}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-[11px] text-slate-500">
                            <span className="font-mono">{outlet.id}</span>
                            <span>·</span>
                            <span>{outlet.hub}</span>
                            <span>·</span>
                            <span>{outlet.accessConstraint}</span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Quick Receiving PIN Pill Badge */}
            <div
              className="hidden lg:inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 text-white text-xs font-mono font-bold shadow-2xs"
              title="Store Manager Receiving PIN for Driver Terminal"
            >
              <ShieldCheck size={13} className="text-emerald-400" />
              <span className="text-[11px] text-slate-400 font-sans font-medium">PoD PIN:</span>
              <span className="text-emerald-300 tracking-wider">{currentOutlet.receivingPin}</span>
            </div>

            {/* Notifications Button */}
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
                title="Account Settings"
                className="w-8 h-8 rounded-full bg-[#E0F2E9] border border-[#C6E7D5] text-[#059669] text-xs font-semibold flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity"
              >
                {currentOutlet.manager.split(' ').map(n => n[0]).join('')}
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-100 rounded-xl shadow-lg py-1 z-50 text-xs">
                  <div className="px-3 py-2 border-b border-gray-100">
                    <p className="font-bold text-gray-900">{currentOutlet.manager}</p>
                    <p className="text-[11px] text-gray-500">Store Manager · {currentOutlet.id}</p>
                  </div>
                  <button
                    onClick={() => {
                      setShowUserMenu(false);
                      if (onLogout) onLogout();
                    }}
                    className="w-full text-left px-3 py-2 text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 flex flex-col gap-6">
        {/* ============================================================== */}
        {/* 1. OVERVIEW TAB: Live Shipments, Multi-Truck Split & Digital Handshake */}
        {/* ============================================================== */}
        {activeTab === 'Overview' && (
          <div className="flex flex-col gap-5">
            {/* Store Context & Outlet Header Strip */}
            <div className="bg-white border border-slate-200/80 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-2xs">
              <div className="flex items-start sm:items-center gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-200/80 flex items-center justify-center text-emerald-700 shrink-0 shadow-2xs">
                  <Building2 size={24} />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h1 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
                      {currentOutlet.name}
                    </h1>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                      {currentOutlet.brand}
                    </span>
                    <span className="font-mono text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                      {currentOutlet.id}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-1">
                    <span className="flex items-center gap-1">
                      <MapPin size={12} className="text-slate-400" />
                      {currentOutlet.address}
                    </span>
                    <span>·</span>
                    <span className="font-medium text-slate-700">Hub: {currentOutlet.hub}</span>
                    <span>·</span>
                    <span>Dock: {currentOutlet.dockType}</span>
                  </div>
                </div>
              </div>

              {/* Digital PoD Receiving PIN Handshake Card */}
              <div className="bg-slate-900 text-white rounded-2xl p-3.5 px-4 flex items-center justify-between sm:justify-end gap-3 shadow-sm shrink-0">
                <div className="text-right">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 block">
                    Receiving PIN
                  </span>
                  <span className="text-[11px] text-slate-300">
                    Handshake with Driver
                  </span>
                </div>
                <div className="bg-slate-800 border border-slate-700 px-3.5 py-1.5 rounded-xl font-mono text-xl font-extrabold tracking-widest text-emerald-300 shadow-inner">
                  {currentOutlet.receivingPin}
                </div>
              </div>
            </div>

            {/* Disruption Alert Notice (Mid-Shift Lineage from Dispatcher) */}
            {currentOutlet.id === 'OUT-1029' && (
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3 shadow-2xs">
                <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="text-xs">
                  <p className="font-bold text-amber-900">
                    Dispatcher Mid-Shift Disruption Notice · Order ORD-30088
                  </p>
                  <p className="text-amber-800 mt-0.5 leading-relaxed">
                    Vehicle VEH006 reported mechanical seizure en route on A1 Highway. Your order was deferred due to delivery window closure and assigned <strong>Anti-Starvation Priority 1</strong> for guaranteed next-run departure.
                  </p>
                </div>
              </div>
            )}

            {currentOutlet.id === 'OUT-4089' && (
              <div className="bg-sky-50 border border-sky-200 rounded-2xl p-4 flex items-start gap-3 shadow-2xs">
                <Info className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
                <div className="text-xs">
                  <p className="font-bold text-sky-900">
                    Recovery Plan Deployed · Cargo Transferred to VEH014 (Trip 2)
                  </p>
                  <p className="text-sky-800 mt-0.5 leading-relaxed">
                    Due to Bay 3 dock lift seizure on VEH011, your staged chilled goods were reassigned to VEH014's returning open slot. Revised estimated arrival at Nugegoda: <strong>09:45 AM</strong>.
                  </p>
                </div>
              </div>
            )}

            {/* Segmented Control Header: Active Inbound vs Deferred */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200/60 shadow-2xs">
                <button
                  type="button"
                  onClick={() => setOrdersSegmentTab('progress')}
                  className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition cursor-pointer ${
                    ordersSegmentTab === 'progress'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <span>Active Inbound Deliveries</span>
                  <span className="rounded-full bg-slate-100 text-slate-700 px-1.5 py-0.5 text-[11px] font-mono font-medium">
                    {activeInboundVehicles.length}
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => setOrdersSegmentTab('deferred')}
                  className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition cursor-pointer ${
                    ordersSegmentTab === 'deferred'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <span>Deferred Allocations</span>
                  <span className="rounded-full bg-amber-100 text-amber-800 font-bold px-1.5 py-0.5 text-[11px] font-mono">
                    {currentOutlet.consecutiveSkips > 0 ? 1 : 0}
                  </span>
                </button>
              </div>

              <span className="text-xs text-slate-500 font-medium">
                {ordersSegmentTab === 'progress'
                  ? `${activeInboundVehicles.length} vehicle runs scheduled today`
                  : 'Protected by Waypoint Anti-Starvation Rules'}
              </span>
            </div>

            {/* Tab 1: Active Inbound Deliveries */}
            {ordersSegmentTab === 'progress' && (
              <div className="space-y-4">
                {activeInboundVehicles.map((vehicle) => {
                  const isExpanded = !!expandedVehicles[vehicle.id];
                  const verification = verifiedShipments[vehicle.id];

                  return (
                    <div
                      key={vehicle.id}
                      className="bg-white border border-gray-200/80 rounded-2xl p-4 sm:p-5 shadow-xs transition-all"
                    >
                      {/* Vehicle Header Strip */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3 pb-3 border-b border-slate-100">
                        <div className="flex items-center flex-wrap gap-2.5">
                          <button
                            type="button"
                            onClick={() => toggleVehicle(vehicle.id)}
                            className="flex items-center gap-1.5 text-base font-bold text-[#0B2019] hover:text-[#059669] transition cursor-pointer"
                          >
                            <span>{vehicle.id}</span>
                            <span className="p-0.5 rounded-md hover:bg-gray-100 text-gray-500">
                              {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                            </span>
                          </button>

                          <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-slate-100 text-slate-700">
                            {vehicle.vehicleType}
                          </span>

                          <span
                            className={`px-2 py-0.5 rounded-md text-xs font-semibold ${
                              vehicle.category.includes('Chilled')
                                ? 'bg-sky-50 text-sky-700 border border-sky-200'
                                : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            }`}
                          >
                            {vehicle.category}
                          </span>

                          <span className="text-xs text-gray-500 font-normal">
                            {vehicle.schedule}
                          </span>
                        </div>

                        {/* Status & Action */}
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-[#E8F7F0] text-[#059669]">
                            <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse mr-1.5" />
                            {vehicle.status}
                          </span>

                          <button
                            type="button"
                            onClick={() => handleOpenInspect(vehicle)}
                            className={`px-3 py-1 rounded-full text-xs font-bold transition shadow-2xs flex items-center gap-1 cursor-pointer ${
                              verification
                                ? 'bg-slate-900 text-white'
                                : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                            }`}
                          >
                            {verification ? (
                              <>
                                <FileCheck size={12} className="text-emerald-400" />
                                <span>Receipt Signed</span>
                              </>
                            ) : (
                              <>
                                <Check size={12} />
                                <span>Inspect & Accept</span>
                              </>
                            )}
                          </button>
                        </div>
                      </div>

                      {/* Milestone Progress Stepper */}
                      <div className="relative w-full py-1">
                        <div className="flex items-center justify-between relative">
                          {vehicle.milestones.map((_, idx) => (
                            <React.Fragment key={idx}>
                              <div className="relative z-10 flex items-center justify-center">
                                {renderNode(idx, vehicle.activeStageIndex)}
                              </div>
                              {idx < vehicle.milestones.length - 1 && (
                                <div className="flex-1 mx-1 h-0.5 rounded-full overflow-hidden transition-all duration-700">
                                  <div
                                    className={`h-full w-full ${
                                      vehicle.activeStageIndex > idx ? 'bg-emerald-600' : 'bg-slate-200'
                                    }`}
                                  />
                                </div>
                              )}
                            </React.Fragment>
                          ))}
                        </div>

                        {/* Step Labels */}
                        <div className="flex justify-between items-start mt-2">
                          {vehicle.milestones.map((milestone, idx) => {
                            const isCompleted = idx < vehicle.activeStageIndex;
                            const isActive = idx === vehicle.activeStageIndex;
                            return (
                              <div key={idx} className="w-1/4 flex flex-col text-center items-center">
                                <p
                                  className={`text-[11px] ${
                                    isActive
                                      ? 'font-bold text-emerald-800'
                                      : isCompleted
                                      ? 'font-medium text-slate-700'
                                      : 'font-medium text-slate-400'
                                  }`}
                                >
                                  {milestone.label}
                                </p>
                                <p className="text-[10px] font-mono text-slate-400 mt-0.5">
                                  {milestone.time}
                                </p>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Expandable Manifest Dropdown */}
                      {isExpanded && (
                        <div className="mt-4 pt-3 border-t border-slate-100">
                          <div className="bg-[#F8FAF9] border border-gray-200/70 rounded-xl p-3.5">
                            <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-gray-200/60 text-xs">
                              <div className="flex items-center gap-2">
                                <span className="text-gray-500 font-normal">Assigned Driver:</span>
                                <span className="font-bold text-gray-900">{vehicle.driver.name}</span>
                                <span className="text-gray-300">·</span>
                                <a
                                  href={`tel:${vehicle.driver.number}`}
                                  className="inline-flex items-center gap-1 font-semibold text-[#059669] hover:underline"
                                >
                                  <Phone size={11} />
                                  <span>{vehicle.driver.number}</span>
                                </a>
                              </div>
                              <span className="text-[11px] text-gray-500 font-medium">
                                {vehicle.products.length} line items on this manifest
                              </span>
                            </div>

                            <div className="overflow-x-auto">
                              <table className="w-full text-left text-xs">
                                <thead>
                                  <tr className="text-gray-500 border-b border-gray-200/60 font-medium">
                                    <th className="pb-1.5 pl-1 font-semibold">Product Description</th>
                                    <th className="pb-1.5 font-semibold">Order Ref</th>
                                    <th className="pb-1.5 font-semibold">Temperature Profile</th>
                                    <th className="pb-1.5 pr-1 text-right font-semibold">Manifest Qty</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                  {vehicle.products.map((item, idx) => (
                                    <tr key={idx} className="hover:bg-white transition-colors">
                                      <td className="py-2 pl-1 font-medium text-gray-900 flex items-center gap-1.5">
                                        <Package size={13} className="text-slate-400" />
                                        <span>{item.name}</span>
                                      </td>
                                      <td className="py-2 font-mono font-semibold text-[#059669]">
                                        {item.orderNo}
                                      </td>
                                      <td className="py-2 text-slate-600">
                                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700">
                                          {item.category}
                                        </span>
                                      </td>
                                      <td className="py-2 pr-1 text-right font-bold text-slate-800">
                                        {item.quantity}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Tab 2: Deferred Allocations */}
            {ordersSegmentTab === 'deferred' && (
              <div className="rounded-2xl border border-amber-200 bg-amber-50/50 p-5 shadow-2xs space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex gap-3.5">
                    <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0 shadow-xs">
                      <AlertCircle className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-slate-900">
                          {currentOutlet.id === 'OUT-1029'
                            ? 'Inverter Refrigerators & OLED TVs (ORD-30088)'
                            : 'Pelwatte Pasteurized Fresh Milk 1L (ORD-30082)'}
                        </h3>
                        <span className="font-mono text-xs text-amber-900 font-bold bg-amber-100 px-2 py-0.5 rounded">
                          Deferred by Dispatcher
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-slate-600">
                        {currentOutlet.id === 'OUT-1029'
                          ? 'En-route vehicle breakdown (VEH006) on A1 Highway. Fresh access window closed before secondary vehicle departure.'
                          : 'Reefer compartment volume cap exceeded on Peliyagoda Trip 1. Protected by Anti-Starvation Rule.'}
                      </p>
                      <div className="mt-2.5 flex items-center gap-3 text-xs text-slate-500">
                        <span>Rescheduled Run: <strong className="text-slate-900 font-mono">Trip 2 / Next Wave</strong></span>
                        <span>·</span>
                        <span>Consecutive Skips: <strong className="text-slate-900">0 of 1 allowed</strong></span>
                      </div>
                    </div>
                  </div>

                  <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-emerald-100 text-emerald-800 text-xs font-bold border border-emerald-200">
                    Priority Lock Active
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* 2. PLACE ORDER TAB: Smart Multi-Brand Ordering Engine */}
        {/* ============================================================== */}
        {activeTab === 'Place order' && (
          <div className="flex flex-col gap-4">
            {/* Header: Title + 4 PM Cutoff Countdown Badge + Cutoff Simulator */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                    Order Requisition — {currentOutlet.name}
                  </h2>
                  <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                    {currentOutlet.brand}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Standard Delivery Window: <strong className="text-slate-800">{currentOutlet.deliveryWindow}</strong> (Arrive before {currentOutlet.mustArriveBefore})
                </p>
              </div>

              {/* 4 PM Cutoff & Simulator Pill */}
              <div className="flex items-center gap-2 self-start sm:self-auto">
                <div
                  className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border shadow-2xs text-xs font-bold ${
                    isSimulatedPastCutoff
                      ? 'bg-rose-50 border-rose-200 text-rose-800'
                      : 'bg-amber-50 border-amber-200 text-amber-800'
                  }`}
                >
                  <AlertTriangle size={13} className={isSimulatedPastCutoff ? 'text-rose-600' : 'text-amber-600'} />
                  <span>
                    {isSimulatedPastCutoff
                      ? 'Past 4:00 PM Cutoff · Day +2 Run'
                      : '4:00 PM Daily Cutoff · 6h 46m Left'}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => setIsSimulatedPastCutoff(!isSimulatedPastCutoff)}
                  className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-lg transition cursor-pointer"
                  title="Test how the system behaves after 4 PM cutoff"
                >
                  {isSimulatedPastCutoff ? 'Reset Cutoff' : 'Simulate > 4 PM'}
                </button>
              </div>
            </div>

            {/* Cutoff Warning Banner if Simulated Past 4 PM */}
            {isSimulatedPastCutoff && (
              <div className="bg-amber-50/90 border border-amber-200 rounded-2xl p-3.5 text-xs text-amber-900 flex items-start gap-2.5 shadow-2xs">
                <Clock size={16} className="text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Operating Rule Enforced: Late Order Cutoff</span>
                  <p className="mt-0.5 text-amber-800 leading-relaxed">
                    Per Waypoint distribution policy, orders confirmed after 4:00 PM close enter the subsequent delivery run. Your shipment will arrive on <strong>Saturday morning</strong>.
                  </p>
                </div>
              </div>
            )}

            {/* Main Ordering Workspace: 2-Column Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
              {/* Left Column: Product Catalog & Category Filters */}
              <div className="lg:col-span-2 bg-white border border-gray-200/80 rounded-2xl p-5 shadow-xs flex flex-col h-[540px]">
                {/* Catalog Controls: Category Pills & Search */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-gray-100 shrink-0">
                  {/* Category Filter Pills */}
                  <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
                    {catalogCategories.map((cat) => (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => setSelectedCategoryFilter(cat)}
                        className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer shrink-0 ${
                          selectedCategoryFilter === cat
                            ? 'bg-slate-900 text-white'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>

                  {/* Search Bar */}
                  <div className="relative w-full sm:w-56">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
                    <input
                      type="text"
                      value={catalogSearch}
                      onChange={(e) => setCatalogSearch(e.target.value)}
                      placeholder="Search catalog..."
                      className="w-full h-8 pl-8 pr-7 text-xs font-medium text-slate-900 bg-white border border-gray-200 rounded-lg placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                    {catalogSearch && (
                      <button
                        type="button"
                        onClick={() => setCatalogSearch('')}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
                      >
                        <X size={13} />
                      </button>
                    )}
                  </div>
                </div>

                {/* Scrollable Products Table */}
                <div className="flex-1 overflow-y-auto min-h-0 divide-y divide-gray-100 pr-1 mt-2">
                  <table className="w-full text-left text-xs relative">
                    <thead className="sticky top-0 z-10 bg-white shadow-2xs">
                      <tr className="bg-[#F8FAFC] text-slate-500 font-semibold select-none">
                        <th
                          onClick={() => handleSortToggle('id')}
                          className="py-2.5 px-3 rounded-l-lg cursor-pointer hover:text-slate-800 transition"
                        >
                          <div className="flex items-center gap-1">
                            <span>Code</span>
                            {catalogSortField === 'id' ? (
                              catalogSortDirection === 'asc' ? <ArrowUp size={11} className="text-emerald-600" /> : <ArrowDown size={11} className="text-emerald-600" />
                            ) : (
                              <ArrowUpDown size={11} className="text-slate-300" />
                            )}
                          </div>
                        </th>
                        <th
                          onClick={() => handleSortToggle('name')}
                          className="py-2.5 px-3 cursor-pointer hover:text-slate-800 transition"
                        >
                          <div className="flex items-center gap-1">
                            <span>Item Name</span>
                            {catalogSortField === 'name' ? (
                              catalogSortDirection === 'asc' ? <ArrowUp size={11} className="text-emerald-600" /> : <ArrowDown size={11} className="text-emerald-600" />
                            ) : (
                              <ArrowUpDown size={11} className="text-slate-300" />
                            )}
                          </div>
                        </th>
                        <th className="py-2.5 px-3">Packaging</th>
                        <th className="py-2.5 px-3 text-right rounded-r-lg">Order Qty</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {sortedCatalog.length === 0 ? (
                        <tr>
                          <td colSpan="4" className="py-12 text-center text-slate-500">
                            No products match your filter criteria.
                          </td>
                        </tr>
                      ) : (
                        sortedCatalog.map((item) => (
                          <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                            <td className="py-2 px-3 font-mono font-semibold text-slate-700">
                              {item.id}
                            </td>
                            <td className="py-2 px-3">
                              <div className="flex items-center gap-1.5">
                                <span className="font-semibold text-slate-900">{item.name}</span>
                                {item.subType && (
                                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600">
                                    {item.subType}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-2 px-3 text-slate-500">{item.format}</td>
                            <td className="py-2 px-3 text-right">
                              <input
                                type="number"
                                min="0"
                                value={orderQuantities[item.id] ?? 0}
                                onChange={(e) => handleQtyChange(item.id, e.target.value)}
                                className="w-16 h-7 text-center font-bold text-slate-900 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-600"
                              />
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Right Column: Order Summary & Dual-Dispatch Calculator */}
              <div className="lg:col-span-1 bg-white border border-gray-200/80 rounded-2xl p-5 shadow-xs flex flex-col gap-4">
                <div className="flex items-center justify-between pb-2 border-b border-gray-100">
                  <h3 className="font-bold text-slate-900 text-sm">Order Summary</h3>
                  <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                    {currentOutlet.brand}
                  </span>
                </div>

                {/* Metrics List */}
                <div className="divide-y divide-gray-100 text-xs">
                  <div className="flex items-center justify-between py-2">
                    <span className="text-slate-500 font-normal">Line items</span>
                    <span className="font-bold text-slate-900 font-mono">{activeLineItems.length} lines</span>
                  </div>

                  <div className="flex items-center justify-between py-2">
                    <span className="text-slate-500 font-normal">Total units</span>
                    <span className="font-bold text-slate-900 font-mono">{totalOrderedUnits} units</span>
                  </div>

                  <div className="flex items-center justify-between py-2">
                    <span className="text-slate-500 font-normal">Estimated gross weight</span>
                    <span className="font-bold text-slate-900 font-mono">~{estTotalWeightKg} kg</span>
                  </div>

                  <div className="flex items-center justify-between py-2">
                    <span className="text-slate-500 font-normal">Estimated volume</span>
                    <span className="font-bold text-slate-900 font-mono">{estTotalVolumeM3} m³</span>
                  </div>

                  <div className="flex items-center justify-between py-2">
                    <span className="text-slate-500 font-normal">Delivery Window</span>
                    <span className="font-bold text-slate-900">{currentOutlet.deliveryWindow}</span>
                  </div>
                </div>

                {/* Automated Dual-Dispatch Split Box for Fresh */}
                {currentOutlet.brand === 'Waypoint Fresh' ? (
                  <div className="bg-[#F0FDF4] border border-[#DCFCE7] rounded-xl p-3 text-xs space-y-1.5">
                    <div className="flex items-center gap-1.5">
                      <span className="w-5 h-5 rounded-full bg-[#059669] text-white flex items-center justify-center font-bold text-[11px]">
                        {dispatchesCount}
                      </span>
                      <span className="font-bold text-slate-900">
                        {dispatchesCount === 1 ? '1 Vehicle Run Required' : '2 Separate Dispatches Required'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                      {dispatchesCount > 1
                        ? 'Dry staples and chilled dairy/produce require distinct vehicle climate controls (Ambient Dry Truck + Reefer Truck).'
                        : 'Your order matches a single temperature profile.'}
                    </p>
                    {dispatchesCount > 1 && (
                      <div className="pt-1.5 border-t border-emerald-200/60 flex items-center justify-between text-[11px] font-semibold text-slate-700">
                        <span>Dry: {dryItems.length} lines</span>
                        <span>Chilled: {chilledItems.length} lines</span>
                      </div>
                    )}
                  </div>
                ) : currentOutlet.brand === 'Waypoint Style' ? (
                  <div className="bg-purple-50 border border-purple-200 rounded-xl p-3 text-xs space-y-1">
                    <span className="font-bold text-purple-900 flex items-center gap-1">
                      <Layers size={13} />
                      Volume Capacity Alert
                    </span>
                    <p className="text-[11px] text-purple-800 leading-relaxed">
                      Garments on hangers consume volumetric capacity before weight. Order volume ({estTotalVolumeM3} m³) will be verified against mall access height (3.2m).
                    </p>
                  </div>
                ) : (
                  <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-xs space-y-1">
                    <span className="font-bold text-blue-900 flex items-center gap-1">
                      <ShieldCheck size={13} />
                      Fragile Heavy Cargo Notice
                    </span>
                    <p className="text-[11px] text-blue-800 leading-relaxed">
                      Major appliances require tail-lift trucks and dedicated upright cargo strap staging at Peliyagoda DC.
                    </p>
                  </div>
                )}

                {/* Primary Order Action Button */}
                <button
                  type="button"
                  onClick={() => setConfirmOrderModalOpen(true)}
                  disabled={activeLineItems.length === 0}
                  className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 disabled:opacity-40 text-white font-bold rounded-xl shadow-xs text-xs transition cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <Package size={14} />
                  <span>Review & Confirm Order ({activeLineItems.length})</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* 3. RECEIPTS & DEFERRALS TAB: Audit Trail & Anti-Starvation Rules */}
        {/* ============================================================== */}
        {activeTab === 'Receipts & Deferrals' && (
          <div className="flex flex-col gap-5">
            {/* Header Strip & Filters */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs">
              <div>
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                  Receipts, Proof of Delivery & Deferrals
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Complete audit trail for {currentOutlet.name} ({currentOutlet.id})
                </p>
              </div>

              {/* Status Filter Pills */}
              <div className="flex items-center gap-1.5 self-start sm:self-auto">
                {['All', 'Delivered', 'Deferred'].map((f) => (
                  <button
                    key={f}
                    type="button"
                    onClick={() => setHistoryFilter(f)}
                    className={`px-3 py-1 rounded-full text-xs font-semibold transition cursor-pointer ${
                      historyFilter === f
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>

            {/* Anti-Starvation Policy Explainer Banner */}
            <div className="bg-emerald-50/70 border border-emerald-200/80 rounded-2xl p-4 flex items-start gap-3 shadow-2xs">
              <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <div className="text-xs">
                <span className="font-bold text-emerald-950">
                  Waypoint Anti-Starvation Protection Policy Active
                </span>
                <p className="text-emerald-800 mt-0.5 leading-relaxed">
                  To prevent outlets from being skipped on consecutive runs when demand exceeds capacity, deferred orders are automatically granted <strong>Priority Lock</strong> for the subsequent delivery wave.
                </p>
              </div>
            </div>

            {/* Order History Table */}
            <div className="bg-white border border-gray-200/80 rounded-2xl p-5 shadow-xs">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-[#F8FAFC] text-slate-500 font-semibold select-none">
                      <th className="py-2.5 px-3 rounded-l-lg">Date</th>
                      <th className="py-2.5 px-3">Order Ref</th>
                      <th className="py-2.5 px-3">Cargo Description</th>
                      <th className="py-2.5 px-3">Quantity</th>
                      <th className="py-2.5 px-3">Category</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3 text-right rounded-r-lg">Inspection</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {orderHistoryList
                      .filter((item) => historyFilter === 'All' || item.outcome === historyFilter)
                      .map((item) => {
                        const isExpanded = !!expandedHistoryRows[item.orderNo];
                        return (
                          <React.Fragment key={item.orderNo}>
                            <tr
                              onClick={() => toggleHistoryRow(item.orderNo)}
                              className={`hover:bg-slate-50 transition cursor-pointer ${
                                item.highlight ? 'bg-emerald-50/30' : ''
                              }`}
                            >
                              <td className="py-3 px-3 font-semibold text-slate-700">{item.date}</td>
                              <td className="py-3 px-3 font-mono font-bold text-slate-900">{item.orderNo}</td>
                              <td className="py-3 px-3 font-medium text-slate-800">{item.product}</td>
                              <td className="py-3 px-3 font-mono">{item.quantity}</td>
                              <td className="py-3 px-3 text-slate-500">{item.type}</td>
                              <td className="py-3 px-3">
                                <span
                                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                                    item.outcome === 'Deferred'
                                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                      : item.outcome === 'Delivered'
                                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                      : 'bg-amber-50 text-amber-700 border border-amber-200'
                                  }`}
                                >
                                  {item.outcome}
                                </span>
                              </td>
                              <td className="py-3 px-3 text-right">
                                <span className="p-1 rounded-md text-slate-400 inline-block">
                                  {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                </span>
                              </td>
                            </tr>

                            {/* Dropdown Audit Details */}
                            {isExpanded && (
                              <tr className="bg-slate-50/50">
                                <td colSpan={7} className="px-4 py-3">
                                  {item.outcome === 'Deferred' ? (
                                    <div className="bg-rose-50 border border-rose-200 rounded-xl p-3.5 text-xs space-y-2">
                                      <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-1.5 font-bold text-rose-950">
                                          <AlertCircle size={14} className="text-rose-600" />
                                          <span>Deferral Reason Logged by Dispatcher</span>
                                        </div>
                                        <span className="px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                                          Anti-Starvation Priority Active
                                        </span>
                                      </div>
                                      <p className="text-rose-800 leading-relaxed text-[11px]">
                                        {item.deferralReason}
                                      </p>
                                    </div>
                                  ) : (
                                    <div className="bg-white border border-slate-200 rounded-xl p-3.5 text-xs flex flex-wrap items-center justify-between gap-4">
                                      <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-1.5">
                                          <Truck size={14} className="text-[#059669]" />
                                          <span className="text-slate-500">Delivery Vehicle:</span>
                                          <strong className="font-mono text-slate-900">{item.deliveryTruck}</strong>
                                        </div>
                                        <div className="flex items-center gap-1.5">
                                          <Clock size={14} className="text-[#059669]" />
                                          <span className="text-slate-500">Time:</span>
                                          <strong className="text-slate-900">{item.deliveryTime}</strong>
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-3">
                                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-emerald-300 font-mono font-bold text-[11px]">
                                          <ShieldCheck size={13} />
                                          PIN Verified: {item.pinUsed}
                                        </span>
                                      </div>
                                    </div>
                                  )}
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
      </main>

      {/* Inspect & Accept Delivery Modal */}
      <InspectDeliveryModal
        isOpen={inspectModalOpen}
        onClose={() => setInspectModalOpen(false)}
        vehicle={selectedInspectVehicle}
        outlet={currentOutlet}
        onConfirmReceipt={handleConfirmInspectionReceipt}
      />

      {/* Review & Confirm Order Modal */}
      <OrderConfirmationModal
        isOpen={confirmOrderModalOpen}
        onClose={() => setConfirmOrderModalOpen(false)}
        outlet={currentOutlet}
        orderLines={activeLineItems}
        totals={orderTotals}
        isPastCutoff={isSimulatedPastCutoff}
        onFinalSubmit={handleFinalOrderSubmit}
      />
    </div>
  );
}
