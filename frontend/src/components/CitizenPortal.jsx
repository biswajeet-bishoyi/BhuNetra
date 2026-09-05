import React, { useState } from 'react';
import { User, FileText, CheckCircle, Clock, AlertTriangle, Download, Send, RefreshCw, ShieldCheck, MapPin, Search } from 'lucide-react';

export default function CitizenPortal({ onSelectParcel }) {
  const [activeTab, setActiveTab] = useState('passbook'); // 'passbook' | 'mutation' | 'grievance'
  const [searchQuery, setSearchQuery] = useState('');
  const [grievanceText, setGrievanceText] = useState('');
  const [grievanceCategory, setGrievanceCategory] = useState('BOUNDARY_DISPUTE');
  const [grievances, setGrievances] = useState([
    {
      id: 'GRV-2026-OD-8841',
      parcel_id: 'P-OD-102',
      category: 'Boundary Encroachment',
      status: 'UNDER_INVESTIGATION',
      filed_date: '2026-08-26',
      sla_days: 15,
      days_left: 7,
      description: 'Adjacent plot owner constructed illegal tin shed over survey line.'
    }
  ]);
  const [mutationList, setMutationList] = useState([
    {
      mutation_id: 'MUT-2026-0412',
      parcel_id: 'P-OD-102',
      type: 'INHERITANCE_SUCCESSION',
      applicant: 'Sudrusti Sethi',
      current_step: 3,
      steps: ['Application Registered', 'e-KYC Verified', 'Public Notice (30 Days)', 'Revenue Officer Approval', 'RoR Updated'],
      status: 'NOTICE_PERIOD_ACTIVE',
      expiry_date: '2026-09-28'
    }
  ]);

  const handleFileGrievance = (e) => {
    e.preventDefault();
    if (!grievanceText) return;
    const newG = {
      id: `GRV-2026-${Math.floor(1000 + Math.random() * 9000)}`,
      parcel_id: 'P-OD-102',
      category: grievanceCategory.replace(/_/g, ' '),
      status: 'PENDING_TRIAGE',
      filed_date: new Date().toISOString().split('T')[0],
      sla_days: 15,
      days_left: 15,
      description: grievanceText
    };
    setGrievances([newG, ...grievances]);
    setGrievanceText('');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
              Citizen Self-Service · Digital Land Record Portal
            </span>
            <h2 className="text-xl font-extrabold text-slate-100">Farmer & Landholder Dashboard</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            View your verified land passbook, download Section 65B certified RoR / 7-12 records, track live mutation status, and file grievances with statutory SLA tracking.
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex bg-slate-900/80 p-1 rounded-xl border border-slate-800 text-xs font-bold">
          <button
            onClick={() => setActiveTab('passbook')}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
              activeTab === 'passbook' ? 'bg-emerald-500 text-slate-950 shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Digital Passbook
          </button>
          <button
            onClick={() => setActiveTab('mutation')}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
              activeTab === 'mutation' ? 'bg-emerald-500 text-slate-950 shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Mutation Tracker
          </button>
          <button
            onClick={() => setActiveTab('grievance')}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
              activeTab === 'grievance' ? 'bg-emerald-500 text-slate-950 shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Grievance Redressal
          </button>
        </div>
      </div>

      {/* Tab 1: Digital Land Passbook */}
      {activeTab === 'passbook' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Parcel Passbook Card 1 */}
            <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col justify-between space-y-4 hover:border-emerald-500/40 transition">
              <div>
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    CLEAR TITLE · 100% HEALTH
                  </span>
                  <span className="text-xs text-slate-400 font-mono">P-OD-102</span>
                </div>
                <h4 className="text-base font-bold text-slate-100 mt-2">Plot No. 45/0 · Khata 102</h4>
                <p className="text-xs text-slate-400">Village: Chhatrapur, Tehsil: Chhatrapur, Ganjam (Odisha)</p>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block">Recorded Extent</span>
                    <span className="font-bold text-slate-200">1,250 Sq.m</span>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block">Land Use</span>
                    <span className="font-bold text-emerald-400">Agricultural</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => onSelectParcel && onSelectParcel('P-OD-102')}
                  className="flex-1 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                  <span>View on Map</span>
                </button>
                <button
                  onClick={() => window.open('/api/certificate/generate/P-OD-102', '_blank')}
                  className="py-2 px-3 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 text-xs font-bold transition border border-emerald-500/40 cursor-pointer flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>RoR PDF</span>
                </button>
              </div>
            </div>

            {/* Parcel Passbook Card 2 */}
            <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col justify-between space-y-4 hover:border-cyan-500/40 transition">
              <div>
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                    DHARANI VERIFIED
                  </span>
                  <span className="text-xs text-slate-400 font-mono">P-105</span>
                </div>
                <h4 className="text-base font-bold text-slate-100 mt-2">Survey No. 105/A</h4>
                <p className="text-xs text-slate-400">Shamshabad, Ranga Reddy (Telangana)</p>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block">Recorded Extent</span>
                    <span className="font-bold text-slate-200">2,420 Sq.m</span>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block">Land Use</span>
                    <span className="font-bold text-amber-400">Residential</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => onSelectParcel && onSelectParcel('P-105')}
                  className="flex-1 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                  <span>View on Map</span>
                </button>
                <button
                  onClick={() => window.open('/api/certificate/generate/P-105', '_blank')}
                  className="py-2 px-3 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-xs font-bold transition border border-cyan-500/40 cursor-pointer flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Pahani PDF</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Mutation Tracker */}
      {activeTab === 'mutation' && (
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-slate-100">Live Title Mutation Status</h3>
          {mutationList.map((m) => (
            <div key={m.mutation_id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-sm text-amber-300">{m.mutation_id}</span>
                    <span className="text-xs text-slate-400">· Parcel {m.parcel_id}</span>
                  </div>
                  <div className="text-xs text-slate-300 mt-0.5">
                    Applicant: <strong>{m.applicant}</strong> ({m.type.replace(/_/g, ' ')})
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded text-[10px] font-bold font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30">
                  {m.status.replace(/_/g, ' ')} · Notice Exp: {m.expiry_date}
                </span>
              </div>

              {/* Progress Stepper */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
                {m.steps.map((stepName, idx) => (
                  <div
                    key={idx}
                    className={`p-2.5 rounded-lg border text-center text-xs flex flex-col items-center justify-center gap-1 ${
                      idx + 1 < m.current_step
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        : idx + 1 === m.current_step
                        ? 'bg-amber-500/20 border-amber-500/50 text-amber-300 shadow'
                        : 'bg-slate-950 border-slate-800 text-slate-600'
                    }`}
                  >
                    <span className="text-[10px] font-mono">Step {idx + 1}</span>
                    <span className="font-bold text-[11px]">{stepName}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 3: Grievance Redressal */}
      {activeTab === 'grievance' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* File New Grievance */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Send className="w-4 h-4 text-emerald-400" />
              <span>File Land Grievance or Encroachment Report</span>
            </h3>

            <form onSubmit={handleFileGrievance} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">Grievance Category</label>
                <select
                  value={grievanceCategory}
                  onChange={(e) => setGrievanceCategory(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="BOUNDARY_DISPUTE">Boundary Encroachment / Pillar Removal</option>
                  <option value="ROR_NAME_ERROR">RoR / Passbook Clerical Name Error</option>
                  <option value="MUTATION_DELAY">Unreasonable Delay in Mutation Order</option>
                  <option value="ILLEGAL_CONSTRUCTION">Illegal Construction on Agricultural Land</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">Description & Evidence Details</label>
                <textarea
                  rows={4}
                  value={grievanceText}
                  onChange={(e) => setGrievanceText(e.target.value)}
                  placeholder="Describe the issue, survey number, and affected plot area..."
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 transition cursor-pointer shadow-lg shadow-emerald-500/20"
              >
                <Send className="w-4 h-4" />
                <span>Submit Grievance to Revenue Tahsildar</span>
              </button>
            </form>
          </div>

          {/* Filed Grievances & SLA Tracking */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-400" />
              <span>Track Active Grievances ({grievances.length})</span>
            </h3>

            <div className="space-y-3">
              {grievances.map((g) => (
                <div key={g.id} className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-amber-300">{g.id}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      {g.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="text-xs font-bold text-slate-200">{g.category} · Parcel {g.parcel_id}</div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{g.description}</p>
                  <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-800">
                    <span>Filed on: {g.filed_date}</span>
                    <span className="text-amber-400 font-bold">SLA: {g.days_left} Days Remaining</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
