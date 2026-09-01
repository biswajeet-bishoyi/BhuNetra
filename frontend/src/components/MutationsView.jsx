/**
 * MutationsView.jsx — Officer mutation request workspace.
 *
 * Officers can draw a new polygon on the cadastral map and submit it
 * as a pending mutation request. The request is stored in the
 * `mutation_requests` table and queued for Tahsildar review/approval.
 *
 * Pure Leaflet drawing (no leaflet-draw dependency): click points on
 * the map, then "Finish polygon" or "Cancel" to reset. Once finished
 * the polygon is rendered and can be submitted.
 */
import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, Polygon, Marker, Tooltip, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { Layers, Trash2, CheckCircle, MapPin, X, FileText, Loader2, Send, AlertCircle } from 'lucide-react';

const SHAMSHABAD_CENTER = [17.258, 78.434];

function ClickCapture({ enabled, points, onAddPoint, onFinish }) {
  useMapEvents({
    click(e) {
      if (!enabled) return;
      const { lat, lng } = e.latlng;
      onAddPoint([lat, lng]);
    },
    dblclick() {
      if (!enabled) return;
      onFinish();
    },
  });
  return null;
}

function FlyToSelection({ target }) {
  const map = useMap();
  useEffect(() => {
    if (target && target.length === 2) {
      map.flyTo(target, 16, { duration: 0.7 });
    }
  }, [target, map]);
  return null;
}

const STATUS_COLORS = {
  PENDING: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  APPROVED: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  REJECTED: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
};

function parcelStyle(feature) {
  const pid = feature.properties.parcel_id;
  const anomalous = feature.properties.is_anomalous;
  let color = '#10b981';
  let fillOpacity = 0.25;
  if (anomalous || pid === 'P-105' || pid === 'P-108' || pid === 'P-135') {
    color = '#f43f5e';
    fillOpacity = 0.45;
  } else if (pid === 'P-112' || pid === 'P-118') {
    color = '#f59e0b';
    fillOpacity = 0.35;
  }
  return { color, weight: 1.5, fillColor: color, fillOpacity };
}

export default function MutationsView({ parcelsData, currentUser, onSelectParcel }) {
  const [parcels, setParcels] = useState(parcelsData);
  const [drawMode, setDrawMode] = useState(false);
  const [points, setPoints] = useState([]);
  const [parcelId, setParcelId] = useState('');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [requests, setRequests] = useState([]);
  const [loadingRequests, setLoadingRequests] = useState(true);
  const [reviewing, setReviewing] = useState(null);
  const [reviewNotes, setReviewNotes] = useState('');

  // Reload parcels if not provided
  useEffect(() => {
    if (!parcels) {
      fetch('/api/gis-check/')
        .then(r => r.json())
        .then(d => setParcels(d))
        .catch(() => setParcels({ features: [] }));
    }
  }, [parcels]);

  // Load mutation requests
  useEffect(() => {
    loadRequests();
  }, []);

  const loadRequests = async () => {
    setLoadingRequests(true);
    try {
      const r = await fetch('/api/mutations/');
      if (r.ok) {
        const d = await r.json();
        setRequests(d.requests || []);
      }
    } catch {
      setRequests([]);
    } finally {
      setLoadingRequests(false);
    }
  };

  const handleAddPoint = (p) => {
    setPoints(prev => [...prev, p]);
    setError('');
  };

  const handleUndo = () => setPoints(prev => prev.slice(0, -1));

  const handleCancel = () => {
    setPoints([]);
    setDrawMode(false);
    setError('');
  };

  const handleFinish = () => {
    if (points.length < 3) {
      setError('Need at least 3 points to form a polygon.');
      return;
    }
    setDrawMode(false);
  };

  const canSubmit = !submitting && points.length >= 3 && reason.trim().length >= 5;

  const buildGeoJSON = () => {
    const ring = [...points, points[0]].map(([lat, lng]) => [lng, lat]);
    return {
      type: 'Polygon',
      coordinates: [ring],
    };
  };

  const handleSubmit = async () => {
    if (points.length < 3) {
      setError('Need at least 3 points to form a polygon.');
      return;
    }
    if (reason.trim().length < 5) {
      setError('Reason must be at least 5 characters (Sec 65B audit trail).');
      return;
    }
    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      const r = await fetch('/api/mutations/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parcel_id: parcelId.trim() || null,
          requested_by: currentUser?.name || 'Revenue Officer',
          reason: reason.trim(),
          geometry: buildGeoJSON(),
        }),
      });
      if (!r.ok) {
        const t = await r.text();
        throw new Error(t || 'Failed to submit mutation request');
      }
      const d = await r.json();
      setSuccess(`Mutation request #${d.mutation_id} submitted and queued for review.`);
      setPoints([]);
      setParcelId('');
      setReason('');
      await loadRequests();
    } catch (e) {
      setError(e.message || 'Submission failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReview = async (mutationId, action) => {
    if (reviewNotes.trim().length < 3 && action === 'REJECT') {
      setError('Rejection reason required (min 3 chars).');
      return;
    }
    setError('');
    try {
      const r = await fetch(`/api/mutations/${mutationId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action,
          reviewed_by: currentUser?.name || 'Tahsildar / Revenue Officer',
          notes: reviewNotes.trim(),
        }),
      });
      if (!r.ok) {
        const t = await r.text();
        throw new Error(t || 'Review failed');
      }
      setReviewing(null);
      setReviewNotes('');
      await loadRequests();
    } catch (e) {
      setError(e.message || 'Review failed.');
    }
  };

  const pendingCount = requests.filter(r => r.status === 'PENDING').length;
  const approvedCount = requests.filter(r => r.status === 'APPROVED').length;

  return (
    <div className="space-y-4">
      {/* Header card */}
      <div className="glass-panel rounded-2xl border border-slate-800 p-5">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-amber-400" />
              Parcel Mutation Workspace
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Draw a new boundary on the cadastral map and submit a mutation request. The proposed
              geometry is stored in the registry and queued for Tahsildar approval before any
              existing record is updated.
            </p>
          </div>
          <div className="flex items-center gap-2 text-[11px] font-bold">
            <span className="px-2 py-1 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-300">
              {pendingCount} PENDING
            </span>
            <span className="px-2 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300">
              {approvedCount} APPROVED
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Map */}
        <div className="lg:col-span-2 glass-panel rounded-2xl border border-slate-800 overflow-hidden relative">
          <div className="absolute top-3 left-3 z-[1000] glass-panel px-3 py-2 rounded-lg border border-slate-700/80 bg-slate-900/95 text-xs">
            <div className="flex items-center gap-2">
              <MapPin className="w-3.5 h-3.5 text-amber-400" />
              <span className="font-bold text-slate-100">
                {drawMode ? 'Drawing mode — click map to add points, double-click to finish' : 'Click "Start Drawing" to begin'}
              </span>
            </div>
            {points.length > 0 && (
              <p className="text-[10px] text-slate-400 mt-1">{points.length} point{points.length === 1 ? '' : 's'} placed</p>
            )}
          </div>

          <div className="absolute top-3 right-3 z-[1000] flex items-center gap-1.5">
            {!drawMode ? (
              <button
                onClick={() => setDrawMode(true)}
                className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold flex items-center gap-1.5 shadow-md cursor-pointer"
              >
                <Layers className="w-3.5 h-3.5" />
                Start Drawing
              </button>
            ) : (
              <>
                <button
                  onClick={handleUndo}
                  disabled={points.length === 0}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 disabled:opacity-40 cursor-pointer"
                >
                  Undo
                </button>
                <button
                  onClick={handleFinish}
                  disabled={points.length < 3}
                  className="px-2.5 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold disabled:opacity-40 cursor-pointer"
                >
                  Finish ({points.length})
                </button>
                <button
                  onClick={handleCancel}
                  className="px-2.5 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 text-xs font-semibold border border-rose-500/30 cursor-pointer"
                >
                  Cancel
                </button>
              </>
            )}
          </div>

          <div className="h-[480px]">
            <MapContainer
              center={SHAMSHABAD_CENTER}
              zoom={14}
              style={{ height: '100%', width: '100%' }}
              doubleClickZoom={!drawMode}
            >
              <TileLayer
                attribution='© OpenStreetMap'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {parcels?.features && (
                <GeoJSON
                  key="parcels-base"
                  data={parcels}
                  style={parcelStyle}
                  onEachFeature={(feature, layer) => {
                    const p = feature.properties;
                    layer.bindTooltip(
                      `<b>${p.parcel_id}</b> · ${p.village} · Survey ${p.survey_no}`,
                      { sticky: true }
                    );
                  }}
                />
              )}
              {points.length > 0 && (
                <>
                  {points.map((p, i) => (
                    <Marker key={`pt-${i}`} position={p}>
                      <Tooltip permanent direction="top" offset={[0, -8]}>
                        <span className="text-[10px]">{i + 1}</span>
                      </Tooltip>
                    </Marker>
                  ))}
                  {points.length >= 3 && (
                    <Polygon
                      positions={points}
                      pathOptions={{ color: '#f59e0b', weight: 2.5, fillColor: '#f59e0b', fillOpacity: 0.25 }}
                    />
                  )}
                </>
              )}
              <ClickCapture enabled={drawMode} points={points} onAddPoint={handleAddPoint} onFinish={handleFinish} />
            </MapContainer>
          </div>
        </div>

        {/* Submission form */}
        <div className="glass-panel rounded-2xl border border-slate-800 p-5 space-y-3">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Send className="w-4 h-4 text-amber-400" />
            Submit Request
          </h3>

          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Target Parcel (optional)
            </label>
            <input
              type="text"
              value={parcelId}
              onChange={e => setParcelId(e.target.value)}
              placeholder="e.g. P-105 (blank for new boundary)"
              className="mt-1 w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Reason (min 5 chars)
            </label>
            <textarea
              value={reason}
              onChange={e => setReason(e.target.value)}
              rows={3}
              placeholder="e.g. Boundary re-survey after sub-division of agricultural plot..."
              className="mt-1 w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          <div className="text-[10px] text-slate-400 bg-slate-900/60 border border-slate-800 rounded-lg p-2.5">
            <p className="font-semibold text-slate-300">Points placed: {points.length}</p>
            {points.length < 3 ? (
              <p className="mt-0.5">Need at least 3 points to form a polygon.</p>
            ) : (
              <p className="mt-0.5 text-emerald-400">Polygon ready for submission.</p>
            )}
          </div>

          {error && (
            <div className="text-[11px] text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-lg p-2.5 flex items-start gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {success && (
            <div className="text-[11px] text-emerald-300 bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-2.5 flex items-start gap-1.5">
              <CheckCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              <span>{success}</span>
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="w-full px-3 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed text-slate-950 text-xs font-bold flex items-center justify-center gap-1.5 cursor-pointer"
          >
            {submitting ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Submitting…
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                Submit Mutation Request
              </>
            )}
          </button>

          <p className="text-[10px] text-slate-500 leading-relaxed">
            Recorded under IT Act 2000 Sec 65B audit trail. Does not amend the existing record
            until the Tahsildar approves.
          </p>
        </div>
      </div>

      {/* Request queue */}
      <div className="glass-panel rounded-2xl border border-slate-800 p-5">
        <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2 mb-3">
          <FileText className="w-4 h-4 text-amber-400" />
          Mutation Request Queue
        </h3>

        {loadingRequests ? (
          <div className="text-xs text-slate-400 text-center py-6 flex items-center justify-center gap-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Loading requests…
          </div>
        ) : requests.length === 0 ? (
          <div className="text-xs text-slate-400 text-center py-6">
            No mutation requests yet. Draw a polygon above to submit the first one.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <th className="text-left py-2 px-2">ID</th>
                  <th className="text-left py-2 px-2">Parcel</th>
                  <th className="text-left py-2 px-2">Requested By</th>
                  <th className="text-left py-2 px-2">Reason</th>
                  <th className="text-left py-2 px-2">Status</th>
                  <th className="text-left py-2 px-2">Created</th>
                  <th className="text-left py-2 px-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {requests.map(r => (
                  <React.Fragment key={r.id}>
                    <tr className="border-b border-slate-800/60 hover:bg-slate-900/40">
                      <td className="py-2 px-2 font-bold text-amber-300">#{r.id}</td>
                      <td className="py-2 px-2 text-slate-200">{r.parcel_id || '—'}</td>
                      <td className="py-2 px-2 text-slate-300">{r.requested_by}</td>
                      <td className="py-2 px-2 text-slate-300 max-w-[280px] truncate" title={r.reason}>
                        {r.reason}
                      </td>
                      <td className="py-2 px-2">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${STATUS_COLORS[r.status] || 'bg-slate-700/40 text-slate-300 border-slate-600/30'}`}>
                          {r.status}
                        </span>
                      </td>
                      <td className="py-2 px-2 text-[10px] text-slate-400">
                        {r.created_at ? new Date(r.created_at).toLocaleString() : '—'}
                      </td>
                      <td className="py-2 px-2">
                        {r.status === 'PENDING' ? (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => setReviewing(r.id === reviewing ? null : r.id)}
                              className="px-2 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-semibold border border-slate-700 cursor-pointer"
                            >
                              {reviewing === r.id ? 'Close' : 'Review'}
                            </button>
                          </div>
                        ) : (
                          <span className="text-[10px] text-slate-500">
                            {r.reviewed_by ? `by ${r.reviewed_by}` : '—'}
                          </span>
                        )}
                      </td>
                    </tr>
                    {reviewing === r.id && (
                      <tr className="bg-slate-900/60">
                        <td colSpan={7} className="px-3 py-3">
                          <div className="space-y-2">
                            <textarea
                              value={reviewNotes}
                              onChange={e => setReviewNotes(e.target.value)}
                              rows={2}
                              placeholder="Review notes (required for rejection)…"
                              className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-amber-500"
                            />
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleReview(r.id, 'APPROVE')}
                                className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-[11px] font-bold cursor-pointer"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => handleReview(r.id, 'REJECT')}
                                className="px-3 py-1.5 rounded-lg bg-rose-500/80 hover:bg-rose-500 text-white text-[11px] font-bold cursor-pointer"
                              >
                                Reject
                              </button>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
