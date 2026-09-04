/**
 * BlockchainVisualizer — Audit chain view for a single parcel.
 *
 * Reads the immutable OfficerAuditLog table and renders each audit entry
 * as a block with prev_hash → hash linkage. The first/last 8 chars of the
 * hash are shown by default; clicking a block reveals the full hash.
 */
import React, { useState, useEffect } from 'react';
import { X, Hash, Link2, CheckCircle2, Clock, User, FileText, ShieldCheck, Loader2, ShieldAlert } from 'lucide-react';

const ACTION_TONES = {
  APPROVE: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  OVERRIDE: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  REJECT: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
  COURT_STATUS_UPDATE: 'bg-sky-500/20 text-sky-300 border-sky-500/30',
};

const truncate = (hash, prefix = 0) => {
  if (!hash) return '—';
  if (hash.length <= prefix * 2 + 6) return hash;
  return `${hash.slice(0, prefix)}…${hash.slice(-prefix)}`;
};

export default function BlockchainVisualizer({ parcelId, isOpen, onClose, onSelectParcel }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(null);
  const [verifyResult, setVerifyResult] = useState(null);

  useEffect(() => {
    if (isOpen && parcelId) {
      loadLogs();
      loadVerify();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, parcelId]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/review-queue/audit-log');
      if (res.ok) {
        const all = await res.json();
        setLogs(all.filter((l) => l.parcel_id === parcelId));
      }
    } catch (err) {
      console.error('Failed to load audit log', err);
    } finally {
      setLoading(false);
    }
  };

  const loadVerify = async () => {
    try {
      const res = await fetch(`/api/blockchain/verify-hash/${parcelId}`);
      if (res.ok) {
        setVerifyResult(await res.json());
      }
    } catch (err) {
      console.error('Failed to verify hash', err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-3xl glass-panel rounded-2xl border border-slate-700/80 shadow-2xl p-6 bg-slate-900/95 text-slate-100 my-8">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Link2 className="w-5 h-5 text-amber-400" />
            <div>
              <h3 className="text-sm font-bold text-slate-100">Blockchain Audit Chain</h3>
              <p className="text-[10px] text-slate-400 font-mono">Parcel {parcelId} · {logs.length} block{logs.length !== 1 ? 's' : ''}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Verification status banner */}
        {verifyResult && (
          <div className={`mt-4 p-3 rounded-xl border ${
            verifyResult.on_chain_status === 'VERIFIED_IMMUTABLE'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          }`}>
            <div className="flex items-center gap-2 text-xs font-bold">
              {verifyResult.on_chain_status === 'VERIFIED_IMMUTABLE'
                ? <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                : <ShieldAlert className="w-4 h-4 text-amber-400" />}
              <span>{verifyResult.on_chain_status === 'VERIFIED_IMMUTABLE' ? 'On-Chain Status: VERIFIED IMMUTABLE' : verifyResult.on_chain_status}</span>
            </div>
            {verifyResult.approval_hash && (
              <p className="text-[10px] text-slate-300 font-mono mt-1 break-all">Latest hash: {verifyResult.approval_hash}</p>
            )}
            {verifyResult.legal_disclaimer && (
              <p className="text-[10px] text-slate-400 mt-1">{verifyResult.legal_disclaimer}</p>
            )}
          </div>
        )}

        {/* Chain */}
        <div className="mt-4 space-y-3 max-h-[60vh] overflow-y-auto pr-1">
          {loading ? (
            <div className="py-12 text-center text-slate-400 text-sm flex flex-col items-center gap-2">
              <Loader2 className="w-6 h-6 text-amber-400 animate-spin" />
              <span>Loading audit chain…</span>
            </div>
          ) : logs.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-sm">
              <Hash className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p>No officer decisions recorded for this parcel yet.</p>
            </div>
          ) : (
            logs.map((log, idx) => {
              const tone = ACTION_TONES[log.action] || 'bg-slate-700/40 text-slate-300 border-slate-700';
              const isOpen = expanded === log.id;
              return (
                <div key={log.id} className="relative">
                  {/* Connecting arrow */}
                  {idx < logs.length - 1 && (
                    <div className="absolute left-7 -bottom-3 w-0.5 h-3 bg-amber-500/40 z-0" />
                  )}
                  <button
                    onClick={() => setExpanded(isOpen ? null : log.id)}
                    className="w-full text-left p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/30 transition space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-300 font-extrabold text-xs">
                          #{log.id}
                        </div>
                        <div>
                          <p className="text-xs font-bold text-slate-100">Block #{log.id} · {log.action}</p>
                          <p className="text-[10px] text-slate-400 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {log.timestamp}
                          </p>
                        </div>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${tone}`}>{log.action}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-400 pt-1">
                      <div className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        <span className="truncate">{log.officer_name}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Hash className="w-3 h-3" />
                        <span className="font-mono text-amber-300 truncate">{truncate(log.blockchain_hash, 8)}</span>
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-300 leading-relaxed line-clamp-2">"{log.reason}"</p>

                    {isOpen && (
                      <div className="mt-2 p-2 rounded bg-slate-950 border border-slate-800 space-y-1.5">
                        <p className="text-[10px] text-slate-500 uppercase font-bold">Full Hash</p>
                        <p className="font-mono text-[10px] text-amber-300 break-all">{log.blockchain_hash}</p>
                        {log.legal_note && (
                          <p className="text-[10px] text-slate-400 mt-1.5 italic">{log.legal_note}</p>
                        )}
                      </div>
                    )}
                  </button>
                </div>
              );
            })
          )}
        </div>

        <div className="mt-4 pt-3 border-t border-slate-800 text-[10px] text-slate-500 text-center">
          Hashes are SHA-256 over (parcel, action, officer, reason, timestamp). Compliance: IT Act 2000 Sec 65B · Registration Act 1908.
        </div>
      </div>
    </div>
  );
}
