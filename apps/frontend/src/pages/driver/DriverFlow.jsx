import React from 'react';
import { User, ShieldCheck, ArrowRight, GitBranch, Smartphone, Layers, CheckCircle2 } from 'lucide-react';

export default function DriverFlow({ onSelectScreen, darkMode = false }) {
  const steps = [
    { id: '01-login', title: 'Shift Overview & Start', desc: 'Identifies driver, confirms offline pack (47 stops), displays safety advisory' },
    { id: '02-runs', title: "Today's Runs", desc: 'Trip 1 (Gampaha Fresh) active, Trip 2 (Colombo Style) locked' },
    { id: '03-checklist', title: 'Pre-departure Check', desc: 'Surfaces loader shortfall (8 missing yogurt) + vehicle & reefer (4°C)' },
    { id: '04-route', title: 'Route Overview', desc: 'Timeline rail with dock icons, delivery windows, and next-stop elevated card' },
    { id: '05-stop', title: 'Stop Detail', desc: '07:30 countdown timer, item table, and sequential arrival action' },
    { id: '06-pod', title: 'Proof of Delivery', desc: 'Full/Partial/Rejected selector, photo evidence & GPS tag' },
    { id: '10-summary', title: 'End of Trip Summary', desc: 'Trip performance (3h 42m under budget, 9.4 km/L) and return to depot CTA' },
  ];

  const branches = [
    {
      trigger: 'From Stop Detail',
      targetId: '07-problem',
      title: 'Report a Problem',
      desc: 'Branch taken when physical hindrance or route blocker occurs (e.g. Kandy corridor monsoon flood at OUT027). Alerts dispatcher immediately.',
      badgeColor: darkMode ? '#F87171' : '#E5484D',
      badgeBg: darkMode ? '#331417' : '#FDECEC',
    },
    {
      trigger: 'Any Screen → Network Loss',
      targetId: '08-offline',
      title: 'Offline / Degradation Mode',
      desc: 'Activated when crossing dead zones (Kegalle). Queues PODs locally with 3 recovery states (Saved → Syncing → Synced) and conflict alert.',
      badgeColor: darkMode ? '#CBD5E1' : '#334155',
      badgeBg: darkMode ? '#1E293B' : '#F1F5F9',
    },
    {
      trigger: 'From Offline or Push Notification',
      targetId: '09-route-change',
      title: 'Route Change Alert',
      desc: 'Dispatcher resequences trip (SPAR OUT031 prioritized ahead of OUT027 due to 07:00 mall cutoff). Driver acknowledges new timeline.',
      badgeColor: darkMode ? '#FCD34D' : '#F59E0B',
      badgeBg: darkMode ? '#2A1E0E' : '#FFF4DB',
    },
  ];

  return (
    <div className={`w-full transition-colors ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
      {/* Title */}
      <div className="mb-8">
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border ${
            darkMode ? 'bg-[#10382E] text-[#34D399] border-[#185344]' : 'bg-[#E8F5EF] text-[#0F9D6C] border-[#C6E8D9]'
          }`}
        >
          Architecture &amp; User Journey
        </span>
        <h1 className={`text-3xl font-bold mt-2 ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
          Driver Portal End-to-End Flow &amp; Persona
        </h1>
        <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
          Interactive state machine connecting all 10 core screens, branch triggers, persona documentation, and AI disclosure.
        </p>
      </div>

      {/* Persona & AI Disclosure (2 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Persona */}
        <div className={`rounded-[20px] p-6 border shadow-sm transition-all ${
          darkMode ? 'bg-[#122822] border-[#1F3D35]' : 'bg-white border-[#E2ECE7]'
        }`}>
          <div className="flex items-center gap-3 mb-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
              darkMode ? 'bg-[#10382E] text-[#34D399]' : 'bg-[#E8F5EF] text-[#0F9D6C]'
            }`}>
              <User size={20} />
            </div>
            <div>
              <h2 className={`text-base font-bold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
                Target Persona: Kasun Perera (34)
              </h2>
              <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
                Delivery Driver · Peliyagoda Depot · Android Device
              </p>
            </div>
          </div>
          <p className={`text-xs leading-relaxed ${darkMode ? 'text-gray-200' : 'text-[#0E1A17]'}`}>
            Works 05:30–14:00 across hill country and urban routes with unreliable connectivity. Currently uses paper run sheets. Needs: glanceable info, large tap targets, offline-first reliability, one-handed use while stopped.
          </p>
        </div>

        {/* AI Disclosure */}
        <div className={`rounded-[20px] p-6 border shadow-sm transition-all ${
          darkMode ? 'bg-[#122822] border-[#1F3D35]' : 'bg-white border-[#E2ECE7]'
        }`}>
          <div className="flex items-center gap-3 mb-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
              darkMode ? 'bg-[#10382E] text-[#34D399]' : 'bg-[#E8F5EF] text-[#0F9D6C]'
            }`}>
              <ShieldCheck size={20} />
            </div>
            <div>
              <h2 className={`text-base font-bold ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
                AI Disclosure &amp; Design Attribution
              </h2>
              <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>
                Waypoint Group Design Systems
              </p>
            </div>
          </div>
          <p className={`text-xs leading-relaxed ${darkMode ? 'text-gray-200' : 'text-[#0E1A17]'}`}>
            Design layouts and component structure generated with Figma AI assistant. All content, data architecture, UX rationale, interaction flows, and design decisions are original work by the team.
          </p>
        </div>
      </div>

      {/* Primary Linear Flow */}
      <div className={`rounded-[20px] p-6 border shadow-sm mb-8 transition-all ${
        darkMode ? 'bg-[#122822] border-[#1F3D35]' : 'bg-white border-[#E2ECE7]'
      }`}>
        <div className="flex items-center gap-2 mb-4">
          <Layers size={18} className="text-[#0F9D6C]" />
          <h2 className={`text-sm font-bold tracking-wide uppercase ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
            Primary Delivery Flow (Linear Happy Path)
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {steps.map((st) => (
            <div
              key={st.id}
              onClick={() => onSelectScreen(st.id)}
              className={`p-4 rounded-xl border transition-all cursor-pointer relative group ${
                darkMode 
                  ? 'border-[#1F3D35] bg-[#16332B] hover:border-[#0F9D6C]' 
                  : 'border-[#E2ECE7] bg-[#FAFCFB] hover:border-[#0F9D6C]'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#0F9D6C] inline-block" />
                <span className="text-[11px] text-[#0F9D6C] font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  Jump to Screen →
                </span>
              </div>
              <h3 className={`text-xs font-bold ${darkMode ? 'text-white' : 'text-[#0E1A17]'}`}>{st.title}</h3>
              <p className={`text-[11px] mt-1 line-clamp-2 ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>{st.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Exception & Resilience Branches */}
      <div className={`rounded-[20px] p-6 border shadow-sm transition-all ${
        darkMode ? 'bg-[#122822] border-[#1F3D35]' : 'bg-white border-[#E2ECE7]'
      }`}>
        <div className="flex items-center gap-2 mb-4">
          <GitBranch size={18} className="text-[#F59E0B]" />
          <h2 className={`text-sm font-bold tracking-wide uppercase ${darkMode ? 'text-white' : 'text-[#0B3D33]'}`}>
            Exception Handling &amp; Network Degradation Branches
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {branches.map((b) => (
            <div
              key={b.targetId}
              onClick={() => onSelectScreen(b.targetId)}
              className={`p-4 rounded-xl border transition-all cursor-pointer relative group ${
                darkMode 
                  ? 'border-[#1F3D35] bg-[#16332B] hover:border-[#0F9D6C]' 
                  : 'border-[#E2ECE7] bg-[#FAFCFB] hover:border-[#0F9D6C]'
              }`}
            >
              <span
                className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider inline-block mb-2"
                style={{ background: b.badgeBg, color: b.badgeColor }}
              >
                {b.trigger}
              </span>
              <h3 className={`text-xs font-bold ${darkMode ? 'text-white' : 'text-[#0E1A17]'}`}>{b.title}</h3>
              <p className={`text-[11px] mt-1 leading-relaxed ${darkMode ? 'text-gray-400' : 'text-[#5B6B66]'}`}>{b.desc}</p>
              <div className={`mt-3 pt-2 border-t flex justify-end ${darkMode ? 'border-[#1F3D35]' : 'border-[#E2ECE7]'}`}>
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
