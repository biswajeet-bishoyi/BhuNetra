import React, { useState, useEffect } from 'react';
import { ShieldCheck, CheckCircle2, XCircle, AlertCircle, Scale, FileText, Lock, RefreshCw, Send, ShieldAlert, FileCheck } from 'lucide-react';

export default function OfficerReviewQueue({ onSelectParcel, selectedRole }) {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [decisionAction, setDecisionAction] = useState('APPROVE');
  const [typedReason, setTypedReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [complianceInfo, setComplianceInfo] = useState(null);

  useEffect(() => {
    fetchReviewQueue();
  }, [selectedRole]);

  const fetchReviewQueue = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/review-queue/?role=${encodeURIComponent(selectedRole || 'Revenue Officer')}`);
      if (res.ok) {
        const json = await res.json();
        setQueue(json.queue);
        setComplianceInfo(json.compliance_context);
      }
    } catch (err) {
      console.error("Queue fetch error", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitDecision = async () => {
    if (!selectedItem || !typedReason || typedReason.trim().length < 5) {
      alert("Mandatory typed reason (at least 5 characters) required for officer decision audit trail.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch('/api/review-queue/decision', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parcel_id: selectedItem.parcel_id,
          officer_name: 'Tahsildar / Revenue Officer Shamshabad',
          action: decisionAction,
          reason: typedReason
        })
      });

      if (res.ok) {
        const json = await res.json();
        alert(`Decision '${decisionAction}' logged for ${selectedItem.parcel_id}!\n\nBlockchain Hash (IT Act Sec 65B): ${json.blockchain_hash}\n\nNote: ${json.statutory_boundary}`);
        setSelectedItem(null);
        setTypedReason('');
        fetchReviewQueue();
      }
    } catch (err) {
      console.error("Failed to submit decision", err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold uppercase">
              P0 Mandatory • REAL
            </span>
            <h2 className="text-xl font-extrabold text-slate-100">Revenue Officer Review Queue & Audit Trail</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Human-in-the-loop decision console. No record is ever auto-rejected; overrides require accountable typed reasons and generate immutable SHA-256 approval hashes.
          </p>
        </div>

        <button
          onClick={fetchReviewQueue}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Compliance Grounding Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start gap-2.5">
          <Lock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <div className="font-bold text-slate-200">DPDP Act 2023 Compliance</div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {selectedRole === 'Citizen' ? 'Active: PII is masked for citizen public view.' : 'Officer Mode: Full unmasked records accessible with audit logging.'}
            </p>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start gap-2.5">
          <FileCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <div className="font-bold text-slate-200">IT Act 2000 Section 65B</div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Cryptographic hashes & timestamps generated for court-admissible electronic records.
            </p>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-start gap-2.5">
          <Scale className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <div className="font-bold text-slate-200">Registration Act 1908 Scope</div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Blockchain hashes verify audit integrity; statutory title remains with the registered deed.
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid: Queue Table & Decision Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Queue Table */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col">
          <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            <span>Flagged Parcels Awaiting Revenue Officer Decision ({queue.length} Total)</span>
          </h3>

          {loading ? (
            <div className="py-16 text-center text-slate-400">Fetching review queue...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    <th className="pb-3 px-2">Parcel ID</th>
                    <th className="pb-3 px-2">Owner / Village</th>
                    <th className="pb-3 px-2">Risk Level</th>
                    <th className="pb-3 px-2">Court Status</th>
                    <th className="pb-3 px-2">Decision State</th>
                    <th className="pb-3 px-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-xs">
                  {queue.map((item) => (
                    <tr
                      key={item.parcel_id}
                      className={`hover:bg-slate-800/40 transition cursor-pointer ${
                        selectedItem?.parcel_id === item.parcel_id ? 'bg-slate-800/60' : ''
                      }`}
                      onClick={() => setSelectedItem(item)}
                    >
                      <td className="py-3 px-2 font-extrabold text-amber-300">{item.parcel_id}</td>
                      <td className="py-3 px-2">
                        <div className="font-semibold text-slate-200">{item.owner_name}</div>
                        <div className="text-[10px] text-slate-400">{item.village}, {item.mandal || 'Shamshabad'}</div>
                      </td>
                      <td className="py-3 px-2">
                        <span
                          className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                            item.ensemble_risk_level === 'RED'
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : item.ensemble_risk_level === 'YELLOW'
                              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                              : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          }`}
                        >
                          {item.ensemble_risk_level} ({item.ensemble_risk_score})
                        </span>
                      </td>
                      <td className="py-3 px-2 font-semibold text-slate-300">{item.revenue_court_status}</td>
                      <td className="py-3 px-2">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          item.review_status === 'APPROVED' || item.review_status === 'OVERRIDE'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-amber-500/20 text-amber-400'
                        }`}>
                          {item.review_status}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-right">
                        <button
                          onClick={(e) => { e.stopPropagation(); setSelectedItem(item); }}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-amber-500 hover:text-slate-950 text-slate-300 text-[11px] font-bold transition"
                        >
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Decision & Audit Log Form */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col justify-between">
          {selectedItem ? (
            <div className="space-y-4">
              <div>
                <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">Officer Verification Desk</span>
                <h3 className="text-lg font-extrabold text-slate-100 mt-0.5">Review Parcel {selectedItem.parcel_id}</h3>
                <p className="text-xs text-slate-400">Owner: {selectedItem.owner_name} • Khatian {selectedItem.khatian_no}</p>
              </div>

              {/* Explanations summary */}
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">AI Flags & Explanations</span>
                {selectedItem.top_explanations.map((exp, idx) => (
                  <p key={idx} className="text-xs text-slate-300 leading-relaxed">• {exp}</p>
                ))}
              </div>

              {selectedRole === 'Citizen' ? (
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400">
                  <span className="font-bold text-amber-300">Citizen View Notice:</span> Administrative override and approval signing actions are restricted to Revenue Officers and Tahsildars.
                </div>
              ) : (
                <>
                  {/* Action Selection */}
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1.5">Select Officer Action:</label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => setDecisionAction('APPROVE')}
                        className={`py-2 px-3 rounded-xl text-xs font-bold border transition ${
                          decisionAction === 'APPROVE'
                            ? 'bg-emerald-500 text-slate-950 border-emerald-500'
                            : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800'
                        }`}
                      >
                        Approve Record
                      </button>
                      <button
                        onClick={() => setDecisionAction('OVERRIDE')}
                        className={`py-2 px-3 rounded-xl text-xs font-bold border transition ${
                          decisionAction === 'OVERRIDE'
                            ? 'bg-amber-500 text-slate-950 border-amber-500'
                            : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800'
                        }`}
                      >
                        Override AI Flag
                      </button>
                    </div>
                  </div>

                  {/* Mandatory Typed Reason Input */}
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1">
                      Mandatory Typed Reason <span className="text-rose-400">*</span>:
                    </label>
                    <textarea
                      value={typedReason}
                      onChange={(e) => setTypedReason(e.target.value)}
                      placeholder="Enter administrative justification (e.g. Physical field survey completed; boundary stones in Shamshabad match Dharani passbook extent)..."
                      rows={4}
                      className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:border-amber-500 focus:outline-none"
                    />
                  </div>

                  <button
                    onClick={handleSubmitDecision}
                    disabled={submitting}
                    className="w-full py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition flex items-center justify-center gap-2"
                  >
                    <Lock className="w-4 h-4 text-slate-950" />
                    <span>{submitting ? 'Signing & Hashing...' : 'Sign & Record Approval Hash'}</span>
                  </button>
                </>
              )}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
              <ShieldCheck className="w-10 h-10 text-slate-600 mb-3" />
              <h4 className="text-sm font-bold text-slate-200">No Parcel Selected for Officer Review</h4>
              <p className="text-xs text-slate-400 mt-1">Select a parcel from the queue table on the left to submit an administrative decision with a logged reason.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
