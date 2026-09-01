import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, AlertOctagon, Scale, ShieldCheck, CheckCircle, Users, Activity, FileCheck, Landmark, RefreshCw, Loader2 } from 'lucide-react';

export default function CollectorAnalytics({ onSelectParcel }) {
  const [mandalData, setMandalData] = useState(null);
  const [recentAudits, setRecentAudits] = useState([]);
  const [anomalyDistribution, setAnomalyDistribution] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMandal, setSelectedMandal] = useState('All');

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const [statsRes, auditRes] = await Promise.all([
        fetch('/api/analytics/mandal-stats'),
        fetch('/api/review-queue/audit-log'),
      ]);
      if (statsRes.ok) {
        const data = await statsRes.json();
        setMandalData(data);

        // Build anomaly distribution from top_anomalies across mandals
        const allAnomalies = {};
        for (const m of data.mandals || []) {
          for (const a of m.top_anomalies || []) {
            const label = ANOMALY_LABELS[a.type] || a.type;
            allAnomalies[label] = (allAnomalies[label] || 0) + a.count;
          }
        }
        const total = Object.values(allAnomalies).reduce((s, v) => s + v, 0) || 1;
        const palette = ['bg-rose-500', 'bg-amber-500', 'bg-purple-500', 'bg-blue-500', 'bg-sky-500'];
        const items = Object.entries(allAnomalies)
          .map(([type, count], i) => ({
            type,
            count,
            percentage: Math.round((count / total) * 100),
            color: palette[i % palette.length],
          }))
          .sort((a, b) => b.count - a.count);
        setAnomalyDistribution(items);
      }
      if (auditRes.ok) {
        const audits = await auditRes.json();
        setRecentAudits(audits.slice(0, 6));
      }
    } catch (err) {
      console.error('Failed to load analytics', err);
    } finally {
      setLoading(false);
    }
  };

  const ANOMALY_LABELS = {
    gis_validation: 'Spatial Boundary Overlaps',
    ownership_intelligence: 'Rapid Resale Title Velocity',
    satellite_verification: 'Satellite Land-Use Mismatch',
    registry_ocr: 'RoR Area Deviation >15%',
  };

  const mandalStats = mandalData?.mandals || [];
  const totalParcels = mandalData?.total_parcels || 0;
  const totalFlagged = mandalData?.total_flagged || 0;
  const cleanRate = mandalData?.clean_rate || 0;

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
            Macro-level governance metrics from live registry data — all Mandals, all engines.
          </p>
        </div>

        {/* Refresh button */}
        <button
          onClick={fetchAnalytics}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-slate-400 text-sm gap-2">
          <Loader2 className="w-5 h-5 text-amber-400 animate-spin" />
          <span>Computing mandal statistics from live registry data…</span>
        </div>
      ) : mandalData ? (
        <>
          {/* Global Summary Stats — live from API */}
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-center min-w-[100px]">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Total Digitized</div>
              <div className="text-xl font-extrabold text-slate-100 mt-0.5">{totalParcels} Parcels</div>
            </div>
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-center min-w-[100px]">
              <div className="text-[10px] text-rose-300 uppercase font-semibold">Flagged Risk</div>
              <div className="text-xl font-extrabold text-rose-400 mt-0.5">{totalFlagged} Anomalies</div>
            </div>
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-center min-w-[100px]">
              <div className="text-[10px] text-emerald-300 uppercase font-semibold">Clean Rate</div>
              <div className="text-xl font-extrabold text-emerald-400 mt-0.5">{cleanRate}%</div>
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
                <span className="text-xs text-slate-400">Ranked by Avg Risk Score</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      <th className="pb-3 px-2">Mandal</th>
                      <th className="pb-3 px-2">Parcels</th>
                      <th className="pb-3 px-2">Anomaly Rate</th>
                      <th className="pb-3 px-2">Avg Risk</th>
                      <th className="pb-3 px-2">Top Anomaly</th>
                      <th className="pb-3 px-2 text-right">Tier</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-xs">
                    {mandalStats.map((m) => (
                      <tr key={m.name} className="hover:bg-slate-800/40 transition cursor-pointer" onClick={() => onSelectParcel && onSelectParcel(m.name)}>
                        <td className="py-3.5 px-2 font-bold text-slate-200">{m.name}</td>
                        <td className="py-3.5 px-2 text-slate-300">{m.total_parcels}</td>
                        <td className="py-3.5 px-2 font-bold text-amber-300">
                          {Math.round(((m.yellow_parcels + m.red_parcels) / m.total_parcels) * 100)}%
                          ({m.yellow_parcels + m.red_parcels}/{m.total_parcels})
                        </td>
                        <td className="py-3.5 px-2 font-bold text-slate-200">{m.avg_risk_score}</td>
                        <td className="py-3.5 px-2 text-slate-400 text-[11px]">
                          {m.top_anomalies?.[0]?.type
                            ? ANOMALY_LABELS[m.top_anomalies[0].type] || m.top_anomalies[0].type
                            : '—'}
                        </td>
                        <td className="py-3.5 px-2 text-right">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            m.vulnerability_tier === 'HIGH'
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : m.vulnerability_tier === 'MEDIUM'
                              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                              : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          }`}>
                            {m.vulnerability_tier}
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

                {anomalyDistribution.length > 0 ? (
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
                ) : (
                  <p className="text-xs text-slate-500">No anomalies detected across the registry.</p>
                )}
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
              {recentAudits.length > 0 ? recentAudits.map((a) => (
                <div key={`${a.parcel_id}-${a.id}`} className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs">
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
                    <span>{a.officer_name}</span>
                    <span className="text-amber-300">{a.blockchain_hash ? `${a.blockchain_hash.slice(0,8)}…` : '—'}</span>
                  </div>
                </div>
              )) : (
                <div className="col-span-3 py-8 text-center text-slate-500 text-xs">
                  No officer decisions recorded yet.
                </div>
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="flex items-center justify-center py-20 text-slate-500 text-sm">
          <AlertOctagon className="w-5 h-5 mr-2" />
          Failed to load mandal statistics. Check that the backend is running.
        </div>
      )}
    </div>
  );
}
