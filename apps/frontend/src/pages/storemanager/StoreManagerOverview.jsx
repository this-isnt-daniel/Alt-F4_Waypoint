import React, { useState } from 'react';
import waypointLogo from '../../assets/icons/waypoint_logo.png';
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
  X
} from 'lucide-react';

export default function StoreManagerOverview({ onLogout }) {
  const [activeTab, setActiveTab] = useState('Overview');
  const [ordersTab, setOrdersTab] = useState('progress'); // 'progress' | 'deferred'
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [hasUnreadNotifications, setHasUnreadNotifications] = useState(true);

  // Catalog products for Place Order screen
  const catalogProducts = [
    {
      id: 'PRD-101',
      name: 'Rice',
      category: 'Dry',
      format: '5kg case',
      unitWeightKg: 5,
      unitVolumeM3: 0.05,
    },
    {
      id: 'PRD-102',
      name: 'Cooking oil',
      category: 'Dry',
      format: '1L bottle',
      unitWeightKg: 1,
      unitVolumeM3: 0.02,
    },
    {
      id: 'PRD-103',
      name: 'Wheat flour',
      category: 'Dry',
      format: '1kg pack',
      unitWeightKg: 1,
      unitVolumeM3: 0.02,
    },
    {
      id: 'PRD-104',
      name: 'Ceylon Black Tea',
      category: 'Dry',
      format: '400g box',
      unitWeightKg: 0.4,
      unitVolumeM3: 0.01,
    },
    {
      id: 'PRD-105',
      name: 'White Sugar',
      category: 'Dry',
      format: '1kg pack',
      unitWeightKg: 1,
      unitVolumeM3: 0.02,
    },
    {
      id: 'PRD-201',
      name: 'Dairy',
      category: 'Chilled',
      subType: 'Chilled',
      format: 'crate',
      unitWeightKg: 12,
      unitVolumeM3: 0.06,
    },
    {
      id: 'PRD-202',
      name: 'Frozen produce',
      category: 'Chilled',
      subType: 'Frozen',
      format: 'case',
      unitWeightKg: 8,
      unitVolumeM3: 0.05,
    },
    {
      id: 'PRD-203',
      name: 'Pure Butter',
      category: 'Chilled',
      subType: 'Chilled',
      format: '227g block',
      unitWeightKg: 0.25,
      unitVolumeM3: 0.01,
    },
  ];

  // Quantities keyed by product ID
  const [orderQuantities, setOrderQuantities] = useState({
    'PRD-101': 12,
    'PRD-102': 24,
    'PRD-103': 30,
    'PRD-201': 8,
    'PRD-202': 5,
  });

  const [catalogSearch, setCatalogSearch] = useState('');
  const [catalogSortField, setCatalogSortField] = useState('id'); // 'id' | 'name'
  const [catalogSortDirection, setCatalogSortDirection] = useState('asc'); // 'asc' | 'desc'
  const [orderConfirmed, setOrderConfirmed] = useState(false);

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

  // Filtered and sorted catalog items
  const filteredCatalog = catalogProducts.filter((item) => {
    const q = catalogSearch.toLowerCase().trim();
    if (!q) return true;
    return (
      item.id.toLowerCase().includes(q) ||
      item.name.toLowerCase().includes(q) ||
      item.format.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q) ||
      (item.subType && item.subType.toLowerCase().includes(q))
    );
  });

  const sortedCatalog = [...filteredCatalog].sort((a, b) => {
    let comparison = 0;
    if (catalogSortField === 'id') {
      comparison = a.id.localeCompare(b.id, undefined, { numeric: true });
    } else {
      comparison = a.name.localeCompare(b.name);
    }
    return catalogSortDirection === 'asc' ? comparison : -comparison;
  });

  // Calculate active order metrics
  const activeLineItems = catalogProducts.filter(
    (p) => (orderQuantities[p.id] || 0) > 0
  );
  const totalOrderedUnits = Object.values(orderQuantities).reduce((acc, qty) => acc + (qty || 0), 0);
  
  const dryItemsOrdered = catalogProducts.filter(
    (p) => p.category === 'Dry' && (orderQuantities[p.id] || 0) > 0
  );
  const chilledItemsOrdered = catalogProducts.filter(
    (p) => p.category === 'Chilled' && (orderQuantities[p.id] || 0) > 0
  );
  const dispatchesCount = (dryItemsOrdered.length > 0 ? 1 : 0) + (chilledItemsOrdered.length > 0 ? 1 : 0);

  const estTotalVolumeM3 = (
    (orderQuantities['PRD-101'] || 0) * 0.038 +
    (orderQuantities['PRD-102'] || 0) * 0.038 +
    (orderQuantities['PRD-103'] || 0) * 0.038 +
    (orderQuantities['PRD-201'] || 0) * 0.054 +
    (orderQuantities['PRD-202'] || 0) * 0.054
  ).toFixed(1);

  const estTotalWeightKg = Math.round(
    catalogProducts.reduce((sum, item) => sum + (orderQuantities[item.id] || 0) * item.unitWeightKg, 0)
  );

  // Tracks which vehicle dropdown is expanded (by ID)
  const [expandedVehicles, setExpandedVehicles] = useState({ 'VH-30302': true });

  // Tracks which Receipts & Deferrals row is expanded (by Order No)
  const [expandedHistoryRows, setExpandedHistoryRows] = useState({ 'ORD-30295': true });

  const toggleVehicle = (id) => {
    setExpandedVehicles((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const toggleHistoryRow = (orderNo) => {
    setExpandedHistoryRows((prev) => ({
      ...prev,
      [orderNo]: !prev[orderNo],
    }));
  };

  const navTabs = [
    'Overview',
    'Place order',
    'Receipts & Deferrals',
  ];

  // Order history data for Receipts & Deferrals page
  const orderHistory = [
    {
      date: 'Sep 29',
      orderNo: 'ORD-30295',
      product: 'Munchee Super Cream Cracker 500g',
      quantity: '12 cases',
      type: 'Dry',
      outcome: 'Deferred',
      highlight: true,
      deferralReason: 'Fleet capacity short — moved to Friday. Priority rollover active for next delivery window.',
    },
    {
      date: 'Sep 27',
      orderNo: 'ORD-30288',
      product: 'Anchor Salted Pure Butter 227g',
      quantity: '8 cases',
      type: 'Chilled',
      outcome: 'Delivered',
      deliveryTruck: 'VH-30288',
      deliveryTime: '8:15 AM',
    },
    {
      date: 'Sep 24',
      orderNo: 'ORD-30270',
      product: 'Pelwatte Fresh Milk 1L & Milk Powder',
      quantity: '20 cases',
      type: 'Dry + chilled',
      outcome: 'Delivered',
      deliveryTruck: 'VH-30270',
      deliveryTime: '7:38 AM',
    },
    {
      date: 'Sep 22',
      orderNo: 'ORD-30250',
      product: 'Dilmah Premium Ceylon Tea 100pk',
      quantity: '15 packs',
      type: 'Dry',
      outcome: 'Delivered',
      deliveryTruck: 'VH-30250',
      deliveryTime: '7:45 AM',
    },
  ];

  // Vehicle data with split order allocations, driver details, and explicit milestone clusters
  const activeVehicles = [
    {
      id: 'VH-30301',
      category: 'Dry',
      schedule: 'Placed Wed · Expected 7:40 AM Thu',
      status: 'Loaded',
      activeStageIndex: 1, // 'Loaded Bay 4'
      driver: {
        name: 'Kamal Perera',
        number: '+94 77 234 5678',
      },
      milestones: [
        { label: 'Order Placed', time: 'Wed 4:00 PM' },
        { label: 'Loaded Bay 4', time: 'Thu 4:30 AM' },
        { label: 'Out for Delivery', time: 'Est. 6:30 AM' },
        { label: 'Arrived at Curb', time: 'Est. 7:40 AM' },
      ],
      products: [
        {
          name: 'Munchee Super Cream Cracker 500g',
          orderNo: 'ORD-30301',
          category: 'Dry',
          quantity: '8 cases',
        },
        {
          name: 'Kotmale Full Cream Milk Powder 400g',
          orderNo: 'ORD-30302',
          category: 'Dry',
          quantity: '5 cases',
        },
        {
          name: 'CBL Tiara Layer Cake (Chocolate)',
          orderNo: 'ORD-30301',
          category: 'Dry',
          quantity: '3 cases',
        },
      ],
    },
    {
      id: 'VH-30302',
      category: 'Chilled',
      schedule: 'Placed Wed · Expected 7:40 AM Thu',
      status: 'Out for delivery',
      activeStageIndex: 2, // 'Out for Delivery'
      driver: {
        name: 'Rohan Wickramasinghe',
        number: '+94 71 890 1234',
      },
      milestones: [
        { label: 'Order Placed', time: 'Wed 4:00 PM' },
        { label: 'Loaded Bay 4', time: 'Thu 4:30 AM' },
        { label: 'Out for Delivery', time: 'Departed 6:15 AM' },
        { label: 'Arrived at Curb', time: 'Est. 7:40 AM' },
      ],
      products: [
        {
          name: 'Anchor Salted Pure Butter 227g',
          orderNo: 'ORD-30301',
          category: 'Chilled',
          quantity: '6 cases',
        },
        {
          name: 'Pelwatte Pasteurized Fresh Milk 1L',
          orderNo: 'ORD-30302',
          category: 'Chilled',
          quantity: '12 crates',
        },
        {
          name: 'Elephant House Premium Vanilla Ice Cream',
          orderNo: 'ORD-30302',
          category: 'Chilled',
          quantity: '4 tubs',
        },
      ],
    },
    {
      id: 'VH-30310',
      category: 'Dry',
      schedule: 'Placed today · Expected 7:40 AM Fri',
      status: 'Confirmed',
      activeStageIndex: 0, // 'Order Placed'
      driver: {
        name: 'Nuwan Pradeep',
        number: '+94 76 543 2109',
      },
      milestones: [
        { label: 'Order Placed', time: 'Today 2:15 PM' },
        { label: 'Loading Bay 2', time: 'Est. 4:00 AM Fri' },
        { label: 'Out for Delivery', time: 'Est. 6:15 AM Fri' },
        { label: 'Arrived at Curb', time: 'Est. 7:40 AM Fri' },
      ],
      products: [
        {
          name: 'Dilmah Premium Ceylon Tea 100pk',
          orderNo: 'ORD-30310',
          category: 'Dry',
          quantity: '4 cases',
        },
        {
          name: 'Maliban Smart Cream Cracker 490g',
          orderNo: 'ORD-30310',
          category: 'Dry',
          quantity: '7 cases',
        },
      ],
    },
  ];

  // Helper to render standardized node state
  const renderNode = (stepIndex, activeStageIndex) => {
    if (stepIndex < activeStageIndex) {
      // Completed Nodes (1 & 2): Solid emerald dot with small checkmark icon
      return (
        <div className="w-3.5 h-3.5 rounded-full bg-emerald-600 flex items-center justify-center text-white shadow-2xs">
          <Check size={9} strokeWidth={3} />
        </div>
      );
    }
    if (stepIndex === activeStageIndex) {
      // Active Node (3): Emerald radar beacon with subtle double-ring pulse
      return (
        <span className="relative flex h-3.5 w-3.5 items-center justify-center">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60 duration-1000" />
          <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-600 ring-2 ring-white shadow-2xs" />
        </span>
      );
    }
    // Pending Node (4): Hollow neutral ring
    return <span className="w-3 h-3 rounded-full border-2 border-slate-300 bg-white" />;
  };

  return (
    <div className={`min-h-screen w-full bg-[#FAFBFA] text-gray-900 font-sans antialiased ${activeTab === 'Place order' ? 'pb-2' : 'pb-16'}`}>
      {/* Top Navigation Bar */}
      <header className="w-full border-b border-gray-100 bg-white sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Left: Brand Logo & Navigation Tabs */}
          <div className="flex items-center gap-8">
            {/* Waypoint Logo + Brand */}
            <div className="flex items-center gap-2.5 cursor-pointer">
              <img
                src={waypointLogo}
                alt="Waypoint"
                className="w-7 h-7 object-contain rounded-lg shadow-xs"
              />
              <span
                className="text-xl font-bold tracking-tight text-[#0B2019]"
                style={{ fontFamily: "'Inter', sans-serif" }}
              >
                Waypoint
              </span>
            </div>

            {/* Navigation Pills */}
            <nav className="hidden md:flex items-center gap-1.5" aria-label="Portal Navigation">
              {navTabs.map((tab) => {
                const isActive = activeTab === tab;
                return (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setActiveTab(tab)}
                    className={`px-3.5 py-1.5 rounded-full text-sm font-medium transition-colors cursor-pointer ${
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

          {/* Right: Actions, Outlet Selector, Notifications & Profile */}
          <div className="flex items-center gap-3">
            {/* Outlet Selector Dropdown */}
            <div className="relative">
              <button
                type="button"
                className="inline-flex items-center gap-1 px-3 py-1 text-sm font-normal text-gray-700 bg-white border border-gray-200 hover:border-gray-300 rounded-full transition-colors cursor-pointer"
              >
                <span>Nugegoda</span>
                <ChevronDown size={14} className="text-gray-500" />
              </button>
            </div>

            {/* Notifications Button */}
            <button
              type="button"
              onClick={() => setHasUnreadNotifications(!hasUnreadNotifications)}
              title="Notifications"
              className="relative w-8 h-8 rounded-full border border-gray-200 hover:border-gray-300 bg-white flex items-center justify-center text-gray-600 hover:text-gray-900 transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#059669]"
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
                DP
              </button>

              {/* Simple Profile Dropdown */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-44 bg-white border border-gray-100 rounded-xl shadow-lg py-1 z-50">
                  <div className="px-3 py-2 border-b border-gray-100">
                    <p className="text-xs font-medium text-gray-900">Store Manager</p>
                    <p className="text-[11px] text-gray-500">outlet/OUT0043</p>
                  </div>
                  <button
                    onClick={() => {
                      setShowUserMenu(false);
                      if (onLogout) onLogout();
                    }}
                    className="w-full text-left px-3 py-2 text-xs text-red-600 hover:bg-red-50 transition-colors"
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
      <main className={`max-w-7xl mx-auto px-6 ${activeTab === 'Place order' ? 'py-4 flex flex-col gap-4' : 'py-6 flex flex-col gap-8'}`}>
        {/* Overview Tab Content */}
        {activeTab === 'Overview' && (
          <>
            {/* Today's Delivery Banner */}
            <section
              aria-label="Delivery Arrival Status"
              className="w-full bg-[#DCF8E6] border border-[#C1F2D1] rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 shadow-xs"
            >
          {/* Left: Status Icon and Details */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-[#059669] text-white flex items-center justify-center flex-shrink-0 shadow-xs">
              <Truck size={18} strokeWidth={2} />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-[#0B2019] leading-snug">
                Today's delivery arrived at 7:38 AM
              </h2>
              <p className="text-xs text-gray-600 mt-0.5">
                Dry + chilled · 13 cases · {isConfirmed ? 'Confirmed' : 'not yet confirmed'}
              </p>
            </div>
          </div>

          {/* Right: Confirm Receipt Button */}
          <div>
            <button
              type="button"
              onClick={() => setIsConfirmed(!isConfirmed)}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all shadow-xs cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#059669] ${
                isConfirmed
                  ? 'bg-emerald-800 text-white'
                  : 'bg-[#059669] hover:bg-[#047857] active:bg-[#065f46] text-white'
              }`}
            >
              {isConfirmed ? 'Receipt confirmed' : 'Confirm receipt'}
            </button>
          </div>
        </section>

        {/* Segmented Control Header & Content */}
        <section aria-label="Orders and Allocations" className="w-full flex flex-col gap-3.5">
          {/* Segmented Control Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200/60 shadow-2xs">
              <button
                type="button"
                onClick={() => setOrdersTab('progress')}
                className={`flex items-center gap-2 rounded-lg px-3 py-1 text-xs font-semibold transition cursor-pointer ${
                  ordersTab === 'progress'
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <span>Orders in progress</span>
                <span className="rounded-full bg-slate-100 text-slate-700 px-1.5 py-0.5 text-[11px] font-mono font-medium">
                  {activeVehicles.length}
                </span>
              </button>

              <button
                type="button"
                onClick={() => setOrdersTab('deferred')}
                className={`flex items-center gap-2 rounded-lg px-3 py-1 text-xs font-semibold transition cursor-pointer ${
                  ordersTab === 'deferred'
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <span>Deferred allocations</span>
                <span className="rounded-full bg-amber-100 text-amber-800 font-bold px-1.5 py-0.5 text-[11px] font-mono">
                  1
                </span>
              </button>
            </div>

            <span className="text-xs text-slate-400 font-medium">
              {ordersTab === 'progress'
                ? `${activeVehicles.length} active dispatches`
                : 'Protected by Anti-Starvation'}
            </span>
          </div>

          {/* Tab 1: Orders in Progress (Compact Refined Stepper) */}
          {ordersTab === 'progress' && (
            <div className="w-full bg-white border border-gray-200/80 rounded-2xl p-4 sm:p-5 shadow-xs">
            {/* Vehicle Rows */}
            <div className="divide-y divide-gray-100">
              {activeVehicles.map((vehicle) => {
                const isExpanded = !!expandedVehicles[vehicle.id];

                return (
                  <div key={vehicle.id} className="py-3.5 first:pt-0.5 last:pb-0.5">
                    {/* Top Row: Vehicle ID, Tag, Schedule and Status Pill with Live Shimmer Dot */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 mb-2.5">
                      {/* Left: Vehicle ID + Tag + Schedule + Dropdown Toggle */}
                      <div className="flex items-center flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => toggleVehicle(vehicle.id)}
                          className="flex items-center gap-1 text-sm font-bold text-[#0B2019] hover:text-[#059669] transition-colors cursor-pointer group"
                        >
                          <span>{vehicle.id}</span>
                          <span className="p-0.5 rounded-md group-hover:bg-gray-100 text-gray-500 transition-colors">
                            {isExpanded ? (
                              <ChevronUp size={14} strokeWidth={2.2} />
                            ) : (
                              <ChevronDown size={14} strokeWidth={2.2} />
                            )}
                          </span>
                        </button>

                        <span className="px-1.5 py-0.5 rounded-md text-[11px] font-medium text-gray-600 bg-gray-100">
                          {vehicle.category}
                        </span>

                        <span className="text-xs text-gray-500 font-normal">
                          {vehicle.schedule}
                        </span>
                      </div>

                      {/* Right: Status Pill with small green live dot */}
                      <div>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#E8F7F0] text-[#059669]">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse inline-block mr-1.5" />
                          {vehicle.status}
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar & Refined Stepper Nodes */}
                    <div className="relative w-full py-1">
                      <div className="flex items-center justify-between relative">
                        {/* Node 0 */}
                        <div className="relative z-10 flex items-center justify-center">
                          {renderNode(0, vehicle.activeStageIndex)}
                        </div>

                        {/* Segment 0 -> 1 */}
                        <div className="flex-1 mx-1 h-0.5 rounded-full overflow-hidden transition-all duration-700 ease-out">
                          <div
                            className={`h-full w-full ${
                              vehicle.activeStageIndex >= 1
                                ? 'bg-emerald-600'
                                : 'bg-slate-200'
                            }`}
                          />
                        </div>

                        {/* Node 1 */}
                        <div className="relative z-10 flex items-center justify-center">
                          {renderNode(1, vehicle.activeStageIndex)}
                        </div>

                        {/* Segment 1 -> 2 */}
                        <div className="flex-1 mx-1 h-0.5 rounded-full overflow-hidden transition-all duration-700 ease-out">
                          <div
                            className={`h-full w-full ${
                              vehicle.activeStageIndex >= 2
                                ? 'bg-emerald-600'
                                : 'bg-slate-200'
                            }`}
                          />
                        </div>

                        {/* Node 2 */}
                        <div className="relative z-10 flex items-center justify-center">
                          {renderNode(2, vehicle.activeStageIndex)}
                        </div>

                        {/* Segment 2 -> 3 */}
                        <div className="flex-1 mx-1 h-0.5 rounded-full overflow-hidden transition-all duration-700 ease-out">
                          <div
                            className={`h-full w-full ${
                              vehicle.activeStageIndex >= 3
                                ? 'bg-emerald-600'
                                : 'bg-slate-200'
                            }`}
                          />
                        </div>

                        {/* Node 3 */}
                        <div className="relative z-10 flex items-center justify-center">
                          {renderNode(3, vehicle.activeStageIndex)}
                        </div>
                      </div>

                      {/* 1. Explicit Step Labels Under Each Node */}
                      <div className="flex justify-between items-start mt-1.5">
                        {vehicle.milestones.map((milestone, idx) => {
                          const isCompleted = idx < vehicle.activeStageIndex;
                          const isActive = idx === vehicle.activeStageIndex;

                          const alignClass =
                            idx === 0
                              ? 'text-left items-start'
                              : idx === vehicle.milestones.length - 1
                              ? 'text-right items-end'
                              : 'text-center items-center';

                          return (
                            <div key={idx} className={`w-1/4 flex flex-col ${alignClass}`}>
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

                    {/* Dropdown Manifest Table: Split Products & Orders allocated to this vehicle */}
                    <div
                      className={`overflow-hidden transition-all duration-300 ease-in-out ${
                        isExpanded
                          ? 'max-h-96 opacity-100 mt-3'
                          : 'max-h-0 opacity-0 mt-0 pointer-events-none'
                      }`}
                    >
                      <div className="bg-[#F8FAF9] border border-gray-200/70 rounded-xl p-3">
                        <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-gray-200/50">
                          <div className="flex items-center gap-2 text-xs">
                            <span className="text-gray-500 font-normal">Driver:</span>
                            <span className="font-semibold text-gray-900">{vehicle.driver.name}</span>
                            <span className="text-gray-300">·</span>
                            <a
                              href={`tel:${vehicle.driver.number}`}
                              className="inline-flex items-center gap-1 font-medium text-[#059669] hover:text-[#047857] hover:underline"
                            >
                              <Phone size={11} strokeWidth={2.2} />
                              <span>{vehicle.driver.number}</span>
                            </a>
                          </div>
                          <span className="text-[10px] text-gray-500 font-medium">
                            {vehicle.products.length} products on this vehicle
                          </span>
                        </div>

                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-xs">
                            <thead>
                              <tr className="text-gray-500 border-b border-gray-200/60 font-medium">
                                <th className="pb-1.5 pl-1 font-semibold">Product</th>
                                <th className="pb-1.5 font-semibold">Order Number</th>
                                <th className="pb-1.5 font-semibold">Category</th>
                                <th className="pb-1.5 pr-1 text-right font-semibold">Quantity</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {vehicle.products.map((item, idx) => (
                                <tr
                                  key={idx}
                                  className="hover:bg-white/80 transition-colors"
                                >
                                  <td className="py-1.5 pl-1 font-medium text-gray-900 flex items-center gap-1.5">
                                    <Package size={12} className="text-gray-400" />
                                    <span>{item.name}</span>
                                  </td>
                                  <td className="py-1.5 font-semibold text-[#059669]">
                                    <span className="bg-[#EBF7F1] px-1.5 py-0.5 rounded text-[11px] border border-[#D5EFE3]">
                                      {item.orderNo}
                                    </span>
                                  </td>
                                  <td className="py-1.5 text-gray-600 text-[11px]">
                                    {item.category}
                                  </td>
                                  <td className="py-1.5 pr-1 text-right font-semibold text-gray-800 text-[11px]">
                                    {item.quantity}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

          {/* Tab 2: Deferred Allocations */}
          {ordersTab === 'deferred' && (
            <div className="rounded-2xl border border-amber-200 bg-amber-50/40 p-5 shadow-xs transition-all">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="flex gap-3.5">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-700 shadow-xs">
                    <AlertCircle className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex items-center flex-wrap gap-2">
                      <h3 className="text-sm font-bold text-slate-900">
                        Pelwatte Pasteurized Fresh Milk 1L
                      </h3>
                      <span className="font-mono text-xs text-slate-500 font-semibold bg-white/80 px-1.5 py-0.5 rounded border border-amber-200/60">
                        ORD-30302
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-600">
                      <span className="font-semibold text-amber-900">8 crates deferred</span> due to vehicle reefer volume cap on Trip 1.
                    </p>
                    <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
                      <span className="font-medium text-slate-700">Rescheduled Run:</span>
                      <span className="font-mono font-semibold text-slate-900 bg-amber-100/70 px-2 py-0.5 rounded text-[11px]">
                        Trip 2 (11:30 AM Today)
                      </span>
                    </div>
                  </div>
                </div>

                <div className="sm:text-right flex sm:flex-col items-start sm:items-end justify-between">
                  <span className="inline-flex items-center rounded-md bg-emerald-100 px-2.5 py-1 text-xs font-bold text-emerald-800 border border-emerald-200/60">
                    Priority Rollover
                  </span>
                  <p className="mt-1 text-[11px] text-slate-500 font-medium">
                    Guaranteed next-slot delivery
                  </p>
                </div>
              </div>
            </div>
          )}
        </section>
      </>
    )}

    {/* Receipts & Deferrals Tab Content */}
    {activeTab === 'Receipts & Deferrals' && (
      <section aria-label="Receipts & Deferrals" className="w-full flex flex-col gap-4">
        <h2 className="text-xl font-bold text-[#0B2019] tracking-tight">
          Receipts & Deferrals
        </h2>

        {/* Main Card Container */}
        <div className="w-full bg-white border border-gray-200/80 rounded-2xl p-6 shadow-xs">
          <h3 className="text-sm font-bold text-[#0B2019] mb-4">
            Order History
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-[#F8FAFC] text-slate-500 text-xs font-semibold">
                  <th className="py-3 px-4 rounded-l-lg">Date</th>
                  <th className="py-3 px-4">Order</th>
                  <th className="py-3 px-4">Product</th>
                  <th className="py-3 px-4">Quantity</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Outcome</th>
                  <th className="py-3 px-4 text-right rounded-r-lg">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {orderHistory.map((item) => {
                  const isExpanded = !!expandedHistoryRows[item.orderNo];

                  return (
                    <React.Fragment key={item.orderNo}>
                      <tr
                        onClick={() => toggleHistoryRow(item.orderNo)}
                        className={`hover:bg-slate-50/80 transition-colors cursor-pointer ${
                          item.highlight ? 'bg-[#F2FAF5]' : ''
                        }`}
                      >
                        <td className="py-3.5 px-4 text-slate-700 font-medium">
                          {item.date}
                        </td>
                        <td className="py-3.5 px-4 font-bold text-slate-900">
                          {item.orderNo}
                        </td>
                        <td className="py-3.5 px-4 font-medium text-slate-800">
                          {item.product}
                        </td>
                        <td className="py-3.5 px-4 text-slate-600 font-mono text-xs">
                          {item.quantity}
                        </td>
                        <td className="py-3.5 px-4 text-slate-500 font-normal">
                          {item.type}
                        </td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                              item.outcome === 'Deferred'
                                ? 'bg-rose-50 text-rose-600 border border-rose-100'
                                : 'bg-emerald-50 text-emerald-600 border border-emerald-100'
                            }`}
                          >
                            {item.outcome}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-right text-slate-400">
                          <span className="p-1 rounded-md hover:bg-gray-100 transition-colors inline-block">
                            {isExpanded ? (
                              <ChevronUp size={16} strokeWidth={2} />
                            ) : (
                              <ChevronDown size={16} strokeWidth={2} />
                            )}
                          </span>
                        </td>
                      </tr>

                      {/* Dropdown Content */}
                      {isExpanded && (
                        <tr className="bg-slate-50/50">
                          <td colSpan={7} className="px-4 py-3">
                            {item.outcome === 'Deferred' ? (
                              <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-rose-50/70 border border-rose-200/70 text-xs">
                                <AlertCircle size={16} className="text-rose-600 flex-shrink-0 mt-0.5" />
                                <div>
                                  <p className="font-bold text-rose-950">Deferral Reason</p>
                                  <p className="text-rose-800 mt-0.5 leading-relaxed">{item.deferralReason}</p>
                                </div>
                              </div>
                            ) : (
                              <div className="flex flex-wrap items-center gap-6 p-3.5 rounded-xl bg-emerald-50/50 border border-emerald-200/70 text-xs">
                                <div className="flex items-center gap-2">
                                  <Truck size={15} className="text-[#059669]" />
                                  <span className="text-slate-500 font-medium">Delivery Truck:</span>
                                  <span className="font-mono font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-emerald-200/60">
                                    {item.deliveryTruck}
                                  </span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <Clock size={15} className="text-[#059669]" />
                                  <span className="text-slate-500 font-medium">Delivered Time:</span>
                                  <span className="font-mono font-semibold text-slate-900">
                                    {item.deliveryTime}
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
      </section>
    )}

    {/* Place Order Screen */}
    {activeTab === 'Place order' && (
      <section aria-label="Place New Order" className="w-full flex flex-col gap-4">
        {/* Header Row: Title on Left, Compact Amber Cutoff Sign on Right */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="text-2xl font-bold text-[#0B2019] tracking-tight">
            New order — Thu, Oct 1
          </h2>

          {/* Compact Amber Sign Badge on Top Right in Same Row */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#FEF7E6] border border-[#FDE5B5] shadow-2xs">
            <span className="w-5 h-5 rounded-full bg-[#D97706] text-white flex items-center justify-center flex-shrink-0">
              <AlertTriangle size={12} strokeWidth={2.4} />
            </span>
            <span className="text-xs font-bold text-slate-800">
              Order closes at 4:00 PM
            </span>
            <span className="text-xs font-semibold text-[#B45309]">
              · 6h 46m remaining
            </span>
          </div>
        </div>

        {/* Main 2-Column Content: Fits directly within viewport without outer page scroll */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
          {/* Left Column: Unified Order Items Table with Internal Scrolling */}
          <div className="lg:col-span-2 bg-white border border-gray-200/80 rounded-2xl p-5 shadow-xs flex flex-col h-[525px] max-h-[calc(100vh-165px)]">
            {/* Box Header: Title on Left, Search Bar at Top Right (No sort toggle button) */}
            <div className="flex items-center justify-between gap-4 pb-3 border-b border-gray-100 flex-shrink-0">
              <div className="flex items-center gap-2.5">
                <h3 className="font-bold text-slate-900 text-base">
                  Order items
                </h3>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200/60">
                  {filteredCatalog.length} {filteredCatalog.length === 1 ? 'item' : 'items'}
                </span>
              </div>

              {/* Search Bar at Top Right */}
              <div className="relative w-56 sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  type="text"
                  value={catalogSearch}
                  onChange={(e) => setCatalogSearch(e.target.value)}
                  placeholder="Search by ID or name..."
                  className="w-full h-8.5 pl-9 pr-8 text-xs font-medium text-slate-900 bg-white border border-gray-200 rounded-lg placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#059669] focus:border-transparent transition-all shadow-2xs"
                />
                {catalogSearch && (
                  <button
                    type="button"
                    onClick={() => setCatalogSearch('')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5 cursor-pointer"
                    title="Clear search"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>
            </div>

            {/* Scrollable Products Table Container */}
            <div className="flex-1 overflow-y-auto min-h-0 divide-y divide-gray-100 pr-1">
              <table className="w-full text-left text-sm relative">
                <thead className="sticky top-0 z-10 bg-white">
                  <tr className="bg-[#F8FAFC] text-slate-500 text-xs font-semibold select-none shadow-2xs">
                    <th
                      onClick={() => handleSortToggle('id')}
                      className="py-2.5 px-4 rounded-l-lg cursor-pointer hover:text-slate-800 transition-colors"
                      title="Sort by Product ID"
                    >
                      <div className="flex items-center gap-1.5">
                        <span>Product ID</span>
                        {catalogSortField === 'id' ? (
                          catalogSortDirection === 'asc' ? <ArrowUp size={13} className="text-[#059669]" /> : <ArrowDown size={13} className="text-[#059669]" />
                        ) : (
                          <ArrowUpDown size={13} className="text-slate-400 opacity-60" />
                        )}
                      </div>
                    </th>
                    <th
                      onClick={() => handleSortToggle('name')}
                      className="py-2.5 px-4 cursor-pointer hover:text-slate-800 transition-colors"
                      title="Sort alphabetically by Name"
                    >
                      <div className="flex items-center gap-1.5">
                        <span>Item</span>
                        {catalogSortField === 'name' ? (
                          catalogSortDirection === 'asc' ? <ArrowUp size={13} className="text-[#059669]" /> : <ArrowDown size={13} className="text-[#059669]" />
                        ) : (
                          <ArrowUpDown size={13} className="text-slate-400 opacity-60" />
                        )}
                      </div>
                    </th>
                    <th className="py-2.5 px-4">Format</th>
                    <th className="py-2.5 px-4 text-right rounded-r-lg">Quantity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {sortedCatalog.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="py-12 text-center text-slate-500 text-sm">
                        No products found matching <span className="font-semibold text-slate-800">"{catalogSearch}"</span>.
                        <button
                          type="button"
                          onClick={() => setCatalogSearch('')}
                          className="ml-2 text-[#059669] hover:underline font-semibold cursor-pointer"
                        >
                          Clear search
                        </button>
                      </td>
                    </tr>
                  ) : (
                    sortedCatalog.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-2.5 px-4">
                          <span className="font-mono text-xs font-semibold text-slate-700 bg-slate-100/90 px-2 py-0.5 rounded border border-slate-200/70">
                            {item.id}
                          </span>
                        </td>
                        <td className="py-2.5 px-4">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-slate-800">{item.name}</span>
                            {item.category === 'Chilled' && (
                              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-sky-50 text-sky-700 border border-sky-200">
                                <Snowflake size={10} className="text-sky-500" />
                                {item.subType || 'Chilled'}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-2.5 px-4 text-slate-500">{item.format}</td>
                        <td className="py-2.5 px-4 text-right">
                          <input
                            type="number"
                            min="0"
                            value={orderQuantities[item.id] ?? 0}
                            onChange={(e) => handleQtyChange(item.id, e.target.value)}
                            className="w-16 h-8 text-center font-bold text-slate-900 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#059669] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                          />
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right Column: Order Summary Sidebar */}
          <div className="lg:col-span-1 bg-white border border-gray-200/80 rounded-2xl p-5 shadow-xs flex flex-col gap-4">
            <h3 className="font-bold text-slate-900 text-base">
              Order summary
            </h3>

            {/* Metrics List */}
            <div className="divide-y divide-gray-100 text-sm">
              <div className="flex items-center justify-between py-2">
                <span className="text-slate-500 font-normal">Line items</span>
                <span className="font-bold text-slate-900 font-mono">
                  {activeLineItems.length}
                </span>
              </div>

              <div className="flex items-center justify-between py-2">
                <span className="text-slate-500 font-normal">Total units</span>
                <span className="font-bold text-slate-900 font-mono">
                  {totalOrderedUnits} cases
                </span>
              </div>

              <div className="flex items-center justify-between py-2">
                <span className="text-slate-500 font-normal">Est. volume</span>
                <span className="font-bold text-slate-900 font-mono">
                  {estTotalVolumeM3} m³
                </span>
              </div>

              <div className="flex items-center justify-between py-2">
                <span className="text-slate-500 font-normal">Est. weight</span>
                <span className="font-bold text-slate-900 font-mono">
                  ~{estTotalWeightKg} kg
                </span>
              </div>

              <div className="flex items-center justify-between py-2">
                <span className="text-slate-500 font-normal">Expected arrival</span>
                <span className="font-bold text-slate-900">
                  7:40 AM, Thu
                </span>
              </div>
            </div>

            {/* Climate Separation Callout Box */}
            <div className="bg-[#F0FDF4] border border-[#DCFCE7] rounded-xl p-3.5">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-[#059669] text-white flex items-center justify-center text-xs font-bold shadow-2xs">
                  {dispatchesCount || 1}
                </span>
                <p className="font-bold text-slate-900 text-xs">
                  {dispatchesCount === 1 ? '1 order will be placed' : `${dispatchesCount} orders will be placed`}
                </p>
              </div>
              <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                {dispatchesCount > 1
                  ? 'Dry and chilled categories are dispatched as separate orders to preserve climate integrity.'
                  : 'All selected items will be dispatched in a single temperature-controlled run.'}
              </p>
              {dispatchesCount > 1 && (
                <div className="mt-2 pt-1.5 border-t border-emerald-200/50 flex items-center justify-between text-[11px] text-slate-600 font-medium">
                  <span>Dry: {dryItemsOrdered.length} items</span>
                  <span>Chilled: {chilledItemsOrdered.length} items</span>
                </div>
              )}
            </div>

            {/* Primary Action Button */}
            <button
              type="button"
              onClick={() => setOrderConfirmed(true)}
              className="w-full bg-[#059669] hover:bg-[#047857] active:bg-[#065f46] text-white font-medium py-2.5 rounded-xl transition-all shadow-xs text-sm cursor-pointer flex items-center justify-center focus:outline-none focus-visible:ring-2 focus-visible:ring-[#059669]"
            >
              {orderConfirmed ? 'Order Placed!' : 'Review & confirm'}
            </button>
          </div>
        </div>
      </section>
    )}
  </main>
</div>
);
}
