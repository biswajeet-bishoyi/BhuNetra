import React, { useState, useEffect, useCallback } from 'react';
import {
  Upload, FileText, CheckCircle2, AlertTriangle, Cpu, RefreshCw,
  ShieldAlert, PencilLine, XCircle, Info, Hash, ArrowRight
} from 'lucide-react';
import DocumentReviewPanel from './DocumentReviewPanel';

/**
 * Engine 1 — Document Digitization Workbench.
 *
 * Talks to POST /api/ocr/extract, which runs an on-device vision-language model
 * over the actual uploaded image bytes. Every field arrives with its own
 * confidence and the deterministic checks behind it, so low-confidence fields
 * can be surfaced amber and routed to a Revenue Officer instead of being
 * presented as settled fact.
 */

const FIELD_ORDER = [
  ['deed_registration_no', 'Deed Registration No.'],
  ['survey_no', 'Survey / Sub-division No.'],
  ['khatian_no', 'Khatian / Passbook No.'],
  ['ulpin', 'ULPIN'],
  ['owner_name', 'Pattadar (Recorded Owner)'],
  ['father_or_husband', 'Father / Husband Name'],
  ['village', 'Village'],
  ['mandal', 'Mandal'],
  ['district', 'District'],
  ['claimed_area_sqm', 'Recorded Extent (sq.m)'],
  ['land_use_claim', 'Land Classification'],
];

const CHECK_LABELS = {
  format_valid: 'Format matches the Dharani field pattern',
  format_invalid: 'Does not match the expected Dharani field pattern',
  matches_master_data: 'Matches government master data',
  normalized_to_master_data: 'Auto-corrected to the nearest master-data entry',
  not_in_master_data: 'Not present in government master data',
  numeric_range_ok: 'Numeric value within a plausible range',
  not_a_number: 'Could not be read as a number',
  area_outside_plausible_range: 'Area outside the plausible range',
  converted_from_acres: 'Converted from acres to square metres',
  field_missing_or_illegible: 'Absent or illegible on the page',
  cross_pass_agreement: 'Two independent reads agreed',
  cross_pass_disagreement: 'Two independent reads disagreed',
};

const SAMPLE_SCANS = [
  { id: 'P-101', label: 'P-101', hint: 'Clean printed deed', file: 'scan_P-101.png' },
  { id: 'P-105', label: 'P-105', hint: 'Printed · boundary overlap parcel', file: 'scan_P-105.png' },
  { id: 'P-112', label: 'P-112', hint: 'Printed · extent deviates from GIS', file: 'scan_P-112.png' },
  { id: 'P-117', label: 'P-117', hint: 'Printed · deed name differs from registry', file: 'scan_P-117.png' },
  { id: 'P-106', label: 'P-106', hint: 'HANDWRITTEN · expect officer review', file: 'scan_P-106.png' },
];

function confidenceTone(conf, needsReview) {
  if (needsReview) return conf > 0 ? 'amber' : 'rose';
  if (conf >= 0.9) return 'emerald';
  return 'sky';
}

const TONE_CLASSES = {
  emerald: 'border-emerald-500/30 bg-emerald-500/[0.06]',
  sky: 'border-sky-500/30 bg-sky-500/[0.06]',
  amber: 'border-amber-500/40 bg-amber-500/[0.08]',
  rose: 'border-rose-500/40 bg-rose-500/[0.08]',
};
const TONE_TEXT = {
  emerald: 'text-emerald-400',
  sky: 'text-sky-300',
  amber: 'text-amber-300',
  rose: 'text-rose-300',
};

export default function OCRScanner({ onSelectParcel }) {
  // ---- Document lifecycle state machine ----
  // step: 'upload' | 'extracting' | 'review' | 'approved' | null
  const [step, setStep] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [error, setError] = useState(null);
  const [engine, setEngine] = useState(null);
  const [edits, setEdits] = useState({});
  const [lifecycleDocId, setLifecycleDocId] = useState(null);
  const [lifecycleStatus, setLifecycleStatus] = useState(null);
  const [lifecycleHash, setLifecycleHash] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    // Fire-and-forget; never block UI render on the engine status ping.
    // The real source of truth is the engine_tag returned by /api/ocr/extract
    // — engine-status is only a UI badge to set initial expectations.
    let cancelled = false;
    fetch('/api/ocr/engine-status')
      .then((r) => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
      .then((body) => { if (!cancelled && body?.data) setEngine(body.data); })
      .catch(() => {
        if (!cancelled) setEngine({ reachable: false, model_available: false, engine_tag: 'UNAVAILABLE' });
      });
    return () => { cancelled = true; };
  }, []);

  const runExtraction = useCallback(async (blob, filename) => {
    setStep('extracting');
    setError(null);
    setResult(null);
    setEdits({});
    setLifecycleDocId(null);
    setLifecycleHash(null);

    try {
      // 1. Upload the document and get document_id
      const uploadForm = new FormData();
      uploadForm.append('file', blob, filename);
      const uploadRes = await fetch('/api/documents/upload', { method: 'POST', body: uploadForm });
      if (!uploadRes.ok) {
        const err = await uploadRes.json();
        setError({ status: uploadRes.status, message: err.detail || 'Upload failed.' });
        setStep(null);
        return;
      }
      const uploadData = await uploadRes.json();
      setLifecycleDocId(uploadData.document_id);

      // 2. Run extraction via the document lifecycle endpoint
      const extractRes = await fetch(`/api/documents/${uploadData.document_id}/extract?passes=auto`, { method: 'POST' });
      if (!extractRes.ok) {
        const err = await extractRes.json();
        setError({ status: extractRes.status, message: err.detail || 'Extraction failed.' });
        setStep(null);
        return;
      }
      const extractData = await extractRes.json();

      // Build a result-like shape from the extraction response
      // so the rest of the UI can render it without major changes
      const r = {
        status: extractData.status,
        document_confidence: extractData.extraction_confidence,
        confidence_threshold: 0.8,
        passes: extractData.passes,
        timing_ms: extractData.timing_ms,
        low_confidence_fields: extractData.low_confidence_fields,
        engine_tag: extractData.engine_tag,
        // We need the full extraction result; fetch it from the document endpoint
      };
      setResult(r);

      // Fetch full extraction details for the field view
      const docRes = await fetch(`/api/documents/${uploadData.document_id}`);
      if (docRes.ok) {
        const docDetail = await docRes.json();
        setResult({
          ...r,
          fields: docDetail.extracted_fields,
          raw_text: docDetail.extraction_result?.raw_text,
          disclaimer: 'Extraction via document lifecycle API. Fields corrected by officer are reflected in the review record.',
        });
      }

      // Transition to review step if there are low-confidence fields
      if (extractData.status === 'NEEDS_REVIEW' || (extractData.low_confidence_fields && extractData.low_confidence_fields.length > 0)) {
        setStep('review');
      } else {
        setStep('extracting'); // still processing
      }
    } catch (err) {
      setError({ status: 0, message: `Could not reach the digitization service. ${err.message}` });
      setStep(null);
    }
  }, []);

  const handleSampleClick = async (sample) => {
    setPreviewUrl(`/static-data/synthetic/registry_scans/${sample.file}`);
    try {
      const res = await fetch(`/static-data/synthetic/registry_scans/${sample.file}`);
      const blob = await res.blob();
      await runExtraction(blob, sample.file);
    } catch (err) {
      setError({ status: 0, message: `Could not load the sample scan. ${err.message}` });
    }
  };

  const handleFileUpload = async (e) => {
    const uploaded = e.target.files[0];
    if (!uploaded) return;
    setPreviewUrl(URL.createObjectURL(uploaded));
    await runExtraction(uploaded, uploaded.name);
  };

  const engineOnline = engine?.model_available;
  const reviewCount = result?.low_confidence_fields?.length ?? 0;
  const isExtracting = step === 'extracting';

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
              engineOnline
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
            }`}>
              Engine 1 • {engineOnline ? 'REAL · On-device vision model' : 'Engine offline'}
            </span>
            <h2 className="text-xl font-extrabold text-slate-100">Record Digitization Workbench</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Scanned or hand-filled Dharani Record-of-Rights pages are read on-device by a
            vision-language model — no page leaves this machine. Every field carries its own
            confidence; anything the model is unsure of is flagged for Revenue Officer verification
            rather than accepted silently.
          </p>
          {engine && (
            <p className="text-[10px] text-slate-500 mt-1.5 font-mono">
              {engine.model} @ {engine.host}
              {!engineOnline && engine.hint ? ` — ${engine.hint}` : ''}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <span className="text-xs text-slate-400 font-medium">Sample registry scans:</span>
          <div className="flex flex-wrap items-center gap-2">
            {SAMPLE_SCANS.map((sample) => (
              <button
                key={sample.id}
                onClick={() => handleSampleClick(sample)}
                disabled={isExtracting}
                title={sample.hint}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40
                           text-xs font-semibold text-amber-300 border border-slate-700 transition"
              >
                {sample.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Document Uploader & Preview */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col">
          <h3 className="text-sm font-bold text-slate-200 mb-3 flex items-center gap-2">
            <FileText className="w-4 h-4 text-amber-400" />
            <span>Document Intake & Scan Viewer</span>
          </h3>

          {!previewUrl ? (
            <label className="flex-1 min-h-[360px] border-2 border-dashed border-slate-700 hover:border-amber-500/50 rounded-xl flex flex-col items-center justify-center p-6 cursor-pointer bg-slate-900/40 hover:bg-slate-900/80 transition group">
              <Upload className="w-10 h-10 text-slate-500 group-hover:text-amber-400 transition mb-3" />
              <p className="text-sm font-bold text-slate-300">Drop a scanned deed image here or click to browse</p>
              <p className="text-xs text-slate-500 mt-1">PNG, JPG, TIFF, WEBP · printed or handwritten RoR pages</p>
              <p className="text-[10px] text-slate-600 mt-2">
                Any land-record page works — the model reads the image, not the filename.
              </p>
              <input type="file" onChange={handleFileUpload} accept="image/*" className="hidden" />
            </label>
          ) : (
            <div className="relative flex-1 min-h-[360px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center p-3">
              <img src={previewUrl} alt="Deed scan preview" className="max-h-[420px] object-contain rounded-lg shadow-xl" />
              <button
                onClick={() => { setPreviewUrl(null); setResult(null); setError(null); setEdits({}); setStep(null); setLifecycleHash(null); setLifecycleDocId(null); }}
                className="absolute top-4 right-4 px-3 py-1.5 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-xs font-bold text-slate-300 border border-slate-700"
              >
                Clear / Upload Another
              </button>
            </div>
          )}
        </div>

        {/* Extracted Fields */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col justify-between">
          <div className="min-w-0">
            <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-amber-400" />
              <span>Extracted Fields & Per-Field Confidence</span>
            </h3>

            {isExtracting ? (
              <div className="py-16 text-center text-slate-400 space-y-3">
                <RefreshCw className="w-8 h-8 text-amber-400 animate-spin mx-auto" />
                <p className="text-xs font-semibold">
                  Reading the page with the on-device vision model…
                </p>
                <p className="text-[10px] text-slate-500">
                  Uploading scan, running extraction, checking field confidence…
                </p>
              </div>
            ) : error ? (
              <div className="py-10 px-4 text-center space-y-3">
                <XCircle className="w-8 h-8 text-rose-400 mx-auto" />
                <p className="text-sm font-bold text-rose-300">
                  {error.status === 503 ? 'Digitization engine unavailable' : 'Extraction failed'}
                </p>
                <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">{error.message}</p>
                <p className="text-[10px] text-slate-500 max-w-md mx-auto">
                  No values are shown because none were read. The system never substitutes
                  placeholder or looked-up data for a failed extraction.
                </p>
              </div>
            ) : result ? (
              <div className="space-y-4">
                {/* Document-level summary */}
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">Doc confidence</span>
                    <p className={`font-extrabold text-base mt-0.5 ${
                      result.document_confidence >= result.confidence_threshold ? 'text-emerald-400' : 'text-amber-300'
                    }`}>
                      {(result.document_confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">Status</span>
                    <p className={`font-extrabold text-[13px] mt-1 ${
                      result.status === 'NEEDS_REVIEW' ? 'text-amber-300' : 'text-emerald-400'
                    }`}>
                      {result.status === 'NEEDS_REVIEW' ? 'NEEDS REVIEW' : 'EXTRACTED'}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">Reads / time</span>
                    <p className="font-bold text-slate-200 text-[13px] mt-1">
                      {result.passes}× · {(result.timing_ms / 1000).toFixed(1)}s
                    </p>
                  </div>
                </div>

                {reviewCount > 0 && (
                  <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 flex gap-2">
                    <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <p className="text-[11px] text-amber-200 leading-relaxed">
                      <strong>{reviewCount} field{reviewCount > 1 ? 's' : ''}</strong> fell below the{' '}
                      {(result.confidence_threshold * 100).toFixed(0)}% confidence threshold and require
                      Revenue Officer verification before this record can be committed.
                    </p>
                  </div>
                )}

                {/* Per-field cards */}
                <div className="space-y-1.5 max-h-[340px] overflow-y-auto pr-1">
                  {FIELD_ORDER.map(([key, label]) => {
                    const f = result.fields?.[key];
                    if (!f) return null;
                    const tone = confidenceTone(f.confidence, f.needs_review);
                    const failed = f.checks?.failed ?? [];
                    const passed = f.checks?.passed ?? [];
                    const shown = edits[key] !== undefined ? edits[key] : (f.value ?? '');
                    return (
                      <div key={key} className={`p-2.5 rounded-lg border ${TONE_CLASSES[tone]}`}>
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-[10px] uppercase font-semibold text-slate-400">{label}</span>
                          <span className={`text-[10px] font-bold ${TONE_TEXT[tone]} flex items-center gap-1`}>
                            {f.needs_review
                              ? <AlertTriangle className="w-3 h-3" />
                              : <CheckCircle2 className="w-3 h-3" />}
                            {(f.confidence * 100).toFixed(0)}%
                          </span>
                        </div>

                        {f.needs_review ? (
                          <div className="mt-1 flex items-center gap-1.5">
                            <PencilLine className="w-3 h-3 text-amber-400 shrink-0" />
                            <input
                              value={shown}
                              onChange={(e) => setEdits({ ...edits, [key]: e.target.value })}
                              placeholder="Enter the correct value from the page"
                              className="w-full bg-slate-950/80 border border-amber-500/30 rounded px-2 py-1
                                         text-xs font-bold text-slate-100 placeholder:text-slate-600
                                         focus:outline-none focus:border-amber-400"
                            />
                          </div>
                        ) : (
                          <p className="font-bold text-slate-100 text-sm mt-0.5 break-words">
                            {shown === '' ? <span className="text-slate-500 italic">not read</span> : String(shown)}
                          </p>
                        )}

                        {(failed.length > 0 || f.alternate_reading !== undefined) && (
                          <div className="mt-1.5 space-y-0.5">
                            {failed.map((c) => (
                              <p key={c} className="text-[10px] text-amber-300/90 flex items-start gap-1">
                                <Info className="w-2.5 h-2.5 mt-[3px] shrink-0" />
                                {CHECK_LABELS[c] || c}
                              </p>
                            ))}
                            {f.alternate_reading !== undefined && (
                              <p className="text-[10px] text-slate-400">
                                Second read produced:{' '}
                                <span className="font-mono text-slate-300">
                                  {String(f.alternate_reading || '—')}
                                </span>
                              </p>
                            )}
                          </div>
                        )}
                        {failed.length === 0 && passed.length > 0 && (
                          <p className="text-[10px] text-slate-500 mt-1">
                            {passed.map((c) => CHECK_LABELS[c] || c).join(' · ')}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Raw text the model transcribed */}
                {result.raw_text && (
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      Text read off the page
                    </span>
                    <pre className="text-[11px] font-mono text-slate-300 mt-1.5 whitespace-pre-wrap leading-relaxed max-h-32 overflow-y-auto">
                      {result.raw_text}
                    </pre>
                  </div>
                )}

                <p className="text-[10px] text-slate-500 leading-relaxed">{result.disclaimer}</p>
              </div>
            ) : step === 'review' && result ? (
              <div className="space-y-3">
                {/* Lifecycle state strip */}
                <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center gap-2 text-[10px] text-slate-400">
                  <Hash className="w-3 h-3 text-amber-400" />
                  <span>Document #{lifecycleDocId}</span>
                  <ArrowRight className="w-3 h-3 text-slate-500" />
                  <span className="font-bold text-amber-300">{result.status}</span>
                  <span className="ml-auto">Step: officer review</span>
                </div>
                <DocumentReviewPanel
                  docId={lifecycleDocId}
                  extractionResult={{ ...result, low_confidence_fields: result.low_confidence_fields || [] }}
                  onCancel={() => setStep(null)}
                  onSubmit={(resp) => {
                    setLifecycleStatus(resp.status || 'VERIFIED');
                    if (resp.blockchain_hash) {
                      setLifecycleHash(resp.blockchain_hash);
                      setStep('approved');
                    } else if (resp.status === 'REJECTED') {
                      setStep('rejected');
                    } else {
                      setStep('verified');
                    }
                  }}
                />
              </div>
            ) : step === 'approved' && lifecycleHash ? (
              <div className="space-y-4">
                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-center space-y-2">
                  <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
                  <h3 className="text-base font-extrabold text-emerald-300">Document Approved</h3>
                  <p className="text-xs text-emerald-200/80">SHA-256 hash generated under IT Act 2000 Sec 65B</p>
                  <p className="font-mono text-[10px] break-all bg-slate-950/80 p-2 rounded text-amber-300 border border-amber-500/20">
                    {lifecycleHash}
                  </p>
                  <p className="text-[10px] text-slate-400">Document #{lifecycleDocId} · {lifecycleStatus || 'APPROVED'}</p>
                </div>
                <button
                  onClick={() => { setStep(null); setResult(null); setPreviewUrl(null); setLifecycleHash(null); setLifecycleDocId(null); }}
                  className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition"
                >
                  Start a New Document
                </button>
              </div>
            ) : step === 'verified' ? (
              <div className="space-y-3">
                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-center space-y-2">
                  <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
                  <h3 className="text-base font-extrabold text-emerald-300">Document Verified</h3>
                  <p className="text-xs text-slate-300">The document has been reviewed and is now in VERIFIED state.</p>
                  <p className="text-[10px] text-slate-500">Approval generates the Sec 65B cryptographic hash.</p>
                </div>
                <button
                  onClick={async () => {
                    const res = await fetch(`/api/documents/${lifecycleDocId}/approve`, { method: 'POST' });
                    if (res.ok) {
                      const j = await res.json();
                      setLifecycleHash(j.blockchain_hash);
                      setLifecycleStatus('APPROVED');
                      setStep('approved');
                    }
                  }}
                  className="w-full py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow-lg shadow-amber-500/20"
                >
                  Approve & Generate SHA-256 Hash
                </button>
              </div>
            ) : step === 'rejected' ? (
              <div className="space-y-3">
                <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-center space-y-2">
                  <XCircle className="w-10 h-10 text-rose-400 mx-auto" />
                  <h3 className="text-base font-extrabold text-rose-300">Document Rejected</h3>
                  <p className="text-xs text-slate-300">The document is in terminal REJECTED state. Upload a new scan to restart.</p>
                </div>
                <button
                  onClick={() => { setStep(null); setResult(null); setPreviewUrl(null); }}
                  className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition"
                >
                  Start Over
                </button>
              </div>
            ) : (
              <div className="py-16 text-center text-slate-500 text-xs px-6">
                Upload a scanned land record — or pick a sample above — to digitize it live.
                {engine && !engineOnline && (
                  <p className="mt-3 text-rose-300/80 text-[11px]">
                    The on-device model is not currently loaded. {engine.hint}
                  </p>
                )}
              </div>
            )}
          </div>

          {result?.parcel_id_hint && (
            <div className="pt-4 border-t border-slate-800 space-y-1.5">
              <button
                onClick={() => onSelectParcel(result.parcel_id_hint)}
                className="w-full py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow-lg shadow-amber-500/20"
              >
                Cross-Verify Parcel {result.parcel_id_hint} against the digital registry
              </button>
              <p className="text-[10px] text-slate-500 text-center">
                Parcel reference {result.parcel_id_hint} was {result.parcel_id_hint_source}.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
