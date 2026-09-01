/**
 * DocumentsView — Lists every document in the lifecycle database.
 *
 * The OCR Scanner uploads go straight into the document lifecycle, so this
 * view gives officers a way to see everything that has been registered,
 * its current state, and the SHA-256 hash for approved documents.
 */
import React, { useState, useEffect } from 'react';
import { FileText, CheckCircle2, AlertTriangle, XCircle, RefreshCw, Hash, Clock, Upload } from 'lucide-react';

const STATUS_TONES = {
  UPLOADED: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
  EXTRACTED: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  NEEDS_REVIEW: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  VERIFIED: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
  APPROVED: 'bg-emerald-500/25 text-emerald-300 border-emerald-500/50',
  REJECTED: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
};

const STATUS_ICONS = {
  UPLOADED: Upload,
  EXTRACTED: CheckCircle2,
  NEEDS_REVIEW: AlertTriangle,
  VERIFIED: CheckCircle2,
  APPROVED: CheckCircle2,
  REJECTED: XCircle,
};

export default function DocumentsView({ onSelectParcel }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('ALL');

  const loadDocs = async () => {
    setLoading(true);
    try {
      const url = filter === 'ALL' ? '/api/documents/?limit=100' : `/api/documents/?status=${filter}&limit=100`;
      const res = await fetch(url);
      if (res.ok) {
        const json = await res.json();
        setDocs(json.documents || []);
      }
    } catch (err) {
      console.error('Failed to load documents', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] font-bold uppercase">
              P3 • Document Lifecycle
            </span>
            <h2 className="text-xl font-extrabold text-slate-100">Document Lifecycle Registry</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Every scanned deed passes through UPLOADED → EXTRACTED → VERIFIED → APPROVED. Approved documents receive a SHA-256 hash under IT Act 2000 Sec 65B.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-200 focus:border-amber-500 focus:outline-none"
          >
            <option value="ALL">All Documents</option>
            <option value="UPLOADED">Uploaded</option>
            <option value="EXTRACTED">Extracted</option>
            <option value="NEEDS_REVIEW">Needs Review</option>
            <option value="VERIFIED">Verified</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
          </select>
          <button
            onClick={loadDocs}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* List */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800">
        {loading ? (
          <div className="py-12 text-center text-slate-400 text-sm">Loading documents…</div>
        ) : docs.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-sm">
            <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p>No documents in the registry yet. Upload a scan via the OCR tab to begin the lifecycle.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {docs.map((doc) => {
              const StatusIcon = STATUS_ICONS[doc.status] || FileText;
              const tone = STATUS_TONES[doc.status] || 'bg-slate-700/30 text-slate-300 border-slate-700';
              return (
                <div key={doc.id} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/30 transition flex items-start gap-3">
                  <StatusIcon className={`w-4 h-4 mt-1 shrink-0 ${
                    doc.status === 'APPROVED' ? 'text-emerald-400' :
                    doc.status === 'NEEDS_REVIEW' ? 'text-amber-400' :
                    doc.status === 'REJECTED' ? 'text-rose-400' : 'text-sky-400'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="font-bold text-amber-300 text-sm">Doc #{doc.id}</span>
                        <span className="text-xs text-slate-300 truncate">{doc.source_filename}</span>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${tone}`}>{doc.status}</span>
                    </div>
                    <div className="mt-1.5 grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px] text-slate-400">
                      <div>
                        <span className="text-slate-500">Confidence</span>
                        <p className="font-bold text-slate-200">{((doc.extraction_confidence || 0) * 100).toFixed(0)}%</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Engine</span>
                        <p className="font-bold text-slate-200">{doc.extraction_engine_tag || '—'}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Low-conf fields</span>
                        <p className="font-bold text-slate-200">{(doc.low_confidence_fields || []).length}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Uploaded</span>
                        <p className="font-bold text-slate-200 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {doc.upload_timestamp ? new Date(doc.upload_timestamp).toLocaleString() : '—'}
                        </p>
                      </div>
                    </div>
                    {doc.blockchain_hash && (
                      <div className="mt-2 p-2 rounded bg-slate-950 border border-amber-500/20 flex items-center gap-2 text-[10px]">
                        <Hash className="w-3 h-3 text-amber-400 shrink-0" />
                        <span className="font-mono text-amber-300 break-all">{doc.blockchain_hash}</span>
                      </div>
                    )}
                    {doc.parcel_id_hint && onSelectParcel && (
                      <button
                        onClick={() => onSelectParcel(doc.parcel_id_hint)}
                        className="mt-2 text-[10px] text-amber-300 hover:text-amber-200 font-semibold"
                      >
                        Cross-verify parcel {doc.parcel_id_hint} →
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
