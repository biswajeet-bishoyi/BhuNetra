import React from 'react';
import { Shield, FileText, Map, Clock, Satellite, CheckCircle, Scale, BarChart3, Bell, LogIn, LogOut, Lock } from 'lucide-react';

export default function Header({
  activeTab,
  setActiveTab,
  selectedRole,
  setSelectedRole,
  showStatusModal,
  setShowStatusModal,
  onOpenAlertModal,
  currentUser,
  onOpenLoginModal,
  onLogout
}) {
  // Clean, concise tab definitions strictly configured per role
  const allTabs = [
    { id: 'analytics', label: 'Executive Analytics', icon: BarChart3, badge: 'Executive', roles: ['District Collector'] },
    { id: 'map', label: 'GIS Map', icon: Map, roles: ['Citizen', 'Revenue Officer', 'District Collector'] },
    { id: 'ocr', label: 'Registry OCR', icon: FileText, roles: ['Citizen', 'Revenue Officer', 'District Collector'] },
    { id: 'ownership', label: 'Ownership Graph', icon: Clock, roles: ['Citizen', 'Revenue Officer', 'District Collector'] },
    { id: 'satellite', label: 'Satellite Cross-Check', icon: Satellite, roles: ['Citizen', 'Revenue Officer', 'District Collector'] },
    { id: 'review', label: 'Officer Queue', icon: CheckCircle, badge: 'P0', roles: ['Revenue Officer', 'District Collector'] },
    { id: 'revenue', label: 'Revenue Court', icon: Scale, roles: ['Revenue Officer', 'District Collector'] },
  ];

  // Filter tabs tailored strictly for active role
  const visibleTabs = allTabs.filter(tab => tab.roles.includes(selectedRole || 'Citizen'));

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-4 py-2.5 shadow-2xl">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3">
        
        {/* Brand & Positioning */}
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center shadow-lg shadow-amber-500/20 shrink-0">
            <Shield className="w-5 h-5 text-slate-950 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold bg-gradient-to-r from-amber-400 via-amber-200 to-white bg-clip-text text-transparent">
                BhuNetra AI
              </h1>
              <span className="text-[9px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                SIH 2026
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium leading-none mt-0.5">
              DILRMP Digitizes • <span className="text-amber-300 font-semibold">BhuNetra Verifies & Decides</span>
            </p>
          </div>
        </div>

        {/* Action Controls & Authentication */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Status Modal Trigger */}
          <button
            onClick={() => setShowStatusModal(true)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition cursor-pointer"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
            <span>Engine Status</span>
          </button>

          {/* User Profile & Auth State */}
          {currentUser ? (
            <div className="flex items-center gap-2 pl-1.5 border-l border-slate-800">
              <div className="flex items-center gap-2 bg-slate-900/90 py-1 px-2.5 rounded-xl border border-slate-800 text-xs shadow-md">
                <div className={`w-5 h-5 rounded-full font-bold flex items-center justify-center text-[9px] ${
                  currentUser.role === 'District Collector'
                    ? 'bg-purple-500 text-white'
                    : currentUser.role === 'Revenue Officer'
                    ? 'bg-amber-500 text-slate-950'
                    : 'bg-emerald-500 text-slate-950'
                }`}>
                  {currentUser.name ? currentUser.name.charAt(0) : 'U'}
                </div>
                <div className="text-left">
                  <div className="text-[11px] font-bold text-slate-200 truncate max-w-[120px] leading-tight">
                    {currentUser.name}
                  </div>
                  <div className={`text-[8px] uppercase font-black tracking-wider ${
                    currentUser.role === 'District Collector'
                      ? 'text-purple-400'
                      : currentUser.role === 'Revenue Officer'
                      ? 'text-amber-400'
                      : 'text-emerald-400'
                  }`}>
                    {currentUser.role}
                  </div>
                </div>
              </div>
              <button
                onClick={onLogout}
                title="Sign Out / Switch Account"
                className="flex items-center gap-1 px-2 py-1.5 rounded-xl bg-slate-800/80 hover:bg-rose-500/20 hover:text-rose-300 text-slate-400 border border-slate-700 text-xs font-semibold transition cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline text-[11px]">Sign Out</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              <div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-900/80 border border-slate-800 text-[11px] text-slate-400">
                <Lock className="w-3 h-3 text-amber-400" />
                <span>Citizen</span>
              </div>
              <button
                onClick={onOpenLoginModal}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold shadow-md shadow-amber-500/20 transition cursor-pointer"
              >
                <LogIn className="w-3.5 h-3.5 stroke-[2.5]" />
                <span>Portal Sign In</span>
              </button>
            </div>
          )}

        </div>
      </div>

      {/* Sleek, Clean Tab Navigation (No Ugly Scrollbar, Refined Pill Spacing) */}
      <div className="max-w-7xl mx-auto mt-2.5 pt-2 border-t border-slate-800/60 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
        {visibleTabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap cursor-pointer ${
                isActive
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-sm font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-amber-400' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span className={`text-[8px] font-black px-1 py-0.2 rounded uppercase ${
                  tab.badge === 'Executive'
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                    : 'bg-amber-500/20 text-amber-300'
                }`}>
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
