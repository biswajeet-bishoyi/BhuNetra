import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Shield,
  FileText,
  Map,
  Clock,
  Satellite,
  CheckCircle,
  Scale,
  BarChart3,
  Bell,
  LogIn,
  LogOut,
  Lock,
  Play,
  Search,
  X,
  Globe,
  Pen,
  FolderOpen,
  Layers,
  TrendingUp,
  ChevronDown,
  Sparkles,
  Check,
  Compass,
  FileSpreadsheet
} from 'lucide-react';
import { useLang } from '../i18n';

export default function Header({
  activeTab,
  setActiveTab,
  selectedRole,
  setSelectedRole,
  showStatusModal,
  setShowStatusModal,
  onOpenAlertModal,
  onStartDemo,
  onSelectParcel,
  currentUser,
  onOpenLoginModal,
  onLogout,
  onOpenOdishaModal
}) {
  const { lang, setLang, t, supportedLanguages } = useLang();

  // Active role determination: unauthenticated defaults to public Citizen view
  const activeRole = currentUser ? currentUser.role : (selectedRole || 'Citizen');
  const isOfficerOrCollector = activeRole === 'Revenue Officer' || activeRole === 'District Collector';

  // Navigation & Language Dropdown State
  const [openNavDropdown, setOpenNavDropdown] = useState(null); // 'verification' | 'operations' | null
  const [showLangDropdown, setShowLangDropdown] = useState(false);
  const navDropdownRef = useRef(null);
  const langDropdownRef = useRef(null);

  // Close dropdown on outside click or escape key
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (navDropdownRef.current && !navDropdownRef.current.contains(e.target)) {
        setOpenNavDropdown(null);
      }
      if (langDropdownRef.current && !langDropdownRef.current.contains(e.target)) {
        setShowLangDropdown(false);
      }
    };
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setOpenNavDropdown(null);
        setShowLangDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  // Primary Direct Tabs
  const primaryTabs = [
    ...(activeRole === 'District Collector'
      ? [{ id: 'analytics', label: t('tab.analytics') || 'Executive Analytics', icon: BarChart3, badge: 'Executive' }]
      : []),
    { id: 'map', label: t('tab.map') || 'GIS Map', icon: Map },
    { id: 'ocr', label: t('tab.ocr') || 'Registry OCR', icon: FileText },
    ...(isOfficerOrCollector
      ? [{ id: 'review', label: t('tab.review') || 'Officer Queue', icon: CheckCircle, badge: 'P0' }]
      : []),
    // For Citizens, directly expose Ownership and Satellite cross-check
    ...(!isOfficerOrCollector
      ? [
          { id: 'ownership', label: t('tab.ownership') || 'Ownership Graph', icon: Clock },
          { id: 'satellite', label: t('tab.satellite') || 'Satellite Cross-Check', icon: Satellite }
        ]
      : [])
  ];

  // Group 1: Verification & Spatial Intelligence (for Officers/Collectors)
  const verificationTabs = [
    {
      id: 'ownership',
      label: t('tab.ownership') || 'Ownership Graph',
      description: 'Title chain, genealogical lineage & sale deeds',
      icon: Clock
    },
    {
      id: 'satellite',
      label: t('tab.satellite') || 'Satellite Cross-Check',
      description: 'Sentinel-2 NDVI, boundary shifts & vegetation index',
      icon: Satellite
    },
    {
      id: 'timeline',
      label: t('tab.timeline') || 'Risk Timeline',
      description: 'Temporal risk trajectory & anomaly progression',
      icon: TrendingUp
    }
  ];

  // Group 2: Revenue Operations & Records (for Officers/Collectors)
  const operationsTabs = [
    {
      id: 'revenue',
      label: t('tab.revenue') || 'Revenue Court',
      description: 'Pending litigations, stay orders & injunctions',
      icon: Scale
    },
    {
      id: 'mutations',
      label: t('tab.mutations') || 'Mutations Registry',
      description: 'Title transfer requests & Tahsildar approval workflow',
      icon: Pen
    },
    {
      id: 'documents',
      label: t('tab.documents') || 'Document Vault',
      description: 'Extracted deeds, encumbrance certs & pattas',
      icon: FolderOpen
    },
    {
      id: 'batch',
      label: t('tab.batch') || 'Batch Processing',
      description: 'Bulk deed ingestion & automated anomaly screening',
      icon: Layers
    }
  ];

  // Determine if activeTab belongs to one of the dropdown groups
  const activeVerificationTab = verificationTabs.find((t) => t.id === activeTab);
  const activeOperationsTab = operationsTabs.find((t) => t.id === activeTab);

  // Parcel search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const searchRef = useRef(null);
  const debounceRef = useRef(null);

  const doSearch = useCallback(
    async (q) => {
      if (!q || q.length < 2) {
        setSearchResults([]);
        setSearching(false);
        return;
      }
      setSearching(true);
      try {
        const res = await fetch(
          `/api/analytics/search?q=${encodeURIComponent(q)}&role=${encodeURIComponent(selectedRole || 'Revenue Officer')}`
        );
        if (res.ok) {
          const data = await res.json();
          setSearchResults(data.results || []);
        }
      } catch {
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    },
    [selectedRole]
  );

  const handleSearchChange = (e) => {
    const v = e.target.value;
    setSearchQuery(v);
    clearTimeout(debounceRef.current);
    if (v.length < 2) {
      setSearchResults([]);
      setSearching(false);
      return;
    }
    setSearching(true);
    debounceRef.current = setTimeout(() => doSearch(v), 300);
  };

  const handleSelectResult = (pid) => {
    setSearchQuery('');
    setSearchResults([]);
    setShowDropdown(false);
    if (onSelectParcel) {
      onSelectParcel(pid);
    } else {
      setActiveTab('map');
    }
  };

  // Close search dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-4 py-2.5 shadow-2xl backdrop-blur-md bg-slate-950/90">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Brand & Positioning */}
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center shadow-lg shadow-amber-500/20 shrink-0">
            <Shield className="w-5 h-5 text-slate-950 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-black bg-gradient-to-r from-amber-400 via-amber-200 to-white bg-clip-text text-transparent tracking-tight">
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
          {/* Parcel Search Bar */}
          <div className="relative" ref={searchRef}>
            <div className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs">
              <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <input
                type="text"
                value={searchQuery}
                onChange={handleSearchChange}
                onFocus={() => setShowDropdown(true)}
                placeholder="Search parcel / survey / ULPIN"
                className="bg-transparent text-slate-200 placeholder:text-slate-500 focus:outline-none w-44 text-xs"
              />
              {searchQuery && (
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setSearchResults([]);
                  }}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            {/* Search Dropdown */}
            {showDropdown && searchQuery.length >= 2 && (
              <div className="absolute top-full mt-1 right-0 w-80 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-50 max-h-72 overflow-y-auto">
                {searching ? (
                  <div className="p-3 text-xs text-slate-400 text-center">Searching…</div>
                ) : searchResults.length === 0 ? (
                  <div className="p-3 text-xs text-slate-400 text-center">No parcels found for "{searchQuery}"</div>
                ) : (
                  searchResults.map((r) => (
                    <button
                      key={r.parcel_id}
                      onClick={() => handleSelectResult(r.parcel_id)}
                      className="w-full text-left px-3 py-2 hover:bg-slate-800 border-b border-slate-800 last:border-0 transition cursor-pointer"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-amber-300 text-xs">{r.parcel_id}</span>
                        <span className="text-[10px] text-slate-400">{r.village}</span>
                      </div>
                      <div className="flex items-center justify-between mt-0.5">
                        <span className="text-[10px] text-slate-400">
                          Sy. {r.survey_no} · ULPIN {r.ulpin}
                        </span>
                        {selectedRole !== 'Citizen' && (
                          <span className="text-[10px] text-slate-300">{r.owner_name}</span>
                        )}
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Status Modal Trigger */}
          <button
            onClick={() => setShowStatusModal(true)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition cursor-pointer"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
            <span className="hidden sm:inline">Engine Status</span>
            <span className="sm:hidden">Engine</span>
          </button>

          {/* Indic Multilingual Language Selector (Sarvam AI) */}
          <div className="relative" ref={langDropdownRef}>
            <button
              onClick={() => setShowLangDropdown(!showLangDropdown)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs font-bold text-slate-200 border border-slate-700 transition cursor-pointer shadow-sm"
              title="Select Language (Sarvam AI Indic Platform)"
            >
              <Globe className="w-3.5 h-3.5 text-amber-400" />
              <span>
                {supportedLanguages.find((l) => l.code === lang)?.native || 'English'}
              </span>
              <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${showLangDropdown ? 'rotate-180' : ''}`} />
            </button>

            {showLangDropdown && (
              <div className="absolute top-full mt-1.5 right-0 w-48 bg-slate-900/98 backdrop-blur-xl border border-slate-700 rounded-xl shadow-2xl z-[9999] p-1.5 space-y-0.5 animate-in fade-in zoom-in-95 duration-150">
                <div className="px-2 py-1 text-[9px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 flex items-center justify-between">
                  <span>Indic Languages</span>
                  <span className="text-amber-400 font-mono text-[8px]">IndicTrans</span>
                </div>
                {supportedLanguages.map((item) => {
                  const isSelected = lang === item.code;
                  return (
                    <button
                      key={item.code}
                      onClick={() => {
                        setLang(item.code);
                        setShowLangDropdown(false);
                      }}
                      className={`w-full text-left flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition cursor-pointer ${
                        isSelected
                          ? 'bg-amber-500/15 text-amber-300 font-bold border border-amber-500/30'
                          : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span>{item.flag}</span>
                        <span>{item.native}</span>
                        <span className="text-[10px] text-slate-500 font-normal">({item.name})</span>
                      </div>
                      {isSelected && <Check className="w-3.5 h-3.5 text-amber-400" />}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Demo Walkthrough Trigger */}
          <button
            onClick={onStartDemo}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-bold transition cursor-pointer"
            title="Watch the 90-second guided demo tour"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span className="hidden sm:inline">Demo Tour</span>
          </button>

          {/* Odisha Bhulekh RoR Intelligence Trigger */}
          {onOpenOdishaModal && (
            <button
              onClick={onOpenOdishaModal}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 text-xs font-bold transition cursor-pointer shadow-sm shadow-emerald-950/30"
              title="Query Odisha Bhulekh Record of Rights (bhulekh.ori.nic.in)"
            >
              <span>📜</span>
              <span className="hidden sm:inline">Odisha RoR (ଭୂଲେଖ)</span>
              <span className="sm:hidden">Odisha</span>
            </button>
          )}

          {/* User Profile & Auth State */}
          {currentUser ? (
            <div className="flex items-center gap-2 pl-1.5 border-l border-slate-800">
              <div className="flex items-center gap-2 bg-slate-900/90 py-1 px-2.5 rounded-xl border border-slate-800 text-xs shadow-md">
                <div
                  className={`w-5 h-5 rounded-full font-bold flex items-center justify-center text-[9px] ${
                    currentUser.role === 'District Collector'
                      ? 'bg-purple-500 text-white'
                      : currentUser.role === 'Revenue Officer'
                      ? 'bg-amber-500 text-slate-950'
                      : 'bg-emerald-500 text-slate-950'
                  }`}
                >
                  {currentUser.name ? currentUser.name.charAt(0) : 'U'}
                </div>
                <div className="text-left">
                  <div className="text-[11px] font-bold text-slate-200 truncate max-w-[120px] leading-tight">
                    {currentUser.name}
                  </div>
                  <div
                    className={`text-[8px] uppercase font-black tracking-wider ${
                      currentUser.role === 'District Collector'
                        ? 'text-purple-400'
                        : currentUser.role === 'Revenue Officer'
                        ? 'text-amber-400'
                        : 'text-emerald-400'
                    }`}
                  >
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

      {/* Streamlined Tab Navigation with Smart Dropdowns */}
      <div
        ref={navDropdownRef}
        className="max-w-7xl mx-auto mt-2.5 pt-2 border-t border-slate-800/60 flex items-center gap-1.5 overflow-visible flex-wrap"
      >
        {/* 1. Core Primary Tabs */}
        {primaryTabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setOpenNavDropdown(null);
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap cursor-pointer ${
                isActive
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-sm font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-amber-400' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  className={`text-[8px] font-black px-1 py-0.2 rounded uppercase ${
                    tab.badge === 'Executive'
                      ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                      : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}

        {/* 2. Verification & Spatial Intelligence Dropdown (Officers / Collectors) */}
        {isOfficerOrCollector && (
          <div className="relative">
            <button
              onClick={() =>
                setOpenNavDropdown(openNavDropdown === 'verification' ? null : 'verification')
              }
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap cursor-pointer ${
                activeVerificationTab
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-sm font-bold'
                  : openNavDropdown === 'verification'
                  ? 'bg-slate-800 text-slate-100 border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
              }`}
            >
              {activeVerificationTab ? (
                <>
                  <activeVerificationTab.icon className="w-3.5 h-3.5 text-amber-400" />
                  <span>{activeVerificationTab.label}</span>
                </>
              ) : (
                <>
                  <Compass className="w-3.5 h-3.5 text-slate-400" />
                  <span>Verification & Insights</span>
                </>
              )}
              <ChevronDown
                className={`w-3 h-3 transition-transform duration-200 ${
                  openNavDropdown === 'verification' ? 'rotate-180 text-amber-400' : 'text-slate-500'
                }`}
              />
            </button>

            {/* Dropdown Menu */}
            {openNavDropdown === 'verification' && (
              <div className="absolute left-0 top-full mt-1.5 w-72 bg-slate-900/98 backdrop-blur-xl border border-slate-700/90 rounded-xl shadow-2xl z-50 p-1.5 space-y-1 animate-in fade-in zoom-in-95 duration-150">
                <div className="px-2.5 py-1 text-[10px] font-black uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  Cadastral & Spatial Intelligence
                </div>
                {verificationTabs.map((item) => {
                  const Icon = item.icon;
                  const isSelected = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        setActiveTab(item.id);
                        setOpenNavDropdown(null);
                      }}
                      className={`w-full text-left flex items-start gap-2.5 px-2.5 py-2 rounded-lg transition cursor-pointer ${
                        isSelected
                          ? 'bg-amber-500/15 text-amber-200 border border-amber-500/25'
                          : 'hover:bg-slate-800/80 text-slate-300 hover:text-white border border-transparent'
                      }`}
                    >
                      <div
                        className={`p-1.5 rounded-lg shrink-0 mt-0.5 ${
                          isSelected ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold leading-tight">{item.label}</span>
                          {isSelected && <Check className="w-3.5 h-3.5 text-amber-400" />}
                        </div>
                        <p className="text-[10px] text-slate-400 line-clamp-1 mt-0.5">
                          {item.description}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* 3. Revenue Operations & Records Dropdown (Officers / Collectors) */}
        {isOfficerOrCollector && (
          <div className="relative">
            <button
              onClick={() =>
                setOpenNavDropdown(openNavDropdown === 'operations' ? null : 'operations')
              }
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition whitespace-nowrap cursor-pointer ${
                activeOperationsTab
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-sm font-bold'
                  : openNavDropdown === 'operations'
                  ? 'bg-slate-800 text-slate-100 border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
              }`}
            >
              {activeOperationsTab ? (
                <>
                  <activeOperationsTab.icon className="w-3.5 h-3.5 text-amber-400" />
                  <span>{activeOperationsTab.label}</span>
                </>
              ) : (
                <>
                  <FileSpreadsheet className="w-3.5 h-3.5 text-slate-400" />
                  <span>Revenue Operations</span>
                </>
              )}
              <ChevronDown
                className={`w-3 h-3 transition-transform duration-200 ${
                  openNavDropdown === 'operations' ? 'rotate-180 text-amber-400' : 'text-slate-500'
                }`}
              />
            </button>

            {/* Dropdown Menu */}
            {openNavDropdown === 'operations' && (
              <div className="absolute left-0 top-full mt-1.5 w-76 bg-slate-900/98 backdrop-blur-xl border border-slate-700/90 rounded-xl shadow-2xl z-50 p-1.5 space-y-1 animate-in fade-in zoom-in-95 duration-150">
                <div className="px-2.5 py-1 text-[10px] font-black uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  Administrative Actions & Records
                </div>
                {operationsTabs.map((item) => {
                  const Icon = item.icon;
                  const isSelected = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        setActiveTab(item.id);
                        setOpenNavDropdown(null);
                      }}
                      className={`w-full text-left flex items-start gap-2.5 px-2.5 py-2 rounded-lg transition cursor-pointer ${
                        isSelected
                          ? 'bg-amber-500/15 text-amber-200 border border-amber-500/25'
                          : 'hover:bg-slate-800/80 text-slate-300 hover:text-white border border-transparent'
                      }`}
                    >
                      <div
                        className={`p-1.5 rounded-lg shrink-0 mt-0.5 ${
                          isSelected ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold leading-tight">{item.label}</span>
                          {isSelected && <Check className="w-3.5 h-3.5 text-amber-400" />}
                        </div>
                        <p className="text-[10px] text-slate-400 line-clamp-1 mt-0.5">
                          {item.description}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
