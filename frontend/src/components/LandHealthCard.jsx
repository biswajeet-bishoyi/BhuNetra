import React, { useState, useEffect, useRef } from 'react';
import { Shield, CheckCircle, AlertTriangle, ShieldAlert, Printer, X, FileCheck, Lock, QrCode, Download, FileText } from 'lucide-react';

export default function LandHealthCard({ parcelId, selectedRole, isOpen, onClose }) {
  const [certData, setCertData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const printRef = useRef();

  useEffect(() => {
    if (isOpen && parcelId) {
      fetchCertificate();
    }
  }, [isOpen, parcelId, selectedRole]);

  const fetchCertificate = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/certificate/${parcelId}?role=${encodeURIComponent(selectedRole || 'Revenue Officer')}`);
      if (res.ok) {
        const json = await res.json();
        setCertData(json);
      }
    } catch (err) {
      console.error("Failed to load certificate", err);
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPdf = async () => {
    setDownloadingPdf(true);
    try {
      const res = await fetch(`/api/certificate/${parcelId}/export-pdf?role=${encodeURIComponent(selectedRole || 'Revenue Officer')}`);
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `BhuNetra-Certificate-${parcelId}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else {
        const err = await res.json();
        alert(`PDF download failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (err) {
      alert(`PDF download error: ${err.message}`);
    } finally {
      setDownloadingPdf(false);
    }
  };

  if (!isOpen) return null;

  const payload = certData?.payload;
  const isHighRisk = payload?.ensemble_risk_level === 'RED';
  const isMediumRisk = payload?.ensemble_risk_level === 'YELLOW';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-3xl glass-panel rounded-2xl border border-slate-700/80 shadow-2xl p-6 md:p-8 bg-slate-900/95 text-slate-100 my-8">
        
        {/* Modal Close & Actions */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-amber-400" />
            <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
              BhuNetra AI • Digital Title Health Card
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-slate-100 text-xs font-bold transition shadow-lg"
              title="Download as PDF"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>{downloadingPdf ? 'Generating…' : 'PDF'}</span>
            </button>
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow-lg shadow-amber-500/20"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {loading || !certData ? (
          <div className="py-20 text-center text-slate-400 text-sm">
            Generating tamper-evident cryptographic certificate...
          </div>
        ) : (
          <div ref={printRef} className="space-y-6 pt-4 text-slate-200">
            
            {/* Certificate Header Emblem */}
            <div className="text-center space-y-1 border-b border-slate-800 pb-4">
              <div className="text-[10px] uppercase font-bold tracking-widest text-slate-400">
                Government of Telangana • Revenue Department
              </div>
              <h2 className="text-xl md:text-2xl font-black text-amber-300 tracking-tight">
                LAND HEALTH & TITLE ADMISSIBILITY CERTIFICATE
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Certificate ID: <span className="text-slate-300 font-bold">{certData.certificate_id}</span> • ULPIN: <span className="text-amber-400 font-bold">{payload.ulpin}</span>
              </p>
            </div>

            {/* Core Identification Card */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-bold">Parcel / Survey No</span>
                <p className="font-extrabold text-amber-300 text-sm mt-0.5">{payload.parcel_id} / Sy. {payload.survey_no}</p>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-bold">Recorded Pattadar</span>
                <p className="font-bold text-slate-200 text-sm mt-0.5">{payload.owner_name}</p>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-bold">Village & Mandal</span>
                <p className="font-bold text-slate-200 text-sm mt-0.5">{payload.village}, {payload.mandal}</p>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-bold">Court Litigation</span>
                <p className="font-bold text-amber-400 text-sm mt-0.5">{payload.revenue_court_status}</p>
              </div>
            </div>

            {/* AI Risk & Multi-Engine Verification Status */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Overall Score Badge */}
              <div className={`p-4 rounded-xl border text-center flex flex-col justify-center items-center ${
                isHighRisk
                  ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                  : isMediumRisk
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                  : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              }`}>
                <div className="text-[10px] uppercase font-bold tracking-wider">Multi-Modal Risk Status</div>
                <div className="text-3xl font-black my-1">{payload.ensemble_risk_level}</div>
                <div className="text-xs font-semibold">Ensemble Risk Score: {payload.ensemble_risk_score} / 100</div>
              </div>

              {/* Sub-Engine Matrix */}
              <div className="md:col-span-2 p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 text-xs">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">4-Engine Verification Matrix</span>
                <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                  <div className="p-2 rounded bg-slate-900 border border-slate-800 flex justify-between">
                    <span className="text-slate-400">GIS Topology (E2):</span>
                    <span className="font-bold text-slate-200">{payload.engine_scores?.gis_validation || 0}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800 flex justify-between">
                    <span className="text-slate-400">Title Velocity (E3):</span>
                    <span className="font-bold text-slate-200">{payload.engine_scores?.ownership_intelligence || 0}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800 flex justify-between">
                    <span className="text-slate-400">Satellite Use (E4):</span>
                    <span className="font-bold text-slate-200">{payload.engine_scores?.satellite_verification || 0}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800 flex justify-between">
                    <span className="text-slate-400">Deed OCR Match (E1):</span>
                    <span className="font-bold text-slate-200">{payload.engine_scores?.registry_ocr || 0}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* SHAP Explanation Summary */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Algorithmic Assessment Summary</span>
              {payload.top_explanations?.map((exp, idx) => (
                <p key={idx} className="text-xs text-slate-300 leading-relaxed">• {exp}</p>
              ))}
            </div>

            {/* Legal Admissibility & Hash Box */}
            <div className="p-3.5 rounded-xl bg-gradient-to-br from-slate-950 to-slate-900 border border-amber-500/20 space-y-2">
              <div className="flex items-center justify-between text-[10px] font-bold text-amber-400 uppercase">
                <span className="flex items-center gap-1">
                  <FileCheck className="w-3.5 h-3.5 text-emerald-400" />
                  IT Act 2000 Section 65B Electronic Admissibility Hash
                </span>
                <span className="text-slate-400">Admissible Evidence</span>
              </div>
              <div className="font-mono text-[10px] break-all bg-slate-900/90 p-2 rounded border border-slate-800 text-amber-300">
                {certData.digital_admissibility_hash}
              </div>
              <div className="text-[10px] text-slate-400 leading-normal flex items-start gap-2">
                <Lock className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                <span>
                  {certData.legal_clauses?.it_act_2000_sec_65b} {certData.legal_clauses?.registration_act_1908}
                </span>
              </div>
            </div>

            {/* Footer Signatures */}
            <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800">
              <div>
                <span className="font-bold text-slate-300">Timestamp:</span> {certData.issued_timestamp}
              </div>
              <div className="text-right font-semibold text-slate-300">
                {certData.statutory_authority}
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}
