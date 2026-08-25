import React, { useState, useEffect } from 'react';
import { Clock, ShieldAlert, ArrowRight, TrendingUp, AlertTriangle } from 'lucide-react';

export default function OwnershipTimeline({ selectedParcelId = 'P-108' }) {
  const [parcelId, setParcelId] = useState(selectedParcelId);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const sampleParcels = ['P-108', 'P-114', 'P-105', 'P-101'];

  useEffect(() => {
    fetchOwnershipTimeline(parcelId);
  }, [parcelId]);

  const fetchOwnershipTimeline = async (pid) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/ownership/${pid}`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (err) {
      console.error("Failed to fetch ownership history", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] font-bold uppercase">
              Engine 3 • RULE-STUB
            </span>
            <h2 className="text-xl font-extrabold text-slate-100">Ownership Intelligence & Title Timeline</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Visual transfer history and title pattern flags on suspiciously rapid resale chains (e.g. &gt;3 transfers in &lt;30 days).
          </p>
        </div>

        {/* Parcel Selector Buttons */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Select Parcel:</span>
          {sampleParcels.map((pid) => (
            <button
              key={pid}
              onClick={() => setParcelId(pid)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                parcelId === pid
                  ? 'bg-amber-500 text-slate-950 border-amber-500 font-bold'
                  : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
              }`}
            >
              {pid}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ownership Timeline Visualization */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-6 border border-slate-800">
          <h3 className="text-sm font-bold text-slate-200 mb-6 flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-400" />
            <span>Title Registration & Ownership Chain for {parcelId}</span>
          </h3>

          {loading ? (
            <div className="py-16 text-center text-slate-400">Loading ownership graph...</div>
          ) : data && data.transfers ? (
            <div className="relative pl-6 border-l-2 border-slate-800 space-y-6">
              {data.transfers.map((t, idx) => (
                <div key={idx} className="relative group">
                  {/* Timeline Node Dot */}
                  <div
                    className={`absolute -left-[31px] top-1 w-4 h-4 rounded-full border-2 bg-slate-950 ${
                      t.flag_rapid_resale
                        ? 'border-rose-500 glow-rose'
                        : 'border-emerald-500'
                    }`}
                  ></div>

                  <div className={`p-4 rounded-xl border transition ${
                    t.flag_rapid_resale
                      ? 'bg-rose-500/10 border-rose-500/30'
                      : 'bg-slate-900/60 border-slate-800'
                  }`}>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono text-slate-400">{t.transfer_date}</span>
                      {t.flag_rapid_resale && (
                        <span className="text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">
                          Rapid Resale Flagged
                        </span>
                      )}
                    </div>
                    
                    <div className="mt-2 flex items-center justify-between">
                      <div>
                        <h4 className="text-base font-bold text-slate-100">{t.owner_name}</h4>
                        <p className="text-xs text-slate-400 mt-0.5">{t.transfer_type} • Deed #{t.deed_number}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-slate-400 uppercase">Consideration Amount</span>
                        <p className="text-sm font-extrabold text-amber-300">
                          ₹{(t.price_inr / 100000).toFixed(2)} Lakhs
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        {/* Anomaly Detection & Rule Panel */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-amber-400" />
              <span>Pattern Analysis & Risk Verdict</span>
            </h3>

            {data && (
              <div className="space-y-4">
                <div className={`p-4 rounded-xl border ${
                  data.is_anomalous
                    ? 'bg-rose-500/15 border-rose-500/30 glow-rose'
                    : 'bg-emerald-500/15 border-emerald-500/30 glow-emerald'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-300">Resale Pattern Status</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${data.is_anomalous ? 'bg-rose-500 text-slate-950' : 'bg-emerald-500 text-slate-950'}`}>
                      {data.is_anomalous ? 'ANOMALY FLAGGED' : 'NORMAL'}
                    </span>
                  </div>
                  <div className="text-2xl font-extrabold text-slate-100 mt-2">
                    {data.ownership_risk_score} <span className="text-xs text-slate-400 font-normal">/ 100 Risk Index</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Engine Rule Output</span>
                  {data.explanations && data.explanations.map((exp, i) => (
                    <div key={i} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 leading-relaxed flex items-start gap-2">
                      {data.is_anomalous ? (
                        <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      )}
                      <span>{exp}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-500 font-medium">
            Tagged honestly as <span className="text-amber-400 font-semibold">RULE-STUB</span> in code comments & STATUS.md.
          </div>
        </div>
      </div>
    </div>
  );
}
