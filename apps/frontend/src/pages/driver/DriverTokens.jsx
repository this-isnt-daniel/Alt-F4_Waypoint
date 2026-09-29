import React from 'react';

const tokens = {
  colors: [
    { name: 'Primary (Emerald)', hex: '#0F9D6C', text: '#FFFFFF', desc: 'Main brand, CTAs, success tags, active borders' },
    { name: 'Primary Pressed', hex: '#0B7F57', text: '#FFFFFF', desc: 'Active/pressed state for primary buttons' },
    { name: 'Primary Deep (Forest)', hex: '#0B3D33', text: '#FFFFFF', desc: 'Hero headers, countdown cards, prominent text' },
    { name: 'Accent Teal', hex: '#14B8A6', text: '#FFFFFF', desc: 'Secondary highlight, chilled category accents' },
    { name: 'Background (Mint-White)', hex: '#F4F8F6', text: '#0E1A17', desc: 'Base surface across all driver application screens' },
    { name: 'Surface', hex: '#FFFFFF', text: '#0E1A17', desc: 'Cards, elevated modals, sheets' },
    { name: 'Surface-Tint', hex: '#E8F5EF', text: '#0F9D6C', desc: 'Badge fills, selected rows, highlight panels' },
    { name: 'Text Primary', hex: '#0E1A17', text: '#FFFFFF', desc: 'High contrast readable primary body and title text' },
    { name: 'Text Secondary', hex: '#5B6B66', text: '#FFFFFF', desc: 'Labels, captions, timestamps, table metadata' },
    { name: 'Warning Amber', hex: '#F59E0B', text: '#000000', desc: 'Background: #FFF4DB. Non-blocking alerts, van warnings' },
    { name: 'Critical Red', hex: '#E5484D', text: '#FFFFFF', desc: 'Background: #FDECEC. Exclusion reports, strict window alerts' },
    { name: 'Info Blue', hex: '#3B82F6', text: '#FFFFFF', desc: 'Background: #E8F0FF. Active sync state, photo evidence' },
    { name: 'Success Green', hex: '#16A34A', text: '#FFFFFF', desc: 'Background: #E6F6EC. Loaded items, synced queue' },
    { name: 'Offline Slate Strip', hex: '#334155', text: '#FFFFFF', desc: 'Paired with red (#E5484D) border for unmistakable offline mode' },
  ],
  typography: [
    { level: 'Display', spec: '32px / 40px Bold', sample: '07:30', usage: 'Countdown timer, critical time metrics' },
    { level: 'Title', spec: '22px / 28px Semibold', sample: 'Keells Super — Gampaha', usage: 'Screen title and outlet header' },
    { level: 'Body', spec: '16px / 24px Regular/Medium', sample: 'Use rear dock, report to goods receiving.', usage: 'Instructions, explanations' },
    { level: 'Caption', spec: '13px / 18px Medium', sample: 'Delivery Window: 06:00 – 07:30', usage: 'Card details, timestamps' },
    { level: 'Overline', spec: '12px / 16px Bold Caps', sample: 'ORDER CONTENT DETAILS', usage: 'Section headers, card labels' },
    { level: 'Tabular Numerals', spec: 'Font-Variant Numeric: tabular-nums', sample: '420 u | 310 kg | 2.2 m³', usage: 'Tables, counts, weights, GPS coordinates' },
  ],
  rules: [
    { title: '8pt Grid & Screen Padding', value: '20px margin, 8pt increments for internal card padding.' },
    { title: 'Corner Radii', value: 'Cards: 20px | Buttons: 16px | Pills & Chips: 9999px (full-pill)' },
    { title: 'Elevation & Borders', value: 'Soft depth 0 8 24 rgba(11,61,51,0.08) with 1px #E2ECE7 hairline border.' },
    { title: 'Touch Targets & Accessibility', value: 'Min 56px height for secondary controls, 64px for primary CTAs. WCAG AA compliant pairing icon + text.' },
  ]
};

export default function DriverTokens({ darkMode = false }) {
  return (
    <div className={`w-full transition-colors ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
      {/* Header */}
      <div className="mb-8">
        <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border ${
          darkMode ? 'bg-[#10382E] text-[#34D399] border-[#185344]' : 'bg-[#E8F5EF] text-[#0F9D6C] border-[#C6E8D9]'
        }`}>
          Design Tokens &amp; Style Guide
        </span>
        <h1 className={`text-3xl font-bold mt-2 ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
          Waypoint Driver Design Tokens
        </h1>
        <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
          Complete token specifications: Colors, Typography, Shapes, Grid, Elevation, and Accessibility rules.
        </p>
      </div>

      {/* Colors Section */}
      <div className={`rounded-[20px] p-6 border shadow-sm mb-6 transition-all ${
        darkMode ? 'bg-[#122822] border-[#1F3D35]' : 'bg-white border-[#E2ECE7]'
      }`}>
        <h2 className={`text-base font-bold mb-4 ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>Color Tokens</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {tokens.colors.map((c) => (
            <div key={c.name} className={`rounded-xl border overflow-hidden transition-all ${
              darkMode ? 'border-[#1F3D35] bg-[#16332B]' : 'border-[#E2ECE7] bg-[#FAFCFB]'
            }`}>
              <div className="h-16 flex items-center justify-center font-mono font-bold text-xs" style={{ background: c.hex, color: c.text }}>
                {c.hex}
              </div>
              <div className="p-3">
                <p className={`text-xs font-bold ${darkMode ? 'text-white' : 'text-[#0E1A17]'}`}>{c.name}</p>
                <p className={`text-[11px] mt-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>{c.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Typography & System Rules */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Typography */}
        <div className={`rounded-[20px] p-6 border shadow-sm transition-all ${
          darkMode ? 'bg-[#122822] border-[#1F3D35]' : 'bg-white border-[#E2ECE7]'
        }`}>
          <h2 className={`text-base font-bold mb-4 ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>Typography System (Inter)</h2>
          <div className="flex flex-col gap-4">
            {tokens.typography.map((t) => (
              <div key={t.level} className={`p-3 rounded-xl border transition-all ${
                darkMode ? 'bg-[#16332B] border-[#1F3D35]' : 'bg-[#F4F8F6] border-[#E2ECE7]'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase text-[#0F9D6C]">{t.level}</span>
                  <span className={`text-[11px] font-mono ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>{t.spec}</span>
                </div>
                <p className={`text-sm font-semibold mt-1 ${darkMode ? 'text-white' : 'text-[#0E1A17]'}`}>{t.sample}</p>
                <p className={`text-[11px] mt-0.5 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>{t.usage}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Spatial, Shape & Accessibility Rules */}
        <div className={`rounded-[20px] p-6 border shadow-sm transition-all ${
          darkMode ? 'bg-[#122822] border-[#1F3D35]' : 'bg-white border-[#E2ECE7]'
        }`}>
          <h2 className={`text-base font-bold mb-4 ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>Shape, Spacing &amp; Accessibility</h2>
          <div className="flex flex-col gap-4">
            {tokens.rules.map((r) => (
              <div key={r.title} className={`p-3.5 rounded-xl border transition-all ${
                darkMode ? 'bg-[#16332B] border-[#1F3D35]' : 'bg-[#F4F8F6] border-[#E2ECE7]'
              }`}>
                <p className={`text-xs font-bold uppercase ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>{r.title}</p>
                <p className={`text-xs mt-1 leading-relaxed ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>{r.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
