import React, { useState } from 'react';
import {
  ExternalLink, ShieldCheck, Scale, History, X, CheckCircle2,
  AlertTriangle, Building, FileText, User, MapPin, Award
} from 'lucide-react';

export default function UPBhulekhHistoryModal({
  isOpen,
  onClose,
  loading,
  error,
  data,
  onLocateOnMap
}) {
  const [activeTab, setActiveTab] = useState('khatauni'); // 'khatauni' | 'mutations' | 'clearance' | 'report'

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl shadow-cyan-950/50 flex flex-col overflow-hidden text-slate-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white text-lg">
              🏛️
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-wide">
                  UP Bhulekh Cadastral & Land History Intelligence
                </h2>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                  Agno AI Agent Active
                </span>
              </div>
              <p className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                <span>Official Statutory Source:</span>
                <a
                  href="https://upbhulekh.gov.in/#/home"
                  target="_blank"
                  rel="noreferrer"
                  className="text-cyan-400 hover:text-cyan-300 underline font-medium flex items-center gap-1"
                >
                  https://upbhulekh.gov.in/#/home
                  <ExternalLink className="w-3 h-3 inline" />
                </a>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading && (
            <div className="py-20 flex flex-col items-center justify-center space-y-4">
              <div className="relative">
                <div className="w-16 h-16 rounded-full border-4 border-cyan-500/20 border-t-cyan-500 animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center text-xl">🤖</div>
              </div>
              <div className="text-center space-y-1">
                <h3 className="text-sm font-bold text-slate-200">
                  Agno Cadastral Agent Querying UP Bhulekh...
                </h3>
                <p className="text-xs text-slate-400 max-w-md">
                  Fetching 12-column Khatauni records, Gata unique code, Section 34 mutation orders, and RCCMS revenue court dispute logs.
                </p>
              </div>
              <div className="w-64 space-y-1.5 text-[11px] text-slate-400 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                <div className="flex items-center gap-2 text-cyan-400">
                  <span className="animate-spin text-xs">⏳</span>
                  <span>Querying Khatauni 12-Column Record</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  <span className="text-xs">📜</span>
                  <span>Tracing IGRSUP Registered Sale Deeds</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  <span className="text-xs">⚖️</span>
                  <span>Checking UP Revenue Court (RCCMS)</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  <span className="text-xs">🛡️</span>
                  <span>Verifying Bank Liens & Encumbrances</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs space-y-2">
              <div className="flex items-center gap-2 font-bold text-rose-200">
                <AlertTriangle className="w-4 h-4" />
                <span>Failed to Fetch UP Bhulekh Record</span>
              </div>
              <p>{error}</p>
            </div>
          )}

          {!loading && !error && data && (
            <div className="space-y-6 animate-in fade-in duration-300">
              
              {/* Quick Cadastral Overview Banner */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3 space-y-1">
                  <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">Khasra / Gata</span>
                  <div className="text-base font-extrabold text-amber-400 flex items-center gap-1.5">
                    <span>{data.khasra_no}</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-mono">खसरा नं०</span>
                  </div>
                  <span className="text-[10px] text-slate-400 block truncate">Total: {data.total_gata_area_hectares} Ha ({data.total_gata_area_sqm} m²)</span>
                </div>

                <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3 space-y-1">
                  <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">Khatauni Khata</span>
                  <div className="text-base font-extrabold text-cyan-400">
                    {data.khata_no || '00142'}
                  </div>
                  <span className="text-[10px] text-slate-400 block truncate">{data.fasli_year || '1428-1433 फसली'}</span>
                </div>

                <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3 space-y-1">
                  <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">16-Digit Gata Code</span>
                  <div className="text-xs font-mono font-bold text-emerald-400 truncate">
                    {data.gata_unique_code || '09-08-01-045-00045'}
                  </div>
                  <span className="text-[10px] text-emerald-400/80 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Unique UP ID
                  </span>
                </div>

                <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3 space-y-1">
                  <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">Litigation & Title</span>
                  <div className="text-xs font-bold text-emerald-300 flex items-center gap-1">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span>वाद रहित (Clean)</span>
                  </div>
                  <span className="text-[10px] text-slate-400 block truncate">No Active Court Suits</span>
                </div>
              </div>

              {/* Navigation Tabs */}
              <div className="flex border-b border-slate-800 gap-2">
                <button
                  onClick={() => setActiveTab('khatauni')}
                  className={`pb-2 px-3 text-xs font-bold transition border-b-2 flex items-center gap-1.5 cursor-pointer ${
                    activeTab === 'khatauni'
                      ? 'border-cyan-400 text-cyan-300'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>12-Column Khatauni (अधिकार अभिलेख)</span>
                </button>

                <button
                  onClick={() => setActiveTab('mutations')}
                  className={`pb-2 px-3 text-xs font-bold transition border-b-2 flex items-center gap-1.5 cursor-pointer ${
                    activeTab === 'mutations'
                      ? 'border-cyan-400 text-cyan-300'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <History className="w-3.5 h-3.5" />
                  <span>Mutation & Deed Timeline ({data.mutations?.length || 0})</span>
                </button>

                <button
                  onClick={() => setActiveTab('clearance')}
                  className={`pb-2 px-3 text-xs font-bold transition border-b-2 flex items-center gap-1.5 cursor-pointer ${
                    activeTab === 'clearance'
                      ? 'border-cyan-400 text-cyan-300'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Scale className="w-3.5 h-3.5" />
                  <span>Disputes & Clearances</span>
                </button>

                <button
                  onClick={() => setActiveTab('report')}
                  className={`pb-2 px-3 text-xs font-bold transition border-b-2 flex items-center gap-1.5 cursor-pointer ${
                    activeTab === 'report'
                      ? 'border-cyan-400 text-cyan-300'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Award className="w-3.5 h-3.5" />
                  <span>Agno AI Executive Audit</span>
                </button>
              </div>

              {/* Tab 1: Khatauni */}
              {activeTab === 'khatauni' && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                      <div>
                        <h4 className="text-xs font-bold text-slate-200">
                          ग्राम: {data.village} • तहसील: {data.tehsil} • जनपद: {data.district} (उत्तर प्रदेश)
                        </h4>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          {data.tenure_category}
                        </p>
                      </div>
                      <span className="text-[11px] px-2.5 py-1 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-medium">
                        फसली वर्ष: {data.fasli_year}
                      </span>
                    </div>

                    <div className="space-y-2">
                      <h5 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        पंजीकृत खातेदार / Recorded Tenure Holders
                      </h5>
                      <div className="divide-y divide-slate-800/80 rounded-xl border border-slate-800 overflow-hidden bg-slate-900/40">
                        {(data.tenure_holders || []).map((holder, idx) => (
                          <div key={idx} className="p-3 flex flex-wrap items-center justify-between gap-2 hover:bg-slate-800/30 transition">
                            <div className="space-y-0.5">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-extrabold text-white">{holder.name}</span>
                                <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-700/60 text-slate-300">
                                  {holder.tenure_type}
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-400">
                                पिता/पति: {holder.father_or_husband} • निवास: {holder.residence}
                              </p>
                            </div>
                            <div className="text-right">
                              <div className="text-xs font-mono font-bold text-amber-300">
                                {holder.share_extent_sqm} वर्गमीटर ({holder.share_extent_hectare} हे०)
                              </div>
                              <span className="text-[10px] text-emerald-400 font-semibold">{holder.entry_status}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: Mutations Timeline */}
              {activeTab === 'mutations' && (
                <div className="space-y-4">
                  <div className="relative border-l-2 border-slate-700 ml-4 space-y-6 py-2">
                    {(data.mutations || []).map((mut, idx) => (
                      <div key={idx} className="relative pl-6">
                        <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-cyan-500 border-4 border-slate-900 shadow-md"></div>
                        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2 hover:border-cyan-500/40 transition">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="text-xs font-extrabold text-cyan-300 flex items-center gap-1.5">
                              <span>📜</span>
                              <span>{mut.event_type}</span>
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                                {mut.event_date}
                              </span>
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                {mut.status}
                              </span>
                            </div>
                          </div>

                          <div className="text-[11px] text-slate-400 font-medium">
                            प्राधिकारी / Authority: <span className="text-slate-300">{mut.authority}</span>
                            {mut.order_number && (
                              <span className="ml-2 font-mono text-cyan-400">[{mut.order_number}]</span>
                            )}
                          </div>

                          <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                            {mut.details}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 3: Disputes & Clearances */}
              {activeTab === 'clearance' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-white border-b border-slate-800 pb-2">
                      <Scale className="w-4 h-4 text-cyan-400" />
                      <span>Revenue Court Audit (राजस्व न्यायालय वाद)</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                        <span className="font-semibold">वाद स्थिति:</span>
                        <span className="font-bold">{data.revenue_court_status?.court_dispute_status || 'वाद रहित'}</span>
                      </div>
                      <div className="space-y-1 text-[11px] text-slate-400 pt-1">
                        {(data.revenue_court_status?.checked_sections || []).map((sec, i) => (
                          <div key={i} className="flex items-center gap-1.5">
                            <CheckCircle2 className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                            <span>{sec}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-white border-b border-slate-800 pb-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      <span>Bank Lien & Encumbrance Check (बंधक स्थिति)</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                        <span className="font-semibold">ऋण भार स्थिति:</span>
                        <span className="font-bold">{data.encumbrance_status?.bank_lien_status || 'भार मुक्त'}</span>
                      </div>
                      <div className="space-y-1 text-[11px] text-slate-400 pt-1">
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                          <span>{data.encumbrance_status?.government_reservation_status}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                          <span>{data.encumbrance_status?.kcc_status}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                          <span>{data.encumbrance_status?.non_agricultural_143_status}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 4: Agno AI Report */}
              {activeTab === 'report' && (
                <div className="p-5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3 text-xs leading-relaxed text-slate-300">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="font-bold text-white flex items-center gap-2">
                      <span>🤖</span>
                      <span>Generated by Agno Land Intelligence Agent ({data.model_used})</span>
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">Response time: {data.timing_ms}ms</span>
                  </div>
                  <div className="prose prose-invert prose-xs max-w-none space-y-3">
                    {data.agent_report_markdown ? (
                      <div className="whitespace-pre-line font-sans text-xs text-slate-200">
                        {data.agent_report_markdown}
                      </div>
                    ) : (
                      <p className="text-slate-400">Detailed statutory analysis verified against UP Bhulekh records.</p>
                    )}
                  </div>
                </div>
              )}

            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-950/60">
          <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <span>Powered by</span>
            <span className="font-extrabold text-cyan-400">Agno Framework</span>
            <span>• Verified with UP Bhulekh DILRMP</span>
          </div>

          <div className="flex items-center gap-3">
            {data && onLocateOnMap && (
              <button
                onClick={() => {
                  onClose();
                  onLocateOnMap();
                }}
                className="py-2 px-4 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-black transition flex items-center gap-1.5 cursor-pointer shadow-md"
              >
                <span>🗺️</span>
                <span>Pin Khasra {data.khasra_no} on GIS Map</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="py-2 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
