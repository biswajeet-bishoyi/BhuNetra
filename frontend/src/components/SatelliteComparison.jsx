import React, { useState, useEffect } from 'react';
import { Satellite, AlertTriangle, CheckCircle, Eye, ShieldAlert, Cpu } from 'lucide-react';

export default function SatelliteComparison({ selectedParcelId = 'P-135' }) {
  const [parcelId, setParcelId] = useState(selectedParcelId);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const sampleParcels = ['P-135', 'P-101', 'P-112'];

  useEffect(() => {
    fetchSatelliteVerification(parcelId);
  }, [parcelId]);

  const fetchSatelliteVerification = async (pid) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/satellite/${pid}`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (err) {
      console.error("Satellite fetch error", err);
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
              Engine 4 • RULE-STUB / MOCK
            </span>
            <h2 className="text-xl font-extrabold text-slate-100">Satellite Land-Use Scene Cross-Check</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Compare registry RoR land-use claims against pre-loaded Sentinel-2 village imagery. Zero live network calls during stage demo.
          </p>
        </div>

        {/* Demo Villages / Parcels Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Demo Parcel:</span>
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

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Precomputed Sentinel-2 Imagery View */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Satellite className="w-4 h-4 text-amber-400" />
              <span>Sentinel-2 L2A Pre-downloaded Village Scene</span>
            </h3>
            <span className="text-[10px] font-mono text-slate-400">Acquired: 2026-06-15</span>
          </div>

          <div className="relative flex-1 min-h-[320px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center p-3">
            <img
              src={data?.preview_image || "/static-data/satellite/rampur_satellite_preview.png"}
              alt="Sentinel-2 Satellite Scene preview"
              className="max-h-[360px] w-full object-cover rounded-lg shadow-2xl"
              onError={(e) => {
                e.target.src = "/static-data/satellite/rampur_satellite_preview.png";
              }}
            />
            <div className="absolute bottom-4 left-4 right-4 glass-panel p-3 rounded-xl border border-slate-700/80 text-xs text-slate-300">
              <span className="text-amber-400 font-bold">NDVI False Color Band (B04, B08)</span>
              <p className="text-[11px] text-slate-400 mt-0.5">High NDVI green = Active crops • High SWIR grey = Concrete built-up structures</p>
            </div>
          </div>
        </div>

        {/* Verification Comparison Card */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-amber-400" />
              <span>Land-Use Classification Verification</span>
            </h3>

            {loading ? (
              <div className="py-16 text-center text-slate-400">Analyzing satellite bands...</div>
            ) : data ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">RoR Registry Claim</span>
                    <p className="font-extrabold text-slate-200 text-base mt-0.5">{data.claimed_use}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">Satellite Scene Detected</span>
                    <p className={`font-extrabold text-base mt-0.5 ${data.mismatch_flag ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {data.satellite_detected_use}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">Vegetation Index (NDVI)</span>
                    <p className="font-bold text-slate-200 mt-0.5">{data.vegetation_ndvi}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">Built-Up Coverage</span>
                    <p className="font-bold text-slate-200 mt-0.5">{data.built_up_coverage_pct}%</p>
                  </div>
                </div>

                {/* Verdict Box */}
                <div className={`p-4 rounded-xl border ${
                  data.mismatch_flag
                    ? 'bg-rose-500/15 border-rose-500/30 glow-rose'
                    : 'bg-emerald-500/15 border-emerald-500/30 glow-emerald'
                }`}>
                  <div className="flex items-start gap-3">
                    {data.mismatch_flag ? (
                      <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                        {data.mismatch_flag ? 'LAND-USE MISMATCH DETECTED' : 'LAND-USE VERIFIED MATCH'}
                      </h4>
                      <p className="text-xs text-slate-300 mt-1 leading-relaxed">{data.explanation}</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-500 font-medium">
            Pre-downloaded Sentinel-2 scene tiles committed to repo; zero live network API calls during demo presentation.
          </div>
        </div>
      </div>
    </div>
  );
}
