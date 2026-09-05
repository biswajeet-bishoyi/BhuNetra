/**
 * ConsentDialog — First-access DPDP Act 2023 consent modal.
 *
 * Blocked behind a one-time acceptance stored in localStorage. Officers must
 * acknowledge what data is being accessed, by whom, and for what purpose before
 * the rest of the app loads. Citizens can decline to prevent any data
 * access from proceeding.
 */
import React, { useState } from 'react';
import { Shield, Lock, FileText, X, CheckCircle2, XCircle, Users, MapPin } from 'lucide-react';

const CONSENT_KEY = 'bhunetra_dpdp_consent';

export function hasAcceptedConsent() {
  try {
    return localStorage.getItem(CONSENT_KEY) === 'accepted';
  } catch {
    return false;
  }
}

export function recordDecline() {
  try {
    localStorage.setItem(CONSENT_KEY, 'declined');
  } catch {}
}

export function clearConsent() {
  try {
    localStorage.removeItem(CONSENT_KEY);
  } catch {}
}

export default function ConsentDialog({ isOpen, onAccept, onDecline }) {
  const [acknowledged, setAcknowledged] = useState(false);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-md">
      <div className="bg-slate-900 border border-amber-500/30 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center">
              <Shield className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h2 className="text-base font-extrabold text-amber-300">BhuNetra AI — Data Access Consent</h2>
              <p className="text-[10px] text-slate-400">Digital Personal Data Protection Act 2023 · Section 6</p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
          <p>
            This application is a <span className="text-amber-300 font-bold">verification and decision-support
            layer</span> for land records digitized under DILRMP. Before continuing, please review what data is
            accessed, by whom, and for what purpose.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 pt-2">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <div className="flex items-center gap-2 text-amber-300 font-bold text-[11px] uppercase">
                <FileText className="w-3.5 h-3.5" />
                <span>Data Accessed</span>
              </div>
              <p className="text-slate-300 text-[11px]">
                Pattadar name, Aadhaar (if present), contact details, land record scans, satellite imagery,
                and ownership transfer history.
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <div className="flex items-center gap-2 text-amber-300 font-bold text-[11px] uppercase">
                <Users className="w-3.5 h-3.5" />
                <span>By Whom</span>
              </div>
              <p className="text-slate-300 text-[11px]">
                BhuNetra AI processing, the District Collector (read-only analytics), and Tahsildar / Revenue
                Officers (audited read &amp; write).
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <div className="flex items-center gap-2 text-amber-300 font-bold text-[11px] uppercase">
                <MapPin className="w-3.5 h-3.5" />
                <span>For What Purpose</span>
              </div>
              <p className="text-slate-300 text-[11px]">
                Algorithmic verification of land records, anomaly detection, and the IT Act 2000 Section 65B
                digital audit trail.
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <div className="flex items-center gap-2 text-amber-300 font-bold text-[11px] uppercase">
                <Lock className="w-3.5 h-3.5" />
                <span>How Long</span>
              </div>
              <p className="text-slate-300 text-[11px]">
                Audit-log entries are retained indefinitely for legal admissibility. Citizen view applies data
                minimization (PII masked) by default.
              </p>
            </div>
          </div>

          {/* Compliance grid */}
          <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 space-y-1 text-[10px] text-amber-200/80">
            <p><span className="font-bold text-amber-300">DPDP Act 2023:</span> Consent-based data minimization &amp; purpose limitation.</p>
            <p><span className="font-bold text-amber-300">IT Act 2000 Sec 65B:</span> Every officer action generates a SHA-256 timestamped hash for court admissibility.</p>
            <p><span className="font-bold text-amber-300">Registration Act 1908:</span> This app does not replace the registered sale deed.</p>
          </div>

          {/* Acknowledge checkbox */}
          <label className="flex items-start gap-2 cursor-pointer pt-2">
            <input
              type="checkbox"
              checked={acknowledged}
              onChange={(e) => setAcknowledged(e.target.checked)}
              className="mt-0.5 accent-amber-500"
            />
            <span className="text-[11px] text-slate-300 leading-relaxed">
              I have read the data access notice above and consent to BhuNetra AI processing the listed data
              for the stated purposes, in accordance with the DPDP Act 2023 and the IT Act 2000.
            </span>
          </label>
        </div>

        {/* Action buttons */}
        <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
          <button
            onClick={onDecline}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-rose-500/20 hover:text-rose-300 text-slate-300 text-xs font-bold border border-slate-700 transition"
          >
            <XCircle className="w-3.5 h-3.5" />
            <span>Decline</span>
          </button>
          <button
            onClick={onAccept}
            disabled={!acknowledged}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-slate-950 text-xs font-bold transition shadow-lg shadow-amber-500/20"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Accept &amp; Continue</span>
          </button>
        </div>
      </div>
    </div>
  );
}
