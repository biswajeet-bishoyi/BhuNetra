/**
 * DocumentReviewPanel — Officer field-correction step in the document lifecycle.
 *
 * Appears after extraction returns low-confidence fields. Officers can edit
 * those fields inline before the document is submitted for review and approval.
 */
import React, { useState } from 'react';
import { PencilLine, CheckCircle2, AlertTriangle, XCircle, ShieldAlert } from 'lucide-react';

const FIELD_LABELS = {
  deed_registration_no: 'Deed Registration No.',
  survey_no: 'Survey / Sub-division No.',
  khatian_no: 'Khatian / Passbook No.',
  ulpin: 'ULPIN',
  owner_name: 'Pattadar (Recorded Owner)',
  father_or_husband: 'Father / Husband Name',
  village: 'Village',
  mandal: 'Mandal',
  district: 'District',
  claimed_area_sqm: 'Recorded Extent (sq.m)',
  land_use_claim: 'Land Classification',
};

export default function DocumentReviewPanel({ docId, extractionResult, onSubmit, onCancel }) {
  const [corrections, setCorrections] = useState({});
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const lowFields = extractionResult?.low_confidence_fields ?? [];
  const fields = extractionResult?.fields ?? {};
  const allFieldKeys = Object.keys(FIELD_LABELS);

  const handleCorrection = (key, value) => {
    setCorrections(prev => ({ ...prev, [key]: value }));
  };

  const isValid = reason.trim().length >= 5;

  const handleSubmit = async (targetStatus) => {
    if (!isValid) return;
    setSubmitting(true);
    try {
      const correctionList = Object.entries(corrections)
        .filter(([, v]) => v !== fields[key]?.value && v !== undefined)
        .map(([key, value]) => ({ field_key: key, corrected_value: value }));

      const res = await fetch(`/api/documents/${docId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          officer_name: 'Tahsildar / Revenue Officer Shamshabad',
          reason: reason.trim(),
          corrections: correctionList,
          target_status: targetStatus,
        }),
      });

      if (res.ok) {
        const json = await res.json();
        onSubmit(json);
      } else {
        const err = await res.json();
        alert(`Review failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (err) {
      alert(`Network error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async () => {
    setSubmitting(true);
    try {
      const res = await fetch(`/api/documents/${docId}/approve`, { method: 'POST' });
      if (res.ok) {
        const json = await res.json();
        onSubmit(json);
      } else {
        const err = await res.json();
        alert(`Approval failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (err) {
      alert(`Network error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-400" />
        <h4 className="text-sm font-bold text-amber-300">Revenue Officer Field Verification</h4>
      </div>

      <p className="text-xs text-slate-400">
        The OCR extraction flagged {lowFields.length} field{lowFields.length !== 1 ? 's' : ''} as low-confidence.
        Please review and correct these fields before the document can be submitted.
      </p>

      {/* Field editors for low-confidence fields */}
      {lowFields.length > 0 && (
        <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
          {lowFields.map((key) => {
            const f = fields[key];
            const label = FIELD_LABELS[key] || key;
            return (
              <div key={key} className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/5 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-bold text-amber-300 tracking-wider">{label}</span>
                  <span className="text-[10px] font-bold text-amber-400 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    Low confidence ({(f?.confidence ?? 0) * 100.toFixed(0)}%)
                  </span>
                </div>
                <input
                  type="text"
                  value={corrections[key] !== undefined ? corrections[key] : (f?.value ?? '')}
                  onChange={(e) => handleCorrection(key, e.target.value)}
                  placeholder={`Enter correct value for ${label}`}
                  className="w-full bg-slate-950 border border-amber-500/30 rounded px-3 py-2 text-xs font-bold text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-amber-400"
                />
                {f?.checks?.failed?.length > 0 && (
                  <p className="text-[10px] text-amber-300/80">
                    Failed checks: {f.checks.failed.join(', ')}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Mandatory reason */}
      <div>
        <label className="block text-xs font-bold text-slate-300 mb-1.5">
          Mandatory Typed Reason <span className="text-rose-400">*</span>:
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Describe the verification action taken (e.g. Corrected survey number after cross-referencing Dharani passbook entry)"
          rows={3}
          className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:border-amber-500 focus:outline-none placeholder:text-slate-600"
        />
        <p className="text-[10px] text-slate-500 mt-1">Minimum 5 characters required for the Sec 65B audit trail.</p>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => handleSubmit('VERIFIED')}
          disabled={!isValid || submitting}
          className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 text-slate-950 text-xs font-bold transition"
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>{submitting ? 'Submitting…' : 'Verified & Submit for Approval'}</span>
        </button>

        <button
          onClick={() => handleSubmit('REJECTED')}
          disabled={submitting}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 text-xs font-bold border border-rose-500/30 transition"
        >
          <XCircle className="w-4 h-4" />
          <span>Reject</span>
        </button>

        <button
          onClick={onCancel}
          disabled={submitting}
          className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
