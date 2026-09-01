import React, { useState, useEffect } from 'react';
import { Scale, CheckCircle2, AlertTriangle, FileText, Save, RefreshCw } from 'lucide-react';

export default function RevenueCourtManager({ parcelsData, onRefresh }) {
  const [selectedPid, setSelectedPid] = useState('P-105');
  const [courtStatus, setCourtStatus] = useState('Court Case');
  const [caseRef, setCaseRef] = useState('CC-2026-PAT-9081');
  const [updating, setUpdating] = useState(false);

  const [allParcels, setAllParcels] = useState([]);
  const [loadingParcels, setLoadingParcels] = useState(true);

  // Load every parcel from /api/gis-check/ on mount so the dropdown
  // reflects the full registry rather than a hard-coded list.
  useEffect(() => {
    let cancelled = false;
    const fetchAll = async () => {
      setLoadingParcels(true);
      try {
        const res = await fetch('/api/gis-check/');
        if (res.ok) {
          const json = await res.json();
          if (!cancelled && json?.features) {
            const ids = json.features
              .map((f) => f?.properties?.parcel_id)
              .filter(Boolean);
            setAllParcels(ids);
            if (ids.length && !ids.includes(selectedPid)) {
              setSelectedPid(ids[0]);
            }
          }
        }
      } catch (err) {
        console.error('Failed to load parcel list for Revenue Court dropdown', err);
      } finally {
        if (!cancelled) setLoadingParcels(false);
      }
    };
    fetchAll();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Prefer the live list; fall back to a small default set if the API is offline.
  const sampleParcels = allParcels.length > 0
    ? allParcels
    : ['P-105', 'P-118', 'P-112', 'P-101'];

  const handleUpdate = async () => {
    setUpdating(true);
    try {
      const res = await fetch('/api/revenue-court/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parcel_id: selectedPid,
          court_status: courtStatus,
          case_reference_no: caseRef,
          updated_by: 'Revenue Officer Rampur'
        })
      });

      if (res.ok) {
        alert(`Revenue Court status for parcel ${selectedPid} updated to '${courtStatus}'!`);
        if (onRefresh) onRefresh();
      }
    } catch (err) {
      console.error("Revenue Court update error", err);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header Banner */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] font-bold uppercase">
              P1 • REAL (Simple CRUD)
            </span>
            <h2 className="text-xl font-extrabold text-slate-100">Revenue Court Status Management</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Maintain legal litigation state (Clean / Stay Order / Mutation Pending / Court Case). Visible before any transaction proceeds.
          </p>
        </div>

        <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <Scale className="w-6 h-6" />
        </div>
      </div>

      {/* Main Form Box */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
        <h3 className="text-sm font-bold text-slate-200 border-b border-slate-800 pb-3 flex items-center gap-2">
          <Scale className="w-4 h-4 text-amber-400" />
          <span>Edit Litigation State for Parcel</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">Select Target Parcel:</label>
            <select
              value={selectedPid}
              onChange={(e) => setSelectedPid(e.target.value)}
              disabled={loadingParcels}
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:border-amber-500 focus:outline-none disabled:opacity-60"
            >
              {loadingParcels && <option value="">Loading parcels…</option>}
              {!loadingParcels && sampleParcels.map((pid) => (
                <option key={pid} value={pid}>Parcel {pid}</option>
              ))}
            </select>
            {!loadingParcels && (
              <p className="text-[10px] text-slate-500 mt-1.5 flex items-center gap-1">
                <RefreshCw className="w-3 h-3" />
                {sampleParcels.length} parcels loaded from /api/gis-check/
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">Revenue Court Status Field:</label>
            <select
              value={courtStatus}
              onChange={(e) => setCourtStatus(e.target.value)}
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-amber-300 font-bold focus:border-amber-500 focus:outline-none"
            >
              <option value="Clean">Clean (No Litigation)</option>
              <option value="Stay Order">Stay Order (Court Injunction Active)</option>
              <option value="Mutation Pending">Mutation Pending (Objection Period)</option>
              <option value="Court Case">Court Case (Sub-Judice Dispute)</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs font-bold text-slate-300 mb-1.5">Case Reference Number / Court Order File:</label>
            <input
              type="text"
              value={caseRef}
              onChange={(e) => setCaseRef(e.target.value)}
              placeholder="e.g. CC-2026-PAT-9081 (District Collector Court Patna)"
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:border-amber-500 focus:outline-none"
            />
          </div>
        </div>

        <button
          onClick={handleUpdate}
          disabled={updating}
          className="w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition flex items-center justify-center gap-2"
        >
          <Save className="w-4 h-4 text-slate-950" />
          <span>{updating ? 'Saving Status...' : 'Save & Publish Revenue Court Status'}</span>
        </button>
      </div>
    </div>
  );
}
