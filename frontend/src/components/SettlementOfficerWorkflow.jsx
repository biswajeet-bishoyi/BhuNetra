import React, { useState, useEffect } from 'react';
import { Scale, Clock, CheckCircle2, ChevronRight, AlertCircle, FileText, User, MapPin, Send, RefreshCw } from 'lucide-react';

export default function SettlementOfficerWorkflow() {
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [loading, setLoading] = useState(true);
  const [progressing, setProgressing] = useState(false);
  const [noticeNotes, setNoticeNotes] = useState('');

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/survey/settlement-cases');
      if (res.ok) {
        const json = await res.json();
        setCases(json.data || []);
        if (json.data && json.data.length > 0 && !selectedCase) {
          setSelectedCase(json.data[0]);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleProgressCase = async () => {
    if (!selectedCase) return;
    setProgressing(true);
    try {
      const res = await fetch(`/api/survey/settlement-cases/${selectedCase.case_id}/progress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: noticeNotes || 'Settlement officer reviewed evidence and approved progression.' })
      });
      if (res.ok) {
        const json = await res.json();
        setSelectedCase(json.data);
        setNoticeNotes('');
        fetchCases();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setProgressing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
              Revenue Court · Settlement Module
            </span>
            <h2 className="text-xl font-extrabold text-slate-100">Settlement Officer Dispute Resolution Workflow</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Statutory boundary dispute settlement & sub-division rectification under the Survey and Settlement Acts.
            Tracks cases through strict 6-phase procedural SLAs with neighbor notices and demarcation audits.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cases List */}
        <div className="glass-panel rounded-2xl p-4 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
              Active Settlement Cases ({cases.length})
            </h3>
            <button onClick={fetchCases} className="p-1 rounded text-slate-400 hover:text-white transition">
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="space-y-2.5">
            {cases.map((c) => (
              <div
                key={c.case_id}
                onClick={() => setSelectedCase(c)}
                className={`p-3 rounded-xl border transition cursor-pointer flex flex-col gap-1.5 ${
                  selectedCase?.case_id === c.case_id
                    ? 'bg-amber-500/10 border-amber-500/40 shadow-sm'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-amber-300">{c.case_id}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300">
                    {c.current_phase.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="text-xs text-slate-200 font-semibold truncate">
                  {c.petitioner} <span className="text-slate-500 font-normal">vs</span> {c.respondent}
                </div>
                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                  <span>{c.village}, {c.district}</span>
                  <span className="text-cyan-400 font-bold">Parcel {c.parcel_id}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Case Detail & Phase Stepper */}
        {selectedCase && (
          <div className="lg:col-span-2 glass-panel rounded-2xl p-5 border border-slate-800 space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-slate-100">{selectedCase.case_id}</span>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                    {selectedCase.dispute_type.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                  <MapPin className="w-3.5 h-3.5 text-slate-500" />
                  <span>{selectedCase.village}, {selectedCase.district}, {selectedCase.state} · Disputed Area: <strong>{selectedCase.disputed_area_sqm} sq.m</strong></span>
                </div>
              </div>

              <div className="text-right">
                <div className="text-[11px] text-slate-400 font-mono">SLA Timeline</div>
                <div className="text-sm font-bold text-amber-400 font-mono">
                  {selectedCase.days_elapsed} / {selectedCase.sla_days_total} Days Elapsed
                </div>
              </div>
            </div>

            {/* 6-Phase Stepper */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono mb-4">
                Statutory Phase Progression Workflow
              </h4>
              <div className="space-y-3">
                {selectedCase.phases.map((phase, idx) => (
                  <div
                    key={phase.phase}
                    className={`p-3.5 rounded-xl border flex items-start gap-3.5 transition ${
                      phase.status === 'COMPLETED'
                        ? 'bg-emerald-500/[0.04] border-emerald-500/30'
                        : phase.status === 'IN_PROGRESS'
                        ? 'bg-amber-500/[0.08] border-amber-500/50 shadow-sm'
                        : 'bg-slate-900/40 border-slate-800 opacity-60'
                    }`}
                  >
                    <div className="mt-0.5">
                      {phase.status === 'COMPLETED' ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      ) : phase.status === 'IN_PROGRESS' ? (
                        <Clock className="w-5 h-5 text-amber-400 animate-pulse" />
                      ) : (
                        <div className="w-5 h-5 rounded-full border border-slate-600 flex items-center justify-center text-[10px] font-mono text-slate-500">
                          {idx + 1}
                        </div>
                      )}
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-200">
                          {idx + 1}. {phase.phase.replace(/_/g, ' ')}
                        </span>
                        {phase.date && (
                          <span className="text-[10px] font-mono text-slate-400">{phase.date}</span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1">{phase.notes}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Officer Action Bar */}
            {selectedCase.phase_index < selectedCase.phases.length - 1 && (
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <h5 className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                  <Scale className="w-4 h-4 text-amber-400" />
                  <span>Settlement Officer Action & Progression</span>
                </h5>
                <input
                  type="text"
                  value={noticeNotes}
                  onChange={(e) => setNoticeNotes(e.target.value)}
                  placeholder="Enter hearing minutes, field Amin inspection note, or survey order..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition"
                />
                <button
                  onClick={handleProgressCase}
                  disabled={progressing}
                  className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer disabled:opacity-50"
                >
                  {progressing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                  <span>Advance to Next Phase: {selectedCase.phases[selectedCase.phase_index + 1]?.phase.replace(/_/g, ' ')}</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
