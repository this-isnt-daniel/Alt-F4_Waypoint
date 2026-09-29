import React from 'react';
import { User, ShieldCheck, ArrowRight, GitBranch, Smartphone, Layers, CheckCircle2 } from 'lucide-react';

export default function DriverFlow({ onSelectScreen }) {
  const steps = [
    { id: '01-login', num: '01', title: 'Login & Shift Start', desc: 'Identifies driver, confirms offline pack (47 stops), displays safety advisory' },
    { id: '02-runs', num: '02', title: "Today's Runs", desc: 'Trip 1 (Gampaha Fresh) active, Trip 2 (Colombo Style) locked' },
    { id: '03-checklist', num: '03', title: 'Pre-departure Check', desc: 'Surfaces loader shortfall (8 missing yogurt) + vehicle & reefer (4°C)' },
    { id: '04-route', num: '04', title: 'Route Overview', desc: 'Timeline rail with dock icons, delivery windows, and next-stop elevated card' },
    { id: '05-stop', num: '05', title: 'Stop Detail', desc: '07:30 countdown timer, item table, and sequential arrival action' },
    { id: '06-pod', num: '06', title: 'Proof of Delivery', desc: 'Full/Partial/Rejected selector, sign pad, photo evidence & GPS tag' },
    { id: '10-summary', num: '10', title: 'End of Trip Summary', desc: 'Trip performance (3h 42m under budget, 9.4 km/L) and return to depot CTA' },
  ];

  const branches = [
    {
      trigger: 'From Screen 05 (Stop Detail)',
      targetId: '07-problem',
      title: 'Screen 07: Report a Problem',
      desc: 'Branch taken when physical hindrance or route blocker occurs (e.g. Kandy corridor monsoon flood at OUT027). Alerts dispatcher immediately.',
      badgeColor: '#E5484D',
      badgeBg: '#FDECEC',
    },
    {
      trigger: 'Any Screen → Network Loss',
      targetId: '08-offline',
      title: 'Screen 08: Offline / Degradation Mode',
      desc: 'Activated when crossing dead zones (Kegalle). Queues PODs locally with 3 recovery states (Saved → Syncing → Synced) and conflict alert.',
      badgeColor: '#334155',
      badgeBg: '#F1F5F9',
    },
    {
      trigger: 'From Offline or Push Notification',
      targetId: '09-route-change',
      title: 'Screen 09: Route Change Alert',
      desc: 'Dispatcher resequences trip (SPAR OUT031 prioritized ahead of OUT027 due to 07:00 mall cutoff). Driver acknowledges new timeline.',
      badgeColor: '#F59E0B',
      badgeBg: '#FFF4DB',
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-6 py-8" style={{ background: '#F4F8F6', minHeight: 'calc(100vh - 64px)' }}>
      {/* Title */}
      <div className="mb-8">
        <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider" style={{ background: '#E8F5EF', color: '#0F9D6C', border: '1px solid #C6E8D9' }}>
          Architecture &amp; User Journey
        </span>
        <h1 className="text-3xl font-bold mt-2" style={{ color: '#0B3D33' }}>
          Driver Portal End-to-End Flow &amp; Persona
        </h1>
        <p className="text-sm mt-1" style={{ color: '#5B6B66' }}>
          Interactive state machine connecting all 10 core screens, branch triggers, persona documentation, and AI disclosure.
        </p>
      </div>

      {/* Persona & AI Disclosure (2 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Persona */}
        <div className="rounded-[20px] p-6 bg-white border border-[#E2ECE7] shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-[#E8F5EF] text-[#0F9D6C] flex items-center justify-center font-bold">
              <User size={20} />
            </div>
            <div>
              <h2 className="text-base font-bold" style={{ color: '#0B3D33' }}>Target Persona: Kasun Perera (34)</h2>
              <p className="text-xs" style={{ color: '#5B6B66' }}>Delivery Driver · Peliyagoda Depot · Android Device</p>
            </div>
          </div>
          <p className="text-xs leading-relaxed" style={{ color: '#0E1A17' }}>
            Works 05:30–14:00 across hill country and urban routes with unreliable connectivity. Currently uses paper run sheets. Needs: glanceable info, large tap targets, offline-first reliability, one-handed use while stopped.
          </p>
        </div>

        {/* AI Disclosure */}
        <div className="rounded-[20px] p-6 bg-white border border-[#E2ECE7] shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-[#E8F5EF] text-[#0F9D6C] flex items-center justify-center font-bold">
              <ShieldCheck size={20} />
            </div>
            <div>
              <h2 className="text-base font-bold" style={{ color: '#0B3D33' }}>AI Disclosure &amp; Design Attribution</h2>
              <p className="text-xs" style={{ color: '#5B6B66' }}>Waypoint Group Design Systems</p>
            </div>
          </div>
          <p className="text-xs leading-relaxed" style={{ color: '#0E1A17' }}>
            Design layouts and component structure generated with Figma AI assistant. All content, data architecture, UX rationale, interaction flows, and design decisions are original work by the team.
          </p>
        </div>
      </div>

      {/* Primary Linear Flow */}
      <div className="rounded-[20px] p-6 bg-white border border-[#E2ECE7] shadow-sm mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Layers size={18} className="text-[#0F9D6C]" />
          <h2 className="text-sm font-bold tracking-wide uppercase" style={{ color: '#0B3D33' }}>
            Primary Delivery Flow (Linear Happy Path)
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {steps.map((st, i) => (
            <div
              key={st.id}
              onClick={() => onSelectScreen(st.id)}
              className="p-4 rounded-xl border border-[#E2ECE7] bg-[#FAFCFB] hover:border-[#0F9D6C] transition-all cursor-pointer relative group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="w-6 h-6 rounded-full bg-[#0F9D6C] text-white text-[11px] font-bold flex items-center justify-center font-mono">
                  {st.num}
                </span>
                <span className="text-[11px] text-[#0F9D6C] font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  Jump to Screen →
                </span>
              </div>
              <h3 className="text-xs font-bold" style={{ color: '#0E1A17' }}>{st.title}</h3>
              <p className="text-[11px] mt-1 line-clamp-2" style={{ color: '#5B6B66' }}>{st.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Exception & Resilience Branches */}
      <div className="rounded-[20px] p-6 bg-white border border-[#E2ECE7] shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <GitBranch size={18} className="text-[#F59E0B]" />
          <h2 className="text-sm font-bold tracking-wide uppercase" style={{ color: '#0B3D33' }}>
            Exception Handling &amp; Network Degradation Branches
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {branches.map((b) => (
            <div
              key={b.targetId}
              onClick={() => onSelectScreen(b.targetId)}
              className="p-4 rounded-xl border border-[#E2ECE7] bg-[#FAFCFB] hover:border-[#0F9D6C] transition-all cursor-pointer relative group"
            >
              <span
                className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider inline-block mb-2"
                style={{ background: b.badgeBg, color: b.badgeColor }}
              >
                {b.trigger}
              </span>
              <h3 className="text-xs font-bold" style={{ color: '#0E1A17' }}>{b.title}</h3>
              <p className="text-[11px] mt-1 leading-relaxed" style={{ color: '#5B6B66' }}>{b.desc}</p>
              <div className="mt-3 pt-2 border-t border-[#E2ECE7] flex justify-end">
                <span className="text-[11px] text-[#0F9D6C] font-semibold group-hover:underline">
                  Launch Branch →
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
