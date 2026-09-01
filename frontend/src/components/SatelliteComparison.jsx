import React, { useState, useEffect, useRef } from 'react';
import { Satellite, AlertTriangle, CheckCircle, Eye, ShieldAlert, Cpu, Sliders, Layers } from 'lucide-react';

export default function SatelliteComparison({ selectedParcelId = 'P-135', selectedRole = 'Revenue Officer' }) {
  const [parcelId, setParcelId] = useState(selectedParcelId);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sliderPos, setSliderPos] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  const sampleParcels = ['P-135', 'P-101', 'P-112'];

  useEffect(() => {
    fetchSatelliteVerification(parcelId, selectedRole);
  }, [parcelId, selectedRole]);

  const fetchSatelliteVerification = async (pid, role) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/satellite/${pid}?role=${encodeURIComponent(role || 'Revenue Officer')}`);
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

  const handleMove = (clientX) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPos(percentage);
  };

  const handleTouchMove = (e) => {
    if (!isDragging) return;
    handleMove(e.touches[0].clientX);
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    handleMove(e.clientX);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] font-bold uppercase">
              Engine 4 • Interactive Temporal Swipe
            </span>
            <h2 className="text-xl font-extrabold text-slate-100">Satellite Land-Use Scene Cross-Check</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Interactive temporal slider comparing registered RoR baseline vs current Sentinel-2 multispectral scene.
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
        {/* Interactive Before / After Swipe Curtain View */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Layers className="w-4 h-4 text-amber-400" />
              <span>Interactive Temporal Swipe Curtain</span>
            </h3>
            <span className="text-[10px] font-mono text-amber-400">Drag Slider to Compare</span>
          </div>

          <div
            ref={containerRef}
            onMouseDown={() => setIsDragging(true)}
            onMouseUp={() => setIsDragging(false)}
            onMouseLeave={() => setIsDragging(false)}
            onMouseMove={handleMouseMove}
            onTouchStart={() => setIsDragging(true)}
            onTouchEnd={() => setIsDragging(false)}
            onTouchMove={handleTouchMove}
            className="relative flex-1 min-h-[340px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800 select-none cursor-ew-resize"
          >
            {/* Background Layer: 2026 Sentinel-2 Verification Scene */}
            <div className="absolute inset-0 flex flex-col items-center justify-center p-3">
              <img
                src={data?.preview_image || "/static-data/satellite/rampur_satellite_preview.png"}
                alt="2026 Sentinel-2 Satellite Scene"
                className="w-full h-full object-cover rounded-lg"
                onError={(e) => {
                  e.target.src = "/static-data/satellite/rampur_satellite_preview.png";
                }}
              />
              <div className="absolute top-4 right-4 px-2.5 py-1 rounded bg-rose-500/80 text-white text-[10px] font-bold backdrop-blur-md shadow-md">
                2026 Sentinel-2 (Commercial Structure)
              </div>
            </div>

            {/* Foreground Clipped Layer: 2021 Agricultural Farmland Scene */}
            <div
              className="absolute inset-0 overflow-hidden"
              style={{ clipPath: `polygon(0 0, ${sliderPos}% 0, ${sliderPos}% 100%, 0 100%)` }}
            >
              <div className="w-full h-full flex flex-col items-center justify-center p-3 bg-emerald-950/40">
                <img
                  src="/static-data/satellite/rampur_satellite_preview.png"
                  alt="2021 Baseline Agricultural Scene"
                  className="w-full h-full object-cover rounded-lg filter hue-rotate-60 brightness-90"
                  onError={(e) => {
                    e.target.src = "/static-data/satellite/rampur_satellite_preview.png";
                  }}
                />
                <div className="absolute top-4 left-4 px-2.5 py-1 rounded bg-emerald-600/90 text-white text-[10px] font-bold backdrop-blur-md shadow-md">
                  2021 Dharani Baseline (Farmland / NDVI 0.74)
                </div>
              </div>
            </div>

            {/* Draggable Divider Line */}
            <div
              className="absolute top-0 bottom-0 w-1 bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.8)] pointer-events-none"
              style={{ left: `${sliderPos}%` }}
            >
              <div className="absolute top-1/2 -translate-y-1/2 -left-3.5 w-8 h-8 rounded-full bg-amber-500 border-2 border-slate-950 flex items-center justify-center text-slate-950 shadow-xl">
                <Sliders className="w-3.5 h-3.5 rotate-90" />
              </div>
            </div>

            <div className="absolute bottom-3 left-3 right-3 glass-panel p-2 rounded-lg border border-slate-700/80 text-[10px] text-slate-300 flex justify-between">
              <span>← Farmland Claim (Dharani RoR)</span>
              <span>Observed Warehouse (Sentinel-2) →</span>
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
