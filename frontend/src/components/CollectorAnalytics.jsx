import React, { useState } from 'react';
import { BarChart3, TrendingUp, AlertOctagon, Scale, ShieldCheck, CheckCircle, Users, Activity, FileCheck, Landmark } from 'lucide-react';

export default function CollectorAnalytics({ onSelectParcel }) {
  const [selectedMandal, setSelectedMandal] = useState('All');

  // Aggregated synthetic mandal statistics
  const mandalStats = [
    {
      name: 'Shamshabad',
      totalParcels: 15,
      cleanParcels: 11,
      flaggedParcels: 4,
      avgRiskScore: 34.2,
      pendingDisputes: 3,
      topAnomaly: 'Severe Overlap (Sy. 101/A)',
      vulnerabilityTier: 'HIGH'
    },
    {
      name: 'Mamidipally',
      totalParcels: 15,
      cleanParcels: 11,
      flaggedParcels: 4,
      avgRiskScore: 29.8,
      pendingDisputes: 2,
      topAnomaly: 'Boundary Gap & Area Deviation',
      vulnerabilityTier: 'MEDIUM'
    },
    {
      name: 'Kothwalguda',
      totalParcels: 12,
      cleanParcels: 11,
      flaggedParcels: 1,
      avgRiskScore: 18.5,
      pendingDisputes: 1,
      topAnomaly: 'Land-Use Mismatch (Sy. 135)',
      vulnerabilityTier: 'LOW'
    }
  ];

  const anomalyDistribution = [
    { type: 'Spatial Boundary Overlaps', percentage: 33, count: 3, color: 'bg-rose-500' },
    { type: 'Rapid Resale Title Velocity', percentage: 33, count: 3, color: 'bg-amber-500' },
    { type: 'RoR Area Deviation >15%', percentage: 22, count: 2, color: 'bg-purple-500' },
    { type: 'Satellite Land-Use Mismatch', percentage: 12, count: 1, color: 'bg-blue-500' }
  ];

  const recentAudits = [
    {
      parcel_id: 'P-105',
      officer: 'Tahsildar Shamshabad',
      action: 'OVERRIDE',
      reason: 'Physical boundary stones match survey map; court case disposed.',
      hash: '0x8f2d...93a1',
      time: '12 mins ago'
    },
    {
      parcel_id: 'P-112',
      officer: 'Revenue Inspector Mamidipally',
      action: 'APPROVE',
      reason: 'Area correction memo submitted under RoR Act Sec 4.',
      hash: '0x3c7e...b412',
      time: '45 mins ago'
    },
    {
      parcel_id: 'P-108',
      officer: 'Tahsildar Shamshabad',
      action: 'HELD_PENDING',
      reason: 'Referred to District Anti-Benami Cell for velocity check.',
      hash: '0x1a8f...cc90',
      time: '2 hours ago'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Executive Header Banner */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
              <Landmark className="w-3 h-3" />
              District Administration • Rangareddy
            </span>
            <span className="text-xs text-slate-400">• Executive Intelligence</span>
          </div>
          <h2 className="text-2xl font-black text-slate-100 mt-1">
            District Collector Executive Analytics & Vulnerability Index
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Macro-level governance metrics, revenue court dispute velocity, and officer audit oversight across all Mandals.
          </p>
        </div>

        {/* Global Summary Stats */}
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-center min-w-[100px]">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Total Digitized</div>
            <div className="text-xl font-extrabold text-slate-100 mt-0.5">42 Parcels</div>
          </div>
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-center min-w-[100px]">
            <div className="text-[10px] text-rose-300 uppercase font-semibold">Flagged Risk</div>
            <div className="text-xl font-extrabold text-rose-400 mt-0.5">9 Anomalies</div>
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-center min-w-[100px]">
            <div className="text-[10px] text-emerald-300 uppercase font-semibold">Clean Rate</div>
            <div className="text-xl font-extrabold text-emerald-400 mt-0.5">78.6%</div>
          </div>
        </div>
      </div>

      {/* Grid: Mandal Vulnerability Table & Anomaly Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Mandal Vulnerability Index Table */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-amber-400" />
              <span>Mandal Vulnerability & Anomaly Ranking</span>
            </h3>
            <span className="text-xs text-slate-400">Ranked by Composite Risk Score</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  <th className="pb-3 px-2">Mandal</th>
                  <th className="pb-3 px-2">Parcels</th>
                  <th className="pb-3 px-2">Anomaly Rate</th>
                  <th className="pb-3 px-2">Court Disputes</th>
                  <th className="pb-3 px-2">Primary Anomaly Vector</th>
                  <th className="pb-3 px-2 text-right">Risk Tier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs">
                {mandalStats.map((m) => (
                  <tr key={m.name} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-2 font-bold text-slate-200">{m.name}</td>
                    <td className="py-3.5 px-2 text-slate-300">{m.totalParcels}</td>
                    <td className="py-3.5 px-2 font-bold text-amber-300">
                      {Math.round((m.flaggedParcels / m.totalParcels) * 100)}% ({m.flaggedParcels}/{m.totalParcels})
                    </td>
                    <td className="py-3.5 px-2 font-semibold text-rose-400">{m.pendingDisputes} Cases</td>
                    <td className="py-3.5 px-2 text-slate-400 text-[11px]">{m.topAnomaly}</td>
                    <td className="py-3.5 px-2 text-right">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        m.vulnerabilityTier === 'HIGH'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : m.vulnerabilityTier === 'MEDIUM'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      }`}>
                        {m.vulnerabilityTier}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Anomaly Breakdown Bars */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-amber-400" />
              <span>Multi-Modal Anomaly Distribution</span>
            </h3>

            <div className="space-y-3 pt-1">
              {anomalyDistribution.map((item) => (
                <div key={item.type} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-300">{item.type}</span>
                    <span className="text-amber-400 font-bold">{item.percentage}% ({item.count})</span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-2 border border-slate-800 overflow-hidden">
                    <div className={`${item.color} h-full rounded-full transition-all duration-500`} style={{ width: `${item.percentage}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400">
            <span className="font-bold text-slate-300">Executive Directive:</span> High concentration of rapid-resale velocity detected in Shamshabad Mandal requires field mutation holds.
          </div>
        </div>
      </div>

      {/* Lower Row: Officer Audit Trail Accountability Log */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-slate-200">
              Live Officer Decision Ledger (Section 6 DPDP Act 2023 Audit Trail)
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">Immutable SHA-256 Signatures</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {recentAudits.map((a) => (
            <div key={a.parcel_id} className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-black text-amber-400 text-sm">Parcel {a.parcel_id}</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                  a.action === 'APPROVE' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                }`}>
                  {a.action}
                </span>
              </div>
              <p className="text-slate-300 leading-relaxed text-[11px] font-medium">"{a.reason}"</p>
              <div className="pt-2 border-t border-slate-800 flex justify-between text-[10px] text-slate-400 font-mono">
                <span>{a.officer}</span>
                <span className="text-amber-300">{a.hash}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
