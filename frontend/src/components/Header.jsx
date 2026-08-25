import React from 'react';
import { Shield, FileText, Map, Clock, Satellite, CheckCircle, Scale, Cpu, Info } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, selectedRole, setSelectedRole, showStatusModal, setShowStatusModal }) {
  const tabs = [
    { id: 'map', label: 'GIS Risk Map', icon: Map },
    { id: 'ocr', label: 'Registry OCR (E1)', icon: FileText },
    { id: 'ownership', label: 'Ownership Graph (E3)', icon: Clock },
    { id: 'satellite', label: 'Satellite Cross-Check (E4)', icon: Satellite },
    { id: 'review', label: 'Officer Queue & Audit', icon: CheckCircle, badge: 'P0' },
    { id: 'revenue', label: 'Revenue Court Status', icon: Scale },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-4 py-3 shadow-2xl">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        {/* Brand & Positioning */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center shadow-lg shadow-amber-500/20">
            <Shield className="w-6 h-6 text-slate-950 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold bg-gradient-to-r from-amber-400 via-amber-200 to-white bg-clip-text text-transparent">
                BhuNetra AI
              </h1>
              <span className="text-[10px] font-semibold tracking-wide uppercase px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                SIH 2026 • SIH26018
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              DILRMP Digitizes • <span className="text-amber-300">BhuNetra Verifies & Decides</span>
            </p>
          </div>
        </div>

        {/* Action Controls & Role Switcher */}
        <div className="flex items-center gap-3">
          {/* Status Modal Trigger */}
          <button
            onClick={() => setShowStatusModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition"
          >
            <Info className="w-4 h-4 text-amber-400" />
            <span>Engine Status Tiers</span>
          </button>

          {/* Role selector */}
          <div className="flex items-center bg-slate-900/90 rounded-lg p-1 border border-slate-800">
            <span className="text-[11px] text-slate-400 px-2 font-medium">Role:</span>
            {['Citizen', 'Revenue Officer', 'District Collector'].map((role) => (
              <button
                key={role}
                onClick={() => setSelectedRole(role)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                  selectedRole === role
                    ? 'bg-amber-500 text-slate-950 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {role}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Primary Tab Navigation */}
      <div className="max-w-7xl mx-auto mt-3 pt-2 border-t border-slate-800/60 flex items-center gap-1 overflow-x-auto no-scrollbar">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
                isActive
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-md shadow-amber-500/5'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-amber-400' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300">
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </header>
  );
}
